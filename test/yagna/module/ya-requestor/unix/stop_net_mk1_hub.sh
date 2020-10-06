#!/bin/sh
# Kill the network hub.
HUB_PID=$(pgrep "ya_sb_router")

if [ -z "$HUB_PID" ]; then
    echo "Cannot find a running network hub process" > /dev/stderr
else
    kill -9 "$HUB_PID"
fi
