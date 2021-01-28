FROM debian:bullseye-slim
COPY deb/* ./
RUN chmod +x /usr/bin/* \
    && apt update \
    && yes | apt install -y ./*.deb \
    && apt install -y libssl-dev
ENTRYPOINT /usr/bin/yagna
