## Scripts

This directory contains Python scripts related to the repo.

To run a script, call `python -m scripts.{script_name} [ARGS]` from the project's root
directory.

Example:
```
python -m scripts.download_artifacts -v
```

## Ethereum Key Conversion Scripts

To help convert keys from hex to json there are 2 scripts:
- eth_key_to_hex.py
- eth_hex_to_key.py

Before using these scripts you need to install one extra dependency.

```
pip install eth_keyfile
```

Then you can convert a key to hex:
```
python -m scripts.eth_key_to_hex ./path-to-key.json
```

Or you can convert a hex to key:
```
python -m scripts.eth_hex_to_key 0x1234567890abcdef...
```
