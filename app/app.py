import logging
import os
import time

from celery import Celery
from slackclient import SlackClient
from urlextract import URLExtract

QUEUE_NAME = os.getenv('SAFELY_QUEUE_NAME', 'safely')
app = Celery(QUEUE_NAME, broker=os.getenv('BROKER_URL'))
logger = logging.getLogger('safely')

logger.setLevel(logging.INFO)


class Listener:
    def __init__(self):
        self.token = os.environ.get('SAFELY_SLACKBOT_TOKEN')
        self.slack_client = SlackClient(self.token)
        self.link_extractor = URLExtract()

    @staticmethod
    def is_message(event: dict) -> bool:
        return event.get('type') == 'message'

    def contains_link(self, event: dict) -> bool:
        """ Does this message contain a link? """
        return len(self.link_extractor.find_urls(event.get('text', ''))) > 0

    def event_with_link(self, event: dict) -> bool:
        """ Is this a message AND does the message container a link? """
        return self.is_message(event) and self.contains_link(event)

    @staticmethod
    def check_message(text: str, channel: str, author: str, timestamp: str) -> None:
        """ Dispatch a celery task that checks if this is a naughty message """
        kwargs = dict(text=text, channel=channel, author=author, timestamp=timestamp)
        app.send_task('check_message', kwargs=kwargs, queue=QUEUE_NAME)

    def run(self) -> None:
        logger.info('Beginning event loop...')
        if self.slack_client.rtm_connect(with_team_state=False):
            while True:
                time.sleep(1)
                events = self.slack_client.rtm_read()
                for event in events:
                    if self.event_with_link(event):
                        channel = event.get('channel')
                        text = event.get('text')
                        author = event.get('user')
                        timestamp = event.get('ts')
                        self.check_message(text, channel, author, timestamp)


if __name__ == '__main__':
    logger.warning('Running ...')
    Listener().run()
