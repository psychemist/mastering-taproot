#!/usr/bin/env python3
"""
BRC-20 mint — REVEAL (script-path spend from temporary address).

Requires: commit tx confirmed, and commit_mint_info.json from step 1.
"""

import json

from bitcoinutils.setup import setup
from bitcoinutils.utils import ControlBlock
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.keys import PrivateKey

from tools.brc20_config import (
    PRIVATE_KEY_WIF,
    NETWORK,
    FEE_CONFIG,
    get_brc20_hex,
    INSCRIPTION_CONFIG,
    get_brc20_json,
)


def load_commit_info():
    try:
        with open("commit_mint_info.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] commit_mint_info.json not found — run 1_commit_mint_brc20.py first")
        return None


def create_mint_reveal_transaction():
    setup(NETWORK)

    print("=== BRC-20 mint — REVEAL ===")

    commit_info = load_commit_info()
    if not commit_info or commit_info.get("operation") != "mint":
        return None

    print(f"COMMIT txid: {commit_info['commit_txid']}")
    print(f"Temporary address: {commit_info['temp_address']}")
    print(f"MINT payload: {get_brc20_json('mint')}")

    private_key = PrivateKey.from_wif(PRIVATE_KEY_WIF)
    public_key = private_key.get_public_key()
    key_path_address = public_key.get_taproot_address()

    if key_path_address.to_string() != commit_info["key_path_address"]:
        print("[ERROR] Key does not match commit step (check BRC20_WIF)")
        return None

    brc20_hex = get_brc20_hex("mint")
    inscription_script = Script(
        [
            public_key.to_x_only_hex(),
            "OP_CHECKSIG",
            "OP_0",
            "OP_IF",
            INSCRIPTION_CONFIG["ord_marker"],
            "OP_1",
            INSCRIPTION_CONFIG["content_type_hex"],
            "OP_0",
            brc20_hex,
            "OP_ENDIF",
        ]
    )

    temp_address = public_key.get_taproot_address([[inscription_script]])
    if temp_address.to_string() != commit_info["temp_address"]:
        print("[ERROR] Rebuilt temporary address does not match commit_mint_info.json")
        return None

    inscription_amount = commit_info["inscription_amount"]
    reveal_fee = FEE_CONFIG["reveal_fee"]
    output_amount = inscription_amount - reveal_fee

    if output_amount < FEE_CONFIG["min_output"]:
        output_amount = FEE_CONFIG["min_output"]
        reveal_fee = inscription_amount - output_amount
        print(f"[INFO] Adjusted reveal fee to {reveal_fee} sats (dust floor)")

    tx_input = TxInput(commit_info["commit_txid"], 0)
    tx_output = TxOutput(output_amount, key_path_address.to_script_pub_key())
    reveal_tx = Transaction([tx_input], [tx_output], has_segwit=True)

    try:
        signature = private_key.sign_taproot_input(
            reveal_tx,
            0,
            [temp_address.to_script_pub_key()],
            [inscription_amount],
            script_path=True,
            tapleaf_script=inscription_script,
            tweak=False,
        )

        control_block = ControlBlock(
            public_key,
            [[inscription_script]],
            0,
            is_odd=temp_address.is_odd(),
        )

        reveal_tx.witnesses.append(
            TxWitnessInput(
                [signature, inscription_script.to_hex(), control_block.to_hex()]
            )
        )

        print(f"\nREVEAL txid: {reveal_tx.get_txid()}")
        print(f"wtxid: {reveal_tx.get_wtxid()}")
        print(f"vsize: {reveal_tx.get_vsize()} vB")

        return reveal_tx

    except Exception as e:
        print(f"[ERROR] Signing failed: {e}")
        return None


def print_broadcast_help(reveal_tx):
    if not reveal_tx:
        return
    print("\n" + "=" * 60)
    print("Raw transaction (hex)")
    print("=" * 60)
    print(reveal_tx.serialize())
    print()
    print("Example broadcast:")
    print(f"  bitcoin-cli -{NETWORK} sendrawtransaction {reveal_tx.serialize()}")
    print()
    print(
        "After broadcast, check the tx on a testnet explorer: witness should list "
        "signature, inscription script, and control block. "
        "BRC-20 / indexer-visible semantics are defined off-chain (see Chapter 9)."
    )


if __name__ == "__main__":
    reveal_tx = create_mint_reveal_transaction()
    if not reveal_tx:
        print("[ERROR] REVEAL build failed")
        raise SystemExit(1)
    print_broadcast_help(reveal_tx)
