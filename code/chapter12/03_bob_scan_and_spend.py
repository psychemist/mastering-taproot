#!/usr/bin/env python3
"""
Chapter 12 — Bob scans the chain and proves he can spend

Simulates Bob's scanning process:
  1. Given a transaction's input pubkey and outputs
  2. Bob uses b_scan to compute ECDH → derive expected one-time address
  3. Check if any output matches → "this payment is for me"
  4. Compute the spending private key and sign a spend transaction

Usage:
  python3 03_bob_scan_and_spend.py
  python3 03_bob_scan_and_spend.py --sp-txid <txid> --sp-vout <n> --sp-amount <sats>
"""

import hashlib
import json
import sys
import argparse
from coincurve import PrivateKey as CPrivateKey, PublicKey as CPublicKey

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, PublicKey
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput

setup('testnet')

SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

BOB_WIF = 'cSNdLFDf3wjx1rswNL2jKykbVkC6o56o5nYZi4FUkWKjFn2Q5DSG'


def tagged_hash(tag: str, data: bytes) -> bytes:
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


def main():
    p = argparse.ArgumentParser(description="Bob scans and spends a Silent Payment")
    p.add_argument("--sp-txid", default="", help="The SP transaction txid (for real spend)")
    p.add_argument("--sp-vout", type=int, default=0, help="The SP output vout")
    p.add_argument("--sp-amount", type=int, default=5000, help="Amount in the SP output")
    args = p.parse_args()

    # Load derivation data
    try:
        with open("sp_derived.json") as f:
            sp = json.load(f)
    except FileNotFoundError:
        print("Error: run 01_silent_payment_derive.py first", file=sys.stderr)
        return 1

    # Bob's keys
    bob_scan_priv = CPrivateKey(hashlib.sha256(b"bob_scan_secret_mastering_taproot").digest())
    bob_spend_priv = CPrivateKey(hashlib.sha256(b"bob_spend_secret_mastering_taproot").digest())
    bob_spend_pub = bob_spend_priv.public_key

    # Alice's input pubkey — in a full BIP352 implementation Bob would parse
    # this from each transaction's vin (scriptSig / witness).  Here we read it
    # from sp_derived.json for simplicity; the ECDH and key derivation are real.
    alice_input_pub = CPublicKey(bytes.fromhex(sp["alice_input_pub"]))

    print("=" * 70)
    print("Bob Scans the Chain")
    print("=" * 70)
    print(f"  Bob's scan key (b_scan): {bob_scan_priv.secret.hex()[:16]}...")
    print(f"  Alice's input pubkey (from chain): {alice_input_pub.format().hex()}")
    print()

    # Step 1: ECDH
    shared_secret = alice_input_pub.multiply(bob_scan_priv.secret)
    print(f"  ECDH (b_scan · A): {shared_secret.format().hex()}")

    # Step 2: Derive expected one-time pubkey
    k = 0
    t_k = tagged_hash(
        "BIP0352/SharedSecret",
        shared_secret.format() + k.to_bytes(4, 'big')
    )
    tweak_point = CPrivateKey(t_k).public_key
    expected_pubkey = CPublicKey.combine_keys([bob_spend_pub, tweak_point])
    expected_x_only = expected_pubkey.format(compressed=True)[1:].hex()

    print(f"  Expected one-time key: {expected_x_only}")
    print(f"  Expected address:      {sp['one_time_address']}")

    # Step 3: Match against transaction outputs
    target_x_only = sp["one_time_x_only"]
    match = expected_x_only == target_x_only
    print()
    print(f"  Output x-only key:     {target_x_only}")
    print(f"  Match: {match}")

    if match:
        print(f"\n  ✅ Bob found his payment!")
    else:
        print(f"\n  ❌ No match — this transaction is not for Bob")
        return 0

    # Step 4: Compute spending private key
    print()
    print("=" * 70)
    print("Bob Computes Spending Key")
    print("=" * 70)

    b_spend_int = int.from_bytes(bob_spend_priv.secret, 'big')
    t_k_int = int.from_bytes(t_k, 'big')
    one_time_privkey_int = (b_spend_int + t_k_int) % SECP256K1_ORDER
    one_time_privkey_bytes = one_time_privkey_int.to_bytes(32, 'big')

    # Verify
    one_time_priv = CPrivateKey(one_time_privkey_bytes)
    derived_pub = one_time_priv.public_key
    print(f"  p = b_spend + t_k: {one_time_privkey_bytes.hex()}")
    print(f"  p·G matches P:     {derived_pub.format() == expected_pubkey.format()}")

    # Step 5: If we have a real txid, build a spend transaction
    if args.sp_txid:
        print()
        print("=" * 70)
        print("Bob Spends the Silent Payment Output")
        print("=" * 70)

        # Bob's regular address for receiving
        bob_btc_priv = PrivateKey(BOB_WIF)
        bob_addr = bob_btc_priv.get_public_key().get_taproot_address()

        fee = 154
        spend_amount = args.sp_amount - fee

        # The one-time address
        sp_pub = PublicKey("02" + target_x_only)
        sp_addr = sp_pub.get_taproot_address()

        tx = Transaction(
            [TxInput(args.sp_txid, args.sp_vout)],
            [TxOutput(spend_amount, bob_addr.to_script_pub_key())],
            has_segwit=True
        )

        # Sign with the one-time private key
        # Need to create a bitcoinutils PrivateKey from raw bytes
        # Convert to WIF first
        import base58
        prefix = b'\xef'  # testnet
        extended = prefix + one_time_privkey_bytes + b'\x01'
        checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
        wif = base58.b58encode(extended + checksum).decode()
        one_time_btc_priv = PrivateKey(wif)

        sig = one_time_btc_priv.sign_taproot_input(
            tx, 0,
            [sp_addr.to_script_pub_key()],
            [args.sp_amount],
            script_path=False
        )
        tx.witnesses.append(TxWitnessInput([sig]))

        signed_hex = tx.serialize()

        print(f"  Spending: {args.sp_txid}:{args.sp_vout} ({args.sp_amount} sats)")
        print(f"  To: Bob's address {bob_addr.to_string()} ({spend_amount} sats)")
        print(f"  Fee: {fee} sats")
        print()
        print(f"  txid: {tx.get_txid()}")
        print(f"  Raw hex:")
        print(f"  {signed_hex}")
        print()
        print(f"  Broadcast: bitcoin-cli -testnet sendrawtransaction {signed_hex[:60]}...")
        print()
        print("  What the chain sees:")
        print("    Input:  a Taproot UTXO (no SP markers)")
        print("    Output: Bob's regular Taproot address")
        print("    → Ordinary Taproot payment, completely unlinkable to Bob's SP address")
    else:
        print()
        print("  To build a real spend, re-run with:")
        print(f"    python3 {sys.argv[0]} --sp-txid <txid> --sp-vout <n> --sp-amount <sats>")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
