from eth_keyfile import create_keyfile_json
import json

eth_key_password = b""
eth_key_hex = "50c8b3fc81e908501c8cd0a60911633acaca1a567d1be8e769c5ae7007b34b23"
eth_key_bytes = bytearray.fromhex(eth_key_hex)

raw_keyfile = create_keyfile_json(eth_key_bytes, eth_key_password, iterations=2)
json_keyffile = json.dumps(raw_keyfile)

print(json_keyffile)
