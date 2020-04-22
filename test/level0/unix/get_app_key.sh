# Get app key from the yagna daemon

SCRIPT="\
import json, sys; \
j = json.load(sys.stdin); \
print(j['values'][0][1])"

yagna app-key list --json \
    | python3 -c "$SCRIPT"
