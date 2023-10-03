FROM docker.pkg.github.com/golemfactory/goth/yagna-goth-base:1.0.0

RUN update-ca-certificates

COPY deb/* ./
RUN chmod +x /usr/bin/* \
    && yes | apt install -y ./*.deb

ENTRYPOINT /usr/bin/yagna
