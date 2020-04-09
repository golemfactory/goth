#!/bin/sh
NODE_ID=$(./with_env.sh requestor.env get_node_id.sh)
APP_KEY=$(./with_env.sh requestor.env get_app_key.sh)

curl -X POST "http://localhost:5001/admin/import-key" \
     -H "accept: application/json" \
     -H "Content-Type: application/json-patch+json" \
     -d "[ { \"key\": \"${APP_KEY}\", \"nodeId\": \"${NODE_ID}\" }]"

set -o allexport
. ./requestor.env
set +o allexport

export RUST_LOG=info
ya-requestor --activity-url "$YAGNA_ACTIVITY_URL" \
	     --app-key "$APP_KEY" \
	     --exe-script "../asset/exe_script.json" \
	     --market-url "$YAGNA_MARKET_URL"
