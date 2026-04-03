#!/usr/bin/env python3
"""
Fetch UTXOs for a taproot address via the Blockstream testnet HTTP API
and pick a large enough output to fund the commit transaction.
"""

import requests


def get_available_utxos(address: str):
    """
    Return UTXOs for `address` (Bech32 / Bech32m testnet).

    Each dict: txid, vout, amount, scriptpubkey, scriptpubkey_address, note.
    """
    if not address:
        raise ValueError("Funding address is required (your key-path taproot address).")

    url = f"https://blockstream.info/testnet/api/address/{address}/utxo"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        utxo_list = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[ERROR] Could not list UTXOs: {e}")
        return []

    utxos = []
    for u in utxo_list:
        tx_url = f"https://blockstream.info/testnet/api/tx/{u['txid']}"
        tx_resp = requests.get(tx_url, timeout=15)
        if tx_resp.status_code == 200:
            tx_data = tx_resp.json()
            vout_data = tx_data["vout"][u["vout"]]
            utxos.append(
                {
                    "txid": u["txid"],
                    "vout": u["vout"],
                    "amount": u["value"],
                    "scriptpubkey": vout_data["scriptpubkey"],
                    "scriptpubkey_address": vout_data["scriptpubkey_address"],
                    "note": "API",
                }
            )
        else:
            utxos.append(
                {
                    "txid": u["txid"],
                    "vout": u["vout"],
                    "amount": u["value"],
                    "scriptpubkey": None,
                    "scriptpubkey_address": None,
                    "note": "API (scriptPubKey unknown)",
                }
            )
    return utxos


def select_best_utxo(min_amount: int, address: str):
    """Pick the largest UTXO with value >= min_amount, or None."""
    utxos = get_available_utxos(address)

    print("=== Scan available UTXOs ===")
    for i, utxo in enumerate(utxos):
        status = "OK" if utxo["amount"] >= min_amount else "too small"
        print(
            f"  {i + 1}. {utxo['txid'][:16]}...:{utxo['vout']} = "
            f"{utxo['amount']} sats — {status}"
        )

    suitable = [u for u in utxos if u["amount"] >= min_amount]
    if not suitable:
        print(f"[ERROR] No UTXO with at least {min_amount} sats")
        return None

    selected = max(suitable, key=lambda x: x["amount"])
    print(
        f"\nSelected UTXO: {selected['txid'][:16]}...:{selected['vout']} "
        f"({selected['amount']} sats)"
    )
    return selected
