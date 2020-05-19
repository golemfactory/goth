#!/bin/sh

if [ -e "./nginx.pid" ]; then
    echo "Reloading nginx configuration..."
    nginx -p . -c ./nginx.conf -s reload
else
    echo "Starting nginx..."
    nginx -p . -c ./nginx.conf &
fi

trap "nginx -p . -c ./nginx.conf -s stop" KILL

echo "Starting mitmproxy..."
mitmdump --mode reverse:"http://127.0.0.1" \
    --listen-port 9000 \
    -s ./router_addon.py \
    -s ./monitor_addon.py \
    --set assertions=level0_assertions
