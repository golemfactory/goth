FROM mitmproxy/mitmproxy:5.1.1

RUN apk add --no-cache nginx \
    && mkdir -p /run/nginx

COPY ya-int/assertions /ya-int/assertions

COPY ya-int/api_monitor/*.py \
     ya-int/api_monitor/nginx.conf \
     ya-int/api_monitor/start-proxy.sh \
     /ya-int/api_monitor/

WORKDIR /ya-int/api_monitor

RUN chmod a+x start-proxy.sh

ENTRYPOINT ./start-proxy.sh
