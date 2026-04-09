#!/usr/bin/env python3
"""
Chapter 11 — Side-by-side comparison: P2WSH vs Taproot channel witness

Builds both funding + close transactions in memory (no broadcast needed)
and prints a direct comparison of witness size, structure, and privacy.

This is the key visual for the chapter: same channel, same parties,
same balances — completely different on-chain footprint.

Usage:
  python3 03_compare_witness.py
"""

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, PublicKey, P2wshAddress
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput

setup('testnet')

# Same keys as the whole book
ALICE_WIF = 'cRxebG1hY6vVgS9CSLNaEbEJaXkpZvc6nFeqqGT7v6gcW7MbzKNT'
BOB_WIF   = 'cSNdLFDf3wjx1rswNL2jKykbVkC6o56o5nYZi4FUkWKjFn2Q5DSG'

alice_priv = PrivateKey(ALICE_WIF)
bob_priv   = PrivateKey(BOB_WIF)
alice_pub  = alice_priv.get_public_key()
bob_pub    = bob_priv.get_public_key()

# Dummy funding txid (same for both, so comparison is fair)
FUND_TXID = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
FUND_AMOUNT = 100000  # sats
FEE = 300


def build_p2wsh_close():
    """Build P2WSH cooperative close and return witness details."""
    pubs = sorted([alice_pub.to_hex(), bob_pub.to_hex()])
    witness_script = Script(['OP_2', pubs[0], pubs[1], 'OP_2', 'OP_CHECKMULTISIG'])
    p2wsh_addr = P2wshAddress.from_script(witness_script)

    alice_amount = FUND_AMOUNT * 6 // 10
    bob_amount = FUND_AMOUNT - alice_amount - FEE

    tx = Transaction(
        [TxInput(FUND_TXID, 0)],
        [
            TxOutput(alice_amount, alice_pub.get_segwit_address().to_script_pub_key()),
            TxOutput(bob_amount, bob_pub.get_segwit_address().to_script_pub_key()),
        ],
        has_segwit=True
    )

    alice_sig = alice_priv.sign_segwit_input(tx, 0, witness_script, FUND_AMOUNT)
    bob_sig = bob_priv.sign_segwit_input(tx, 0, witness_script, FUND_AMOUNT)

    tx.witnesses.append(TxWitnessInput(['', alice_sig, bob_sig, witness_script.to_hex()]))

    sig_a_bytes = len(alice_sig) // 2
    sig_b_bytes = len(bob_sig) // 2
    script_bytes = len(witness_script.to_hex()) // 2
    witness_bytes = 1 + sig_a_bytes + sig_b_bytes + script_bytes  # +1 for empty element

    return {
        "funding_spk": p2wsh_addr.to_script_pub_key().to_hex(),
        "funding_addr": p2wsh_addr.to_string(),
        "witness_elements": 4,
        "signatures": 2,
        "sig_format": "DER (variable, ~71-72 bytes each)",
        "script_exposed": f"Yes — 2-of-2 multisig ({script_bytes} bytes)",
        "witness_bytes": witness_bytes,
        "tx_vsize": tx.get_vsize(),
        "tx_hex": tx.serialize(),
        "identifiable_as_channel": "Yes — 2-of-2 multisig is a Lightning signature",
    }


def build_taproot_close():
    """Build Taproot cooperative close and return witness details."""
    # Use Alice's key as simplified aggregate key
    funding_addr = alice_pub.get_taproot_address()

    alice_amount = FUND_AMOUNT * 6 // 10
    bob_amount = FUND_AMOUNT - alice_amount - FEE

    tx = Transaction(
        [TxInput(FUND_TXID, 0)],
        [
            TxOutput(alice_amount, alice_pub.get_taproot_address().to_script_pub_key()),
            TxOutput(bob_amount, bob_pub.get_taproot_address().to_script_pub_key()),
        ],
        has_segwit=True
    )

    sig = alice_priv.sign_taproot_input(
        tx, 0,
        [funding_addr.to_script_pub_key()],
        [FUND_AMOUNT],
        script_path=False
    )

    tx.witnesses.append(TxWitnessInput([sig]))

    return {
        "funding_spk": funding_addr.to_script_pub_key().to_hex(),
        "funding_addr": funding_addr.to_string(),
        "witness_elements": 1,
        "signatures": 1,
        "sig_format": "Schnorr (fixed 64 bytes)",
        "script_exposed": "No — key path only, no script revealed",
        "witness_bytes": 64,
        "tx_vsize": tx.get_vsize(),
        "tx_hex": tx.serialize(),
        "identifiable_as_channel": "No — identical to any Taproot payment",
    }


def main():
    p2wsh = build_p2wsh_close()
    taproot = build_taproot_close()

    print("=" * 70)
    print("  P2WSH vs Taproot: Lightning Channel Cooperative Close")
    print("=" * 70)

    print("\n--- Funding Output ---\n")
    print(f"  {'':30s} {'P2WSH':25s} {'Taproot':25s}")
    print(f"  {'Address prefix':30s} {'tb1q... (bech32)':25s} {'tb1p... (bech32m)':25s}")
    print(f"  {'ScriptPubKey':30s} {'OP_0 <32-byte hash>':25s} {'OP_1 <32-byte key>':25s}")
    print(f"  {'SegWit version':30s} {'v0':25s} {'v1 (Taproot)':25s}")
    print(f"  {'Observer inference':30s} {'Likely multisig/channel':25s} {'Could be anything':25s}")

    print("\n--- Cooperative Close Witness ---\n")
    fields = [
        ("Witness elements", "witness_elements"),
        ("Signatures", "signatures"),
        ("Signature format", "sig_format"),
        ("Script exposed", "script_exposed"),
        ("Witness size", "witness_bytes"),
        ("Transaction vsize", "tx_vsize"),
        ("Identifiable as channel", "identifiable_as_channel"),
    ]
    for label, key in fields:
        v1 = p2wsh[key]
        v2 = taproot[key]
        if key in ("witness_bytes", "tx_vsize"):
            v1 = f"{v1} bytes"
            v2 = f"{v2} bytes"
        print(f"  {label:30s} {str(v1):25s} {str(v2):25s}")

    savings = (1 - taproot["witness_bytes"] / p2wsh["witness_bytes"]) * 100
    print(f"\n  Witness size savings: {savings:.0f}%")

    print("\n--- What Each Observer Concludes ---\n")
    print("  P2WSH close:")
    print("    'This is a 2-of-2 multisig. Probably a Lightning channel.'")
    print()
    print("  Taproot close:")
    print("    'This is an ordinary Taproot payment. Nothing unusual.'")
    print()
    print("  Same channel. Same parties. Same balances.")
    print("  Completely different on-chain footprint.")
    print()

    print("=" * 70)
    print("  Raw Transaction Comparison")
    print("=" * 70)
    print(f"\n  P2WSH  tx size: {len(p2wsh['tx_hex']) // 2} bytes, vsize: {p2wsh['tx_vsize']} vbytes")
    print(f"  Taproot tx size: {len(taproot['tx_hex']) // 2} bytes, vsize: {taproot['tx_vsize']} vbytes")


if __name__ == "__main__":
    main()
