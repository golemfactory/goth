# Get node id from the yagna daemon
# Note: this may easily break if the output format of `yagna id show` changes
yagna id show \
    | grep -Po '(?<=nodeId: )0x[0-9a-f]{40}'
