FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_EXTRA_INDEX_URL

WORKDIR /app

RUN apt-get update -y
RUN apt install -y git ruby-dev ruby-ffi redis-server wkhtmltopdf
RUN apt clean
RUN apt install -y python3-pip
RUN python3 -m pip install --no-cache-dir redis