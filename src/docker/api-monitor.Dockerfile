FROM python:3.7.7-alpine3.11

RUN apk add --no-cache gcc g++ libffi-dev linux-headers musl-dev openssl-dev python-dev

RUN apk add --no-cache nginx \
    && mkdir -p /run/nginx

RUN pip install mitmproxy==5.1.1

COPY src/assertions /src/assertions

COPY src/api_monitor/*.py \
     src/api_monitor/nginx.conf \
     src/api_monitor/start-proxy.sh \
     /src/api_monitor/

WORKDIR /src/api_monitor

RUN chmod a+x start-proxy.sh

ENTRYPOINT ./start-proxy.sh
