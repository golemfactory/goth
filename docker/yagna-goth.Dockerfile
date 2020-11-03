FROM debian:bullseye-slim
COPY deb/* ./
COPY bin/* /usr/bin/
RUN apt update \
    && apt install -y ./*.deb \
    && apt install -y libssl-dev \
    && ln -s /usr/bin/exe-unit /usr/lib/yagna/plugins/exe-unit
ENTRYPOINT /usr/bin/yagna
