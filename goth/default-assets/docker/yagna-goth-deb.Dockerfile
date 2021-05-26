# see: https://github.com/golemfactory/ya-service-bus/issues/31
FROM debian@sha256:bfc52d4a307296ece86057c74b899818fb154b33b42e8074a6bea848e84a3e71
COPY deb/* ./
RUN chmod +x /usr/bin/* \
    && apt update \
    && yes | apt install -y ./*.deb \
    && apt install -y libssl-dev ca-certificates \
    && update-ca-certificates
ENTRYPOINT /usr/bin/yagna
