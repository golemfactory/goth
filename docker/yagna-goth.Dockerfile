FROM python:3.8.6-alpine3.12 AS downloader
ARG GITHUB_API_TOKEN
ARG YAGNA_BRANCH=master
ARG YAGNA_COMMIT_HASH
ARG YAGNA_DEB_PATH
ENV YAGNA_COMMIT_HASH $YAGNA_COMMIT_HASH
WORKDIR /
# If YAGNA_DEB_PATH is not empty then copy whatever it's pointing to (either a file or a directory), otherwise copy harmless stuff from context (in this case - .md files)
COPY download_artifacts.py download_release.py ${YAGNA_DEB_PATH:-*.md}* ./
RUN pip install requests \
    # If YAGNA_DEB_PATH is empty then download the `yagna` artifact from Actions
    && [[ -n "$YAGNA_DEB_PATH" ]] && yagna_artifact="" || yagna_artifact="yagna" \
    && python ./download_artifacts.py -b ${YAGNA_BRANCH} -t ${GITHUB_API_TOKEN} ya-sb-router $yagna_artifact \
    && python ./download_release.py -t ${GITHUB_API_TOKEN} ya-runtime-wasi

FROM debian:bullseye-slim
COPY --from=downloader /*.deb ./
RUN apt update && apt install -y ./*.deb
ENTRYPOINT /usr/bin/yagna
