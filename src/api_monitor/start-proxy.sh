#!/bin/sh

SCRIPT_DIR=$(dirname $0)
cd $SCRIPT_DIR

echo "Starting nginx..."
nginx -p . -c ./nginx.conf &
trap "[ ! -e ./nginx.pid ] || nginx -p . -c ./nginx.conf -s stop" EXIT

echo "Starting mitmproxy..."
export PYTHONPATH=../..:$PYTHONPATH
mitmdump --mode reverse:"http://127.0.0.1" \
    --listen-port 9000 \
    -q \
    -s ./router_addon.py \
    -s ./monitor_addon.py \
    --set assertions=assertions.level0_assertions