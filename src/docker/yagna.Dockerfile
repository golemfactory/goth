FROM python:3.8.2-alpine3.11 AS downloader
WORKDIR /
ARG GITHUB_API_TOKEN
ENV GITHUB_API_TOKEN ${GITHUB_API_TOKEN}
COPY ./download_artifact.py .
RUN pip install requests && ./download_artifact.py

FROM ubuntu:16.04
COPY --from=downloader /yagna.deb yagna.deb
RUN apt update && apt install -y ./yagna.deb
ENTRYPOINT /usr/bin/yagna
