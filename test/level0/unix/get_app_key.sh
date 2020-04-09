# Note: this depends on the specific output format from `yagna app-key list`
yagna app-key list \
    | grep "$KEY_NAME" \
    | sed -e 's/\s*│\s*/ /g' -e 's/^ //' \
    | cut -d ' ' -f2
