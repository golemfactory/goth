FROM python:3.8.6-alpine3.12 AS downloader
ARG GITHUB_API_TOKEN
ARG YAGNA_BRANCH
ARG YAGNA_COMMIT_HASH
ENV YAGNA_COMMIT_HASH $YAGNA_COMMIT_HASH
WORKDIR /
COPY download_artifacts.py download_release.py ./
RUN pip install requests \
    && mkdir yagna-binaries \
    && python ./download_artifacts.py -b ${YAGNA_BRANCH} -t ${GITHUB_API_TOKEN} -o yagna-binaries \
    && chmod +x yagna-binaries/* \
    && python ./download_release.py -t ${GITHUB_API_TOKEN} ya-runtime-wasi

FROM debian:bullseye-slim
COPY --from=downloader /yagna-binaries/* /usr/bin/
COPY --from=downloader /*.deb ./
RUN apt update && apt install -y ./*.deb && apt install -y libssl-dev
ENTRYPOINT /usr/bin/yagna
