#!/usr/bin/env python3
"""
Script to convert raw hex private keys to keystore files.

- `raw hex private keys` are found in the ganache logs ( ethereum.log )
- `keystore files` are used to import identities into yagna
"""

from eth_keyfile import extract_key_from_keyfile
import json
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <private_key_json>")
        exit(1)

    print("Reading keyfile: " + sys.argv[1])
    eth_key_password = b""

    eth_key_hex = extract_key_from_keyfile(sys.argv[1], eth_key_password)

    print(eth_key_hex.hex())
