#!/usr/bin/env python3
"""
Chapter 10 — Verify an RGB transfer transaction on-chain.

Fetches a testnet transaction from the public Esplora API and prints
output types. Use this to confirm that the RGB transfer looks like an
ordinary Taproot transaction: both outputs are v1_p2tr, no OP_RETURN,
no visible RGB marker.

No rgb CLI required — stdlib only.

Usage:
  python3 02_verify_tx_onchain.py <txid>
  python3 02_verify_tx_onchain.py 64a1455125724ce79d4914d7af5e0226f465c7522b8dd6f048440b8935c20b6b
"""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error

ESPLORA_BASE = "https://mempool.space/testnet/api"


def fetch_tx(txid: str) -> dict:
    url = f"{ESPLORA_BASE}/tx/{txid}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "mastering-taproot-ch10/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <txid>", file=sys.stderr)
        return 1

    txid = sys.argv[1].strip()
    tx = fetch_tx(txid)

    print(f"txid: {tx.get('txid', '?')}")
    print(f"inputs: {len(tx.get('vin', []))}")
    print()

    for i, vout in enumerate(tx.get("vout", [])):
        script_type = vout.get("scriptpubkey_type", "?")
        value = vout.get("value", "?")
        addr = vout.get("scriptpubkey_address", "")
        print(f"  vout[{i}]  type={script_type}  value={value} sats  {addr}")

    # Check: are all outputs P2TR?
    types = [v.get("scriptpubkey_type") for v in tx.get("vout", [])]
    all_p2tr = all(t == "v1_p2tr" for t in types)
    has_opreturn = any(t == "op_return" for t in types)

    print()
    if all_p2tr and not has_opreturn:
        print("All outputs are P2TR. No OP_RETURN. Indistinguishable from a normal Taproot spend.")
    elif has_opreturn:
        print("Note: OP_RETURN output present (opret commitment scheme, not tapret).")
    else:
        print(f"Output types: {types}")

    print(f"\nExplorer: https://mempool.space/testnet/tx/{txid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
