FROM mitmproxy/mitmproxy:5.1.1

RUN apk add --no-cache nginx \
    && mkdir -p /run/nginx

COPY ya-int/assertions /src/assertions

COPY ya-int/api_monitor/*.py \
     ya-int/api_monitor/nginx.conf \
     ya-int/api_monitor/start-proxy.sh \
     /src/api_monitor/

WORKDIR /src/api_monitor

RUN chmod a+x start-proxy.sh

ENTRYPOINT ./start-proxy.sh
