FROM mitmproxy/mitmproxy:5.1.1

RUN apk add --no-cache nginx \
    && mkdir -p /run/nginx

COPY goth/assertions /goth/assertions

COPY goth/address.py /goth/address.py

COPY goth/api_monitor/*.py \
     goth/api_monitor/nginx.conf \
     goth/api_monitor/start-proxy.sh \
     /goth/api_monitor/

WORKDIR /goth/api_monitor

RUN chmod a+x start-proxy.sh

ENTRYPOINT ./start-proxy.sh
