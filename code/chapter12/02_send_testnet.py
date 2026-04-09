#!/usr/bin/env python3
"""
Chapter 12 — Send a real testnet transaction to a Silent Payment one-time address

Reads the derived address from 01_silent_payment_derive.py (sp_derived.json),
builds a transaction sending testnet coins to the one-time P2TR address.

What the chain sees: an ordinary Taproot transfer. No SP metadata on-chain.

Usage:
  # First run 01 to derive the address:
  python3 01_silent_payment_derive.py

  # Then send:
  python3 02_send_testnet.py --fund-txid <txid> --fund-vout <n> --fund-amount <sats>
"""

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, PublicKey, P2trAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
import argparse
import json
import sys

setup('testnet')

ALICE_WIF = 'cRxebG1hY6vVgS9CSLNaEbEJaXkpZvc6nFeqqGT7v6gcW7MbzKNT'
alice_priv = PrivateKey(ALICE_WIF)
alice_pub = alice_priv.get_public_key()


def main():
    p = argparse.ArgumentParser(description="Send testnet coins to Silent Payment one-time address")
    p.add_argument("--fund-txid", required=True, help="Alice's funding UTXO txid")
    p.add_argument("--fund-vout", type=int, default=0, help="Funding vout")
    p.add_argument("--fund-amount", type=int, default=10000, help="Funding amount in sats")
    p.add_argument("--send-amount", type=int, default=5000, help="Amount to send to SP address")
    args = p.parse_args()

    # Load derived SP address
    try:
        with open("sp_derived.json") as f:
            sp = json.load(f)
    except FileNotFoundError:
        print("Error: run 01_silent_payment_derive.py first to generate sp_derived.json", file=sys.stderr)
        return 1

    sp_address = sp["one_time_address"]
    sp_spk_hex = sp["one_time_scriptpubkey"]

    fee = 154
    change = args.fund_amount - args.send_amount - fee

    if change < 0:
        print(f"Error: insufficient funds ({args.fund_amount} < {args.send_amount} + {fee})", file=sys.stderr)
        return 1

    print("=" * 70)
    print("Silent Payment: Send to One-Time Address")
    print("=" * 70)
    print(f"  From: Alice's UTXO {args.fund_txid}:{args.fund_vout} ({args.fund_amount} sats)")
    print(f"  To:   {sp_address} ({args.send_amount} sats)")
    print(f"  Change back to Alice: {change} sats")
    print(f"  Fee:  {fee} sats")
    print()

    # Alice's Taproot address for change
    alice_addr = alice_pub.get_taproot_address()

    # SP one-time address
    sp_pub = PublicKey("02" + sp["one_time_x_only"])
    sp_addr = sp_pub.get_taproot_address()

    # Build transaction
    outputs = [
        TxOutput(args.send_amount, sp_addr.to_script_pub_key()),
    ]
    if change > 546:  # dust threshold
        outputs.append(
            TxOutput(change, alice_addr.to_script_pub_key()),
        )

    tx = Transaction(
        [TxInput(args.fund_txid, args.fund_vout)],
        outputs,
        has_segwit=True
    )

    # Sign (Alice's key-path spend)
    sig = alice_priv.sign_taproot_input(
        tx, 0,
        [alice_addr.to_script_pub_key()],
        [args.fund_amount],
        script_path=False
    )
    tx.witnesses.append(TxWitnessInput([sig]))

    signed_hex = tx.serialize()

    print(f"  txid: {tx.get_txid()}")
    print(f"  Size: {len(signed_hex) // 2} bytes, vsize: {tx.get_vsize()} vbytes")
    print()
    print("  What the chain sees:")
    print(f"    Input:  Alice's Taproot UTXO")
    print(f"    Output: {sp_address}")
    print(f"    Witness: [64-byte Schnorr signature]")
    print(f"    → Looks like an ordinary Taproot payment")
    print(f"    → No SP metadata, no special markers")
    print()
    print(f"  Raw hex:")
    print(f"  {signed_hex}")
    print()
    print(f"  Broadcast: bitcoin-cli -testnet sendrawtransaction {signed_hex[:60]}...")

    # Save for verification
    result = {
        "txid": tx.get_txid(),
        "sp_address": sp_address,
        "send_amount": args.send_amount,
        "raw_hex": signed_hex,
    }
    with open("sp_send_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Saved to sp_send_result.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
