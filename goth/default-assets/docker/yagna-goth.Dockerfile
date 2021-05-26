# see: https://github.com/golemfactory/ya-service-bus/issues/31
FROM debian@sha256:bfc52d4a307296ece86057c74b899818fb154b33b42e8074a6bea848e84a3e71
COPY deb/* ./
COPY bin/* /usr/bin/
RUN chmod +x /usr/bin/* \
    && apt update \
    && apt install -y ./*.deb \
    && apt install -y libssl-dev ca-certificates \
    && update-ca-certificates \
    && ln -s /usr/bin/exe-unit /usr/lib/yagna/plugins/exe-unit
ENTRYPOINT /usr/bin/yagna
