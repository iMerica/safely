import logging
import os

from celery import Celery

from .main import Moderator

QUEUE_NAME = os.getenv('SAFELY_QUEUE_NAME', 'safely')
logger = logging.getLogger(QUEUE_NAME)
app = Celery(QUEUE_NAME, broker=os.getenv('BROKER_URL'))


@app.task(name='check_message')
def check_message(text, channel, author, timestamp):
    Moderator(text, channel, author, timestamp).run()
    return True
