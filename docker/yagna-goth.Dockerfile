FROM python:3.8.6-alpine3.12 AS downloader
ARG GITHUB_API_TOKEN
ARG YAGNA_COMMIT_HASH
ARG YAGNA_DEB_PATH
ENV YAGNA_COMMIT_HASH $YAGNA_COMMIT_HASH
WORKDIR /
COPY download_artifacts.py download_release.py ${YAGNA_DEB_PATH:-*.deb}* ./
RUN pip install requests \
    && [[ -n "$YAGNA_DEB_PATH" ]] && yagna_artifact="" || yagna_artifact="yagna" \
    && python ./download_artifacts.py -t ${GITHUB_API_TOKEN} ya-sb-router $yagna_artifact \
    && python ./download_release.py -t ${GITHUB_API_TOKEN} ya-runtime-wasi

FROM debian:bullseye-slim
COPY --from=downloader /*.deb ./
RUN apt update && apt install -y ./*.deb
ENTRYPOINT /usr/bin/yagna
