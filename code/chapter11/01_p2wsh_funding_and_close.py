#!/usr/bin/env python3
"""
Chapter 11 — Traditional Lightning Channel: P2WSH 2-of-2 Funding + Cooperative Close

Demonstrates the P2WSH approach to Lightning channel funding and closing.
Uses the same Alice/Bob keys as previous chapters.

Flow:
  1. Build 2-of-2 multisig witness script
  2. Derive P2WSH funding address
  3. Fund it (you send testnet coins to this address)
  4. Build cooperative close transaction (both sign)
  5. Print raw hex for broadcast

What the chain sees:
  Funding:  OP_0 <32-byte-hash> → observer knows it's P2WSH
  Closing:  witness = [empty, sig_alice, sig_bob, 2-of-2 script] → observer knows it's multisig

Usage:
  python3 01_p2wsh_funding_and_close.py
  python3 01_p2wsh_funding_and_close.py --fund-txid <txid> --fund-vout <n> --fund-amount <sats>
"""

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, PublicKey, P2wshAddress
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.utils import to_satoshis
import argparse
import sys

setup('testnet')

# ===== Same keys used throughout the book =====
ALICE_WIF = 'cRxebG1hY6vVgS9CSLNaEbEJaXkpZvc6nFeqqGT7v6gcW7MbzKNT'
BOB_WIF   = 'cSNdLFDf3wjx1rswNL2jKykbVkC6o56o5nYZi4FUkWKjFn2Q5DSG'

alice_priv = PrivateKey(ALICE_WIF)
bob_priv   = PrivateKey(BOB_WIF)
alice_pub  = alice_priv.get_public_key()
bob_pub    = bob_priv.get_public_key()


def build_funding():
    """Build P2WSH 2-of-2 multisig funding address."""
    # BIP67: sort pubkeys lexicographically for deterministic multisig
    pubs = sorted([alice_pub.to_hex(), bob_pub.to_hex()])

    witness_script = Script([
        'OP_2', pubs[0], pubs[1], 'OP_2', 'OP_CHECKMULTISIG'
    ])

    p2wsh_addr = P2wshAddress.from_script(witness_script)

    print("=" * 70)
    print("P2WSH 2-of-2 Lightning Channel Funding")
    print("=" * 70)
    print(f"Alice pubkey: {alice_pub.to_hex()}")
    print(f"Bob pubkey:   {bob_pub.to_hex()}")
    print()
    print(f"Witness Script (hex): {witness_script.to_hex()}")
    print(f"Witness Script size:  {len(bytes.fromhex(witness_script.to_hex()))} bytes")
    print()
    print(f"Funding Address (P2WSH): {p2wsh_addr.to_string()}")
    print(f"ScriptPubKey: {p2wsh_addr.to_script_pub_key().to_hex()}")
    print(f"Format: OP_0 <32-byte SHA256(witness_script)>")
    print()
    print("On-chain visibility:")
    print("  Observer sees: OP_0 + 32-byte hash")
    print("  Observer knows: This is a P2WSH output (likely multisig or channel)")
    print()

    return witness_script, p2wsh_addr


def build_cooperative_close(witness_script, p2wsh_addr, fund_txid, fund_vout, fund_amount_sats):
    """Build and sign a cooperative close transaction."""
    fee = 300  # sats
    alice_amount = fund_amount_sats * 6 // 10        # 60% to Alice
    bob_amount = fund_amount_sats - alice_amount - fee  # rest to Bob

    # Close transaction: spend funding output, distribute to both parties
    tx = Transaction(
        [TxInput(fund_txid, fund_vout)],
        [
            TxOutput(alice_amount, alice_pub.get_segwit_address().to_script_pub_key()),
            TxOutput(bob_amount, bob_pub.get_segwit_address().to_script_pub_key()),
        ],
        has_segwit=True
    )

    # Both parties sign
    alice_sig = alice_priv.sign_segwit_input(
        tx, 0, witness_script, fund_amount_sats
    )
    bob_sig = bob_priv.sign_segwit_input(
        tx, 0, witness_script, fund_amount_sats
    )

    # P2WSH witness: [empty, sig_alice, sig_bob, witness_script]
    # The empty element is required by the legacy OP_CHECKMULTISIG bug
    tx.witnesses.append(TxWitnessInput([
        '', alice_sig, bob_sig, witness_script.to_hex()
    ]))

    signed_hex = tx.serialize()

    print("=" * 70)
    print("P2WSH Cooperative Close")
    print("=" * 70)
    print(f"Spending: {fund_txid}:{fund_vout} ({fund_amount_sats} sats)")
    print(f"  → Alice: {alice_amount} sats")
    print(f"  → Bob:   {bob_amount} sats")
    print(f"  → Fee:   {fee} sats")
    print()
    print(f"Witness structure:")
    print(f"  [0] empty (CHECKMULTISIG bug)")
    print(f"  [1] Alice signature ({len(alice_sig) // 2} bytes, DER)")
    print(f"  [2] Bob signature   ({len(bob_sig) // 2} bytes, DER)")
    print(f"  [3] Witness script  ({len(witness_script.to_hex()) // 2} bytes)")
    print(f"  Total witness: ~{len(alice_sig)//2 + len(bob_sig)//2 + len(witness_script.to_hex())//2 + 1} bytes")
    print()
    print("On-chain visibility:")
    print("  Observer sees: 2-of-2 multisig script + two signatures")
    print("  Observer knows: This is a Lightning channel cooperative close")
    print()
    print(f"txid: {tx.get_txid()}")
    print(f"Raw hex ({len(signed_hex) // 2} bytes):")
    print(signed_hex)
    print()
    print(f"Broadcast: bitcoin-cli -testnet sendrawtransaction {signed_hex[:60]}...")

    return tx


def main():
    p = argparse.ArgumentParser(description="P2WSH Lightning channel funding + cooperative close")
    p.add_argument("--fund-txid", default="", help="Funding UTXO txid (if already funded)")
    p.add_argument("--fund-vout", type=int, default=0, help="Funding UTXO vout")
    p.add_argument("--fund-amount", type=int, default=100000, help="Funding amount in sats")
    args = p.parse_args()

    witness_script, p2wsh_addr = build_funding()

    if args.fund_txid:
        print("Send testnet coins to the funding address above, then re-run with --fund-txid.\n")
        build_cooperative_close(witness_script, p2wsh_addr,
                                args.fund_txid, args.fund_vout, args.fund_amount)
    else:
        print("Next step: send testnet coins to the P2WSH address above, then re-run:")
        print(f"  python3 {sys.argv[0]} --fund-txid <txid> --fund-vout <n> --fund-amount <sats>")


if __name__ == "__main__":
    main()
