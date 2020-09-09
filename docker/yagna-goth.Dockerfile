FROM python:3.8.2-alpine3.11 AS downloader
WORKDIR /
ARG GITHUB_API_TOKEN
ARG YAGNA_COMMIT_HASH
ENV YAGNA_COMMIT_HASH $YAGNA_COMMIT_HASH
COPY ./download_artifacts.py ./download_release.py ./
RUN pip install requests \
    && python ./download_artifacts.py -t ${GITHUB_API_TOKEN} \
    && python ./download_release.py -t ${GITHUB_API_TOKEN} ya-runtime-wasi

FROM debian:bullseye-slim
COPY default/asset /asset
COPY default/asset/presets.json /presets.json
COPY --from=downloader /*.deb ./
RUN apt update && apt install -y ./*.deb
ENTRYPOINT /usr/bin/yagna
