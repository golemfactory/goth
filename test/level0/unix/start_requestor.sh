#!/bin/sh
# Start the requestor agent
export AGENT=1

NODE_ID=$(./with_env.sh requestor.env get_node_id.sh)
APP_KEY=$(./with_env.sh requestor.env get_app_key.sh)

echo "Node ID: $NODE_ID"
echo "App key: $APP_KEY"

set -o allexport
. ./requestor.env
set +o allexport

echo "YAGNA_ACTIVITY_URL: $YAGNA_ACTIVITY_URL" > /dev/stderr
echo "YAGNA_MARKET_URL: $YAGNA_MARKET_URL" > /dev/stderr

export RUST_LOG=info

ya-requestor --activity-url "$YAGNA_ACTIVITY_URL" \
	     --app-key "$APP_KEY" \
	     --exe-script "../asset/exe_script.json" \
	     --market-url "$YAGNA_MARKET_URL"
