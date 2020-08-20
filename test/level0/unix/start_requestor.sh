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

echo "Init payment"
yagna payment init ngnt -r ${NODE_ID}

ya-requestor --activity-url "$YAGNA_ACTIVITY_URL" \
       --app-key "$APP_KEY" \
       --exe-script "../asset/exe_script.json" \
       --market-url "$YAGNA_MARKET_URL" \
       --task-package "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1:http://34.244.4.185:8000/rust-wasi-tutorial.zip"
