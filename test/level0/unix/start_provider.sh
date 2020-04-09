#!/bin/sh
# Start the provider agent

NODE_ID=$(./with_env.sh provider.env ./get_node_id.sh)
APP_KEY=$(./with_env.sh provider.env ./get_app_key.sh)

curl -X POST "http://localhost:5001/admin/import-key" \
     -H "accept: application/json" \
     -H "Content-Type: application/json-patch+json" \
     -d "[ { \"key\": \"${APP_KEY}\", \"nodeId\": \"${NODE_ID}\" }]"

set -o allexport
. ./provider.env
set +o allexport

export RUST_LOG=info
ya-provider --activity-url "$YAGNA_ACTIVITY_URL" \
	    --app-key "$APP_KEY" \
	    --credit-address "$NODE_ID" \
	    --market-url "$YAGNA_MARKET_URL"
	    # --exe-unit-path ../asset/local-exeunits-descriptor.json

