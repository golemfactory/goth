# Get node id from the yagna daemon

SCRIPT="\
import json, sys; \
j = json.load(sys.stdin); \
print(j['Ok']['nodeId'])"

yagna id show --json \
    | python3 -c "$SCRIPT"
