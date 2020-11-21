FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN set -ex \
    && pip install --upgrade pip \
    && pip install -r requirements.txt