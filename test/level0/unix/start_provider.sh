#!/bin/sh
# Start the provider agent
export AGENT=1

NODE_ID=$(./with_env.sh provider.env ./get_node_id.sh)
APP_KEY=$(./with_env.sh provider.env ./get_app_key.sh)

echo "Node ID: $NODE_ID"
echo "App key: $APP_KEY"

set -o allexport
. ./provider.env
set +o allexport

echo "YAGNA_ACTIVITY_URL: $YAGNA_ACTIVITY_URL" > /dev/stderr
echo "YAGNA_MARKET_URL: $YAGNA_MARKET_URL" > /dev/stderr


# The file `presets.json` is required in the current dir.
[ -f "./presets.json" ] || cp ../asset/presets.json .

# This preset must be defined in `presets.json`:
PRESET_NAME=amazing-offer

# This is the standard location of `exeunits-descriptor.json`
# for `ya-provider` installed from `.deb` package:
EXE_UNIT_PATH="/usr/lib/yagna/plugins/exeunits-descriptor.json"

export RUST_LOG=info

ya-provider --exe-unit-path "$EXE_UNIT_PATH" \
	    run \
	    --activity-url "$YAGNA_ACTIVITY_URL" \
	    --app-key "$APP_KEY" \
	    --market-url "$YAGNA_MARKET_URL" \
	    --node-name test-provider \
	    "$PRESET_NAME"
