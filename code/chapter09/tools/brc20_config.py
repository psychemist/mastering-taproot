#!/usr/bin/env python3
"""
BRC-20 configuration for the Chapter 9 commit / reveal scripts.

Default WIF matches the testnet example in the book (public demo key).
Override with environment variable BRC20_WIF for your own testnet wallet.
"""

import os

# Private key (testnet WIF). Same default as Chapter 9 worked example.
PRIVATE_KEY_WIF = os.environ.get(
    "BRC20_WIF",
    "cRxebG1hY6vVgS9CSLNaEbEJaXkpZvc6nFeqqGT7v6gcW7MbzKNT",
)

NETWORK = "testnet"

FEE_CONFIG = {
    "commit_fee": 300,
    "reveal_fee": 500,
    "min_output": 546,
}

TOKEN_CONFIG = {
    "mint": {
        "p": "brc-20",
        "op": "mint",
        "tick": "DEMO",
        "amt": "1000",
    },
}

INSCRIPTION_CONFIG = {
    "content_type_hex": "746578742f706c61696e3b636861727365743d7574662d38",
    "ord_marker": "6f7264",
}


def get_brc20_json(op_type="mint"):
    if op_type not in TOKEN_CONFIG:
        raise ValueError(f"Unsupported operation type: {op_type}")
    import json

    return json.dumps(TOKEN_CONFIG[op_type], separators=(",", ":"))


def get_brc20_hex(op_type="mint"):
    return get_brc20_json(op_type).encode("utf-8").hex()


def calculate_inscription_amount():
    return FEE_CONFIG["min_output"] + FEE_CONFIG["reveal_fee"]
