#!/usr/bin/env python3
"""
Script to convert raw hex private keys to keystore files.

- `raw hex private keys` are found in the ganache logs ( ethereum-*.log )
- `keystore files` are used to import identities into yagna
"""

from eth_keyfile import create_keyfile_json
import json
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <private_key_hex>")
        exit(1)

    eth_key_hex = sys.argv[1][2:] if sys.argv[1].startswith("0x") else sys.argv[1]
    eth_key_bytes = bytearray.fromhex(eth_key_hex)
    eth_key_password = b""

    raw_keyfile = create_keyfile_json(eth_key_bytes, eth_key_password, iterations=2)
    json_keyffile = json.dumps(raw_keyfile)

    print(json_keyffile)
