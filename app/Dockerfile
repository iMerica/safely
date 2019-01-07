FROM python:3.7.1

WORKDIR /app

ENV PYTHONUNBUFFERED 1

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

CMD python app.py