FROM mitmproxy/mitmproxy:5.1.1

RUN apk add --no-cache nginx \
    && mkdir -p /run/nginx

COPY src/assertions /src/assertions

COPY src/api_monitor/*.py \
     src/api_monitor/nginx.conf \
     src/api_monitor/start-proxy.sh \
     /src/api_monitor/

WORKDIR /src/api_monitor

RUN chmod a+x start-proxy.sh

ENTRYPOINT ./start-proxy.sh
