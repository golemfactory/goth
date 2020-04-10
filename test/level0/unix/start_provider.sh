#!/bin/sh
# Start the provider agent

NODE_ID=$(./with_env.sh provider.env ./get_node_id.sh)
APP_KEY=$(./with_env.sh provider.env ./get_app_key.sh)

set -o allexport
. ./provider.env
set +o allexport

# This is to make sure app keys are exported, since
# right now we cannot rely on the daemon doing this
curl -X POST "${MARKET_URL_BASE}/admin/import-key" \
     -H "accept: application/json" \
     -H "Content-Type: application/json-patch+json" \
     -d "[ { \"key\": \"${APP_KEY}\", \"nodeId\": \"${NODE_ID}\" }]"

export RUST_LOG=info
ya-provider --activity-url "$YAGNA_ACTIVITY_URL" \
	    --app-key "$APP_KEY" \
	    --credit-address "$NODE_ID" \
	    --market-url "$YAGNA_MARKET_URL"
