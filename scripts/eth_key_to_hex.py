#!/usr/bin/env python3
"""
Script to convert keystore files to raw hex private keys.

- `keystore files` are used to import/export identities into yagna
- `raw hex private keys` are used in metamask
"""

from eth_keyfile import extract_key_from_keyfile
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <private_key_json>")
        exit(1)

    print("Reading keyfile: " + sys.argv[1])
    eth_key_password = b""

    eth_key_hex = extract_key_from_keyfile(sys.argv[1], eth_key_password)

    print(eth_key_hex.hex())
