FROM scx1332/goth_base:latest

RUN update-ca-certificates

COPY deb/* ./
COPY bin/* /usr/bin/

RUN chmod +x /usr/bin/* \
    && apt install -y ./*.deb \
    && ln -s /usr/bin/exe-unit /usr/lib/yagna/plugins/exe-unit

ENTRYPOINT /usr/bin/yagna
