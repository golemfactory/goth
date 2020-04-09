#!/bin/sh
# Kill the network hub.
HUB_PID=$(ps a \
	      | grep "ya_sb_router" \
	      | grep -v "grep" | \
	      sed 's/^ *\([0-9]\+\).*/\1/')
if [ -z "$HUB_PID" ]; then
    echo "Cannot find a running network hub process" > /dev/stderr
else
    kill -9 "$HUB_PID"
fi

