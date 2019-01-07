FROM tensorflow/tensorflow:latest-py3

WORKDIR /worker

ENV PYTHONUNBUFFERED 1

ENV DISPLAY :99

ADD requirements.txt .

RUN pip3 install -r requirements.txt

ENV PYTHON_EXECUTABLE=/usr/local/bin/python

ARG NSFW_MODEL=https://github.com/iMerica/models/raw/master/tensorflow/nsfw_classifier.pb

ADD $NSFW_MODEL /var/opt/nsfw_classifier.pb

ADD https://dl-ssl.google.com/linux/linux_signing_key.pub /var/opt/linux_signing_key.pub

RUN apt-key add /var/opt/linux_signing_key.pub

RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

RUN apt-get -y update

RUN apt-get install -y google-chrome-stable

RUN apt-get -y update

RUN apt-get install -y google-chrome-stable git

RUN LATEST_RELEASE=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q -O /tmp/chromedriver.zip \
    http://chromedriver.storage.googleapis.com/$LATEST_RELEASE/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver

ADD . .

CMD celery -A src.task worker --loglevel=DEBUG -Q safely