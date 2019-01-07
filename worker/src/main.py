import contextlib
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from profanity_check import predict
from selenium import webdriver
from slackclient import SlackClient
from urlextract import URLExtract

import tensorflow as tf

logger = logging.getLogger('safely')

logger.setLevel(logging.INFO)

DEBUG = True


class Moderator:
    NSFW_MODEL = Path('/var/opt/nsfw_classifier.pb')
    NSFW_THRESHOLD = 0.95
    REACT_TO_CLEAN = bool(os.getenv('SAFELY_REACT_TO_CLEAN', False))

    def __init__(self, text, channel, author, timestamp):
        self.token = os.environ.get('SAFELY_SLACKBOT_TOKEN')
        if not self.NSFW_MODEL.exists():
            raise RuntimeError('Model file is not present!')
        self.slack_client = SlackClient(self.token)
        self.text = text
        self.channel = channel
        self.author = author
        self.timestamp = timestamp
        self.link_extractor = URLExtract()
        self.images_directory = TemporaryDirectory()
        self.admins = os.getenv('SAFELY_ADMINS_LIST', '').split(',')
        self.urls = self.extract_links()
        self.is_nsfw = False

    def extract_links(self) -> list:
        return self.link_extractor.find_urls(str(self.text))

    @staticmethod
    def link_is_image(link) -> bool:
        resp = requests.head(link)
        _type = resp.headers.get('Content-Type', '')
        invalid_types = ['svg', 'base64']
        if any([i in _type for i in invalid_types]):
            return False
        return 'image' in _type

    @staticmethod
    def link_is_html(link) -> bool:
        resp = requests.head(link)
        return 'html' in resp.headers.get('Content-Type', '')

    def report_bad_message(self) -> None:
        """ Report Slack Message to Admins and Notify the poster """
        if DEBUG:
            logger.info('Message appears to be NSFW')
        self.slack_client.api_call(
            "chat.postMessage",
            channel=self.channel,
            text="This message appears to be NSFW cc/ {} ".format(' '.join(self.admins)),
            as_user=True
        )

    def report_safe_message(self) -> None:
        """ Add an Emoji Slack Reaction  """
        if DEBUG:
            logger.info('Message appears to be safe')
        if self.REACT_TO_CLEAN:
            self.slack_client.api_call(
                "reactions.add",
                channel=self.channel,
                name="white_check_mark",
                timestamp=self.timestamp,
            )

    @staticmethod
    def image_url_path(url: str) -> str:
        """ Get a file-system friendly path """
        path = urlparse(url).path
        return path[1:].replace('/', '-')

    def download_image(self, url: str) -> str:
        """ Download an image URL to a temp directory """
        image_path = self.image_url_path(url)
        destination_path = '{0}/{1}'.format(self.images_directory.name, image_path)
        with open(destination_path, 'wb') as handle:
            response = requests.get(url, stream=True)
            if response.ok:
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
        return destination_path

    def check_message(self, image_data) -> dict:
        """ Run Tensorflow Classifier using Open NSFW model """
        image_data = tf.gfile.GFile(image_data, 'rb').read()

        label_lines = ['sfw', 'nsfw']

        with tf.gfile.GFile(str(self.NSFW_MODEL.resolve()), 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            tf.import_graph_def(graph_def, name='')
        with tf.Session() as sess:
            # Feed the image_data as input to the graph and get first prediction
            softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

            predictions = sess.run(softmax_tensor,  {'DecodeJpeg/contents:0': image_data})

            # Sort to show labels of first prediction in order of confidence
            top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
            scores = {}
            for node_id in top_k:
                human_string = label_lines[node_id]
                score = predictions[0][node_id]
                data = {
                    human_string: score
                }
                scores.update(data)
            return scores

    def message_is_bad(self, scores: dict) -> bool:
        score = scores.get('nsfw')
        return score and score > self.NSFW_THRESHOLD

    def check_all_images(self) -> bool:
        """ Classify all images in Slack post """
        for image_url in self.urls:
            if self.link_is_image(image_url):
                image_path = self.download_image(image_url)
                scores = self.check_message(image_path)
                if self.message_is_bad(scores):
                    self.is_nsfw = True
                    return False
        return True

    def check_all_sites(self) -> bool:
        """ Classify all images that are within a Slack post containing a web page link """
        for url in self.urls:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            image_urls = [
                img.get('src')
                for img in soup.find_all('img')
                if img.get('src') is not None and 'http' in img.get('src')
            ]
            for image in image_urls:
                if self.link_is_image(image):
                    image_path = self.download_image(image)
                    scores = self.check_message(image_path)
                    if self.message_is_bad(scores):
                        self.is_nsfw = True
                        return False
            return True

    def check_textual_content(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        for url in self.urls:
            with contextlib.closing(webdriver.Chrome(chrome_options=options)) as driver:
                driver.get(url)
                word_list = ' '.join(driver.find_element_by_tag_name('body').get_attribute('innerText').split('\n')).split(' ')
                if any(predict(word_list)):
                    self.is_nsfw = True
                    return

    def cleanup(self) -> None:
        self.images_directory.cleanup()

    def run(self) -> None:
        fns = [self.check_textual_content, self.check_all_images, self.check_all_sites]
        for fn in fns:
            if self.is_nsfw:
                self.report_bad_message()
                break
            fn()
        if not self.is_nsfw:
            self.report_safe_message()
        self.cleanup()
