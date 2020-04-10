#!/bin/sh
# Start the requestor agent

NODE_ID=$(./with_env.sh requestor.env get_node_id.sh)
APP_KEY=$(./with_env.sh requestor.env get_app_key.sh)

set -o allexport
. ./requestor.env
set +o allexport

# This is to make sure app keys are exported, since
# right now we cannot rely on the daemon doing this
curl -X POST "${MARKET_URL_BASE}/admin/import-key" \
     -H "accept: application/json" \
     -H "Content-Type: application/json-patch+json" \
     -d "[ { \"key\": \"${APP_KEY}\", \"nodeId\": \"${NODE_ID}\" }]"

export RUST_LOG=info
ya-requestor --activity-url "$YAGNA_ACTIVITY_URL" \
	     --app-key "$APP_KEY" \
	     --exe-script "../asset/exe_script.json" \
	     --market-url "$YAGNA_MARKET_URL"
