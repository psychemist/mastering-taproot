#!/usr/bin/env python3
"""
BRC-20 mint — COMMIT (key-path spend to temporary taproot address).

Run order: this script -> broadcast raw tx -> wait for confirmation -> 2_reveal_mint_brc20.py
"""

import json

from bitcoinutils.setup import setup
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.keys import PrivateKey, P2trAddress

from tools.utxo_scanner import select_best_utxo
from tools.brc20_config import (
    PRIVATE_KEY_WIF,
    NETWORK,
    FEE_CONFIG,
    get_brc20_hex,
    calculate_inscription_amount,
    INSCRIPTION_CONFIG,
    get_brc20_json,
)


def create_mint_commit_transaction():
    setup(NETWORK)

    print("=== BRC-20 mint — COMMIT ===")
    print(f"MINT payload: {get_brc20_json('mint')}")

    private_key = PrivateKey.from_wif(PRIVATE_KEY_WIF)
    public_key = private_key.get_public_key()
    key_path_address = public_key.get_taproot_address()

    print(f"Key-path (funding) address: {key_path_address.to_string()}")

    inscription_amount = calculate_inscription_amount()
    min_utxo_amount = inscription_amount + FEE_CONFIG["commit_fee"] + 546

    selected_utxo = select_best_utxo(min_utxo_amount, key_path_address.to_string())
    if not selected_utxo:
        return None, None, None

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

    print(f"\nTemporary (commit) address: {temp_address.to_string()}")
    print(f"Inscription script hex: {inscription_script.to_hex()}")

    utxo_amount = selected_utxo["amount"]
    commit_fee = FEE_CONFIG["commit_fee"]
    change_amount = utxo_amount - inscription_amount - commit_fee

    print("\n=== Amounts ===")
    print(f"Input UTXO: {utxo_amount} sats")
    print(f"Output to temporary address: {inscription_amount} sats")
    print(f"Commit fee: {commit_fee} sats")
    print(f"Change: {change_amount} sats")

    if change_amount < 0:
        print("[ERROR] Insufficient funds for inscription + fee")
        return None, None, None

    if 0 < change_amount < 546:
        print(f"[WARN] Change {change_amount} sats below dust; adding to fee")
        commit_fee += change_amount
        change_amount = 0

    tx_input = TxInput(selected_utxo["txid"], selected_utxo["vout"])
    outputs = [TxOutput(inscription_amount, temp_address.to_script_pub_key())]
    if change_amount > 0:
        outputs.append(TxOutput(change_amount, key_path_address.to_script_pub_key()))

    commit_tx = Transaction([tx_input], outputs, has_segwit=True)

    try:
        if selected_utxo.get("scriptpubkey_address"):
            utxo_address = P2trAddress(selected_utxo["scriptpubkey_address"])
            script_pubkey_for_signing = utxo_address.to_script_pub_key()
        else:
            script_pubkey_for_signing = key_path_address.to_script_pub_key()
            print("[WARN] Missing scriptPubKey address; signing with key-path scriptPubKey")

        signature = private_key.sign_taproot_input(
            commit_tx,
            0,
            [script_pubkey_for_signing],
            [utxo_amount],
        )
        commit_tx.witnesses.append(TxWitnessInput([signature]))

        print(f"\nCOMMIT txid: {commit_tx.get_txid()}")
        print(f"vsize: {commit_tx.get_vsize()} vB")

        return commit_tx, temp_address, key_path_address

    except Exception as e:
        print(f"[ERROR] Signing failed: {e}")
        return None, None, None


def print_broadcast_help(commit_tx):
    if not commit_tx:
        return
    print("\n" + "=" * 60)
    print("Raw transaction (hex)")
    print("=" * 60)
    print(commit_tx.serialize())
    print()
    print("Example broadcast (adjust for your node):")
    print(f"  bitcoin-cli -{NETWORK} sendrawtransaction {commit_tx.serialize()}")
    print()
    print("Or use a testnet pushtx page, then wait for confirmation before reveal.")


if __name__ == "__main__":
    commit_tx, temp_address, key_path_address = create_mint_commit_transaction()

    if not commit_tx:
        print("[ERROR] COMMIT build failed")
        raise SystemExit(1)

    commit_info = {
        "commit_txid": commit_tx.get_txid(),
        "temp_address": temp_address.to_string(),
        "key_path_address": key_path_address.to_string(),
        "inscription_amount": calculate_inscription_amount(),
        "operation": "mint",
    }
    with open("commit_mint_info.json", "w", encoding="utf-8") as f:
        json.dump(commit_info, f, indent=2)
    print("\nWrote commit_mint_info.json (needed for reveal step).")

    print_broadcast_help(commit_tx)
