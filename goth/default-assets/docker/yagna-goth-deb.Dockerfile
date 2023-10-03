FROM scx1332/goth_base:latest

RUN update-ca-certificates

COPY deb/* ./
RUN chmod +x /usr/bin/* \
    && yes | apt install -y ./*.deb

ENTRYPOINT /usr/bin/yagna
