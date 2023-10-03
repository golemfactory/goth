FROM ghcr.io/golemfactory/goth/yagna-goth-base:1.0.0

RUN update-ca-certificates

COPY deb/* ./
COPY bin/* /usr/bin/

RUN chmod +x /usr/bin/* \
    && apt install -y ./*.deb \
    && ln -s /usr/bin/exe-unit /usr/lib/yagna/plugins/exe-unit

ENTRYPOINT /usr/bin/yagna
