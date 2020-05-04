FROM python:3.8.2-alpine3.11 AS downloader
WORKDIR /
ARG GITHUB_API_TOKEN
COPY ./download_artifacts.py ./download_release.py ./
RUN pip install requests \
    && ./download_artifacts.py -t ${GITHUB_API_TOKEN} \
    && ./download_release.py -t ${GITHUB_API_TOKEN} ya-runtime-wasi

FROM ubuntu:20.04
COPY --from=downloader /yagna.deb /ya-sb-router.deb ya-runtime-wasi.deb ./
RUN apt update && apt install -y ./yagna.deb ./ya-sb-router.deb ./ya-runtime-wasi.deb
ENTRYPOINT /usr/bin/yagna
