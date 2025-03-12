FROM python:3.11

WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt
RUN rm -rf /root/.cache/pip

COPY adapters_bio_tags_server.py /app
COPY adapters_bio_tags.py /app
COPY adapters_classifier.py /app
