#!/usr/bin/env python3
"""
Chapter 11 — Taproot Lightning Channel: MuSig2 Funding + Cooperative Close

Real MuSig2 (BIP-327): Alice and Bob aggregate their public keys into one,
then cooperatively sign with partial signatures aggregated into a single
64-byte Schnorr signature. No faking — both private keys participate.

Flow:
  1. MuSig2 KeyAgg: aggregate Alice + Bob pubkeys (with BIP-327 coefficients)
  2. BIP86 tweak: compute Taproot output key (no script tree)
  3. Fund it (you send testnet coins to this address)
  4. MuSig2 Sign: both parties generate nonces, partial-sign, aggregate
  5. Broadcast cooperative close with single Schnorr signature

What the chain sees:
  Funding:  OP_1 <32-byte-key> → observer sees ordinary Taproot address
  Closing:  witness = [64-byte schnorr signature] → observer sees ordinary payment

Uses the BIP-327 reference implementation (musig2_ref.py) for the full
MuSig2 protocol: KeyAgg → NonceGen → NonceAgg → Sign → SigAgg.

Usage:
  python3 02_taproot_funding_and_close.py
  python3 02_taproot_funding_and_close.py --fund-txid <txid> --fund-vout <n> --fund-amount <sats>
"""

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, PublicKey
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
import musig2_ref as mu
import argparse
import hashlib
import struct
import sys

setup('testnet')

# ===== Same keys used throughout the book =====
ALICE_WIF = 'cRxebG1hY6vVgS9CSLNaEbEJaXkpZvc6nFeqqGT7v6gcW7MbzKNT'
BOB_WIF   = 'cSNdLFDf3wjx1rswNL2jKykbVkC6o56o5nYZi4FUkWKjFn2Q5DSG'

alice_priv = PrivateKey(ALICE_WIF)
bob_priv   = PrivateKey(BOB_WIF)
alice_pub  = alice_priv.get_public_key()
bob_pub    = bob_priv.get_public_key()


def wif_to_secret_bytes(wif_key: PrivateKey) -> bytes:
    """Extract 32-byte secret from a bitcoinutils PrivateKey."""
    # PrivateKey.to_bytes() returns the raw secret
    hex_str = wif_key.to_bytes().hex()
    return bytes.fromhex(hex_str)


def pubkey_to_plain(pub: PublicKey) -> bytes:
    """Convert bitcoinutils PublicKey to 33-byte compressed format."""
    return bytes.fromhex(pub.to_hex())


def bip86_tweak(xonly_agg: bytes) -> bytes:
    """Compute BIP-86 taptweak: t = TaggedHash('TapTweak', xonly_pubkey).
    BIP-86 means no script tree — tweak uses only the internal key."""
    tag = b'TapTweak'
    tag_hash = hashlib.sha256(tag).digest()
    return hashlib.sha256(tag_hash + tag_hash + xonly_agg).digest()


def build_funding():
    """MuSig2 KeyAgg + BIP86 tweak → Taproot funding address."""
    # Alice and Bob's compressed public keys (33 bytes each)
    pk_alice = pubkey_to_plain(alice_pub)
    pk_bob = pubkey_to_plain(bob_pub)

    # MuSig2 KeyAgg (BIP-327): deterministic aggregation with coefficients
    agg_ctx = mu.key_agg([pk_alice, pk_bob])
    xonly_agg = mu.get_xonly_pk(agg_ctx)

    # BIP-86 tweak (no script tree)
    tweak = bip86_tweak(xonly_agg)
    agg_ctx_tweaked = mu.apply_tweak(agg_ctx, tweak, is_xonly=True)
    xonly_output = mu.get_xonly_pk(agg_ctx_tweaked)

    # Convert to bech32m address
    funding_pub = PublicKey("02" + xonly_output.hex())
    funding_addr = funding_pub.get_taproot_address()

    print("=" * 70)
    print("Taproot Lightning Channel Funding (MuSig2 + BIP86)")
    print("=" * 70)
    print(f"Alice pubkey:     {pk_alice.hex()}")
    print(f"Bob pubkey:       {pk_bob.hex()}")
    print(f"Aggregated (x):   {xonly_agg.hex()}")
    print(f"BIP86 tweak:      {tweak.hex()}")
    print(f"Output key (x):   {xonly_output.hex()}")
    print()
    print(f"Funding Address (P2TR): {funding_addr.to_string()}")
    print(f"ScriptPubKey: {funding_addr.to_script_pub_key().to_hex()}")
    print(f"Format: OP_1 <32-byte-output-key>")
    print(f"Script tree: None (BIP86 — provably no hidden scripts)")
    print()
    print("On-chain visibility:")
    print("  Observer sees: OP_1 + 32-byte public key")
    print("  Observer knows: This is a Taproot address")
    print("  Observer CANNOT tell: Is it a channel? Multisig? Regular wallet?")
    print()

    return agg_ctx_tweaked, funding_addr


def build_sighash(funding_addr, fund_txid, fund_vout, fund_amount_sats):
    """Build the close transaction and compute its sighash."""
    fee = 154
    alice_amount = fund_amount_sats * 6 // 10
    bob_amount = fund_amount_sats - alice_amount - fee

    tx = Transaction(
        [TxInput(fund_txid, fund_vout)],
        [
            TxOutput(alice_amount, alice_pub.get_taproot_address().to_script_pub_key()),
            TxOutput(bob_amount, bob_pub.get_taproot_address().to_script_pub_key()),
        ],
        has_segwit=True
    )

    # Compute BIP-341 sighash for taproot key-path spend (SIGHASH_DEFAULT = 0x00)
    # bitcoinutils expects Script objects, not raw bytes
    scriptpubkeys = [funding_addr.to_script_pub_key()]
    amounts = [fund_amount_sats]

    sighash = tx.get_transaction_taproot_digest(
        0, scriptpubkeys, amounts, 0, sighash=0x00
    )

    return tx, sighash, alice_amount, bob_amount, fee


def musig2_sign(agg_ctx_tweaked, sighash_bytes):
    """Full MuSig2 signing: NonceGen → NonceAgg → PartialSign → SigAgg.

    Both Alice and Bob participate. This is the real BIP-327 protocol,
    not a simplification.

    The BIP86 tweak is passed into SessionContext so the signing accounts
    for the tweaked output key (not just the raw aggregate key).
    """
    sk_alice = wif_to_secret_bytes(alice_priv)
    sk_bob = wif_to_secret_bytes(bob_priv)
    pk_alice = pubkey_to_plain(alice_pub)
    pk_bob = pubkey_to_plain(bob_pub)

    pubkeys = [pk_alice, pk_bob]

    # The on-chain key has TWO BIP86 tweaks:
    #   1. MuSig2 BIP86 tweak on aggregate key: t1 = HashTapTweak(agg_xonly)
    #   2. bitcoinutils BIP86 tweak on already-tweaked key: t2 = HashTapTweak(tweaked_xonly)
    # Both must be passed to SessionContext for the signature to be valid.
    agg_ctx_raw = mu.key_agg(pubkeys)
    xonly_raw = mu.get_xonly_pk(agg_ctx_raw)
    tweak1 = bip86_tweak(xonly_raw)

    # After first tweak
    agg_ctx_t1 = mu.apply_tweak(agg_ctx_raw, tweak1, is_xonly=True)
    xonly_after_t1 = mu.get_xonly_pk(agg_ctx_t1)

    # Second tweak (applied by get_taproot_address)
    tweak2 = bip86_tweak(xonly_after_t1)

    # Final output key (matches on-chain)
    agg_ctx_t2 = mu.apply_tweak(agg_ctx_t1, tweak2, is_xonly=True)
    xonly_output = mu.get_xonly_pk(agg_ctx_t2)
    msg = sighash_bytes

    # Round 1: Both parties generate secret nonces + public nonces
    nonce_alice = mu.nonce_gen_internal(
        rand_=bytes(32),
        sk=sk_alice,
        pk=pk_alice,
        aggpk=xonly_output,
        msg=msg,
        extra_in=None
    )
    nonce_bob = mu.nonce_gen_internal(
        rand_=bytes([1] * 32),
        sk=sk_bob,
        pk=pk_bob,
        aggpk=xonly_output,
        msg=msg,
        extra_in=None
    )

    pubnonce_alice = nonce_alice[1]
    pubnonce_bob = nonce_bob[1]
    secnonce_alice = nonce_alice[0]
    secnonce_bob = nonce_bob[0]

    # Round 2: Aggregate nonces
    aggnonce = mu.nonce_agg([pubnonce_alice, pubnonce_bob])

    # Round 3: Each party creates a partial signature
    # Pass BOTH BIP86 tweaks so signing produces a valid sig for the double-tweaked key
    session_ctx = mu.SessionContext(
        aggnonce, pubkeys,
        [tweak1, tweak2],   # both tweaks
        [True, True],       # both are x-only tweaks
        msg
    )

    psig_alice = mu.sign(secnonce_alice, sk_alice, session_ctx)
    psig_bob = mu.sign(secnonce_bob, sk_bob, session_ctx)

    print(f"  Alice partial sig: {psig_alice.hex()[:32]}...")
    print(f"  Bob partial sig:   {psig_bob.hex()[:32]}...")

    # Round 4: Aggregate partial signatures
    final_sig = mu.partial_sig_agg([psig_alice, psig_bob], session_ctx)

    print(f"  Aggregated sig:    {final_sig.hex()[:32]}...")
    print(f"  Signature length:  {len(final_sig)} bytes")

    # Verify against the tweaked output key
    assert mu.schnorr_verify(msg, xonly_output, final_sig), "Signature verification failed!"
    print(f"  Verification:      PASSED (against tweaked output key)")

    return final_sig


def build_cooperative_close(agg_ctx_tweaked, funding_addr, fund_txid, fund_vout, fund_amount_sats):
    """Build close tx, sign with MuSig2, produce broadcastable raw hex."""
    print("=" * 70)
    print("Taproot Cooperative Close (MuSig2)")
    print("=" * 70)

    tx, sighash, alice_amount, bob_amount, fee = build_sighash(
        funding_addr, fund_txid, fund_vout, fund_amount_sats
    )

    print(f"Spending: {fund_txid}:{fund_vout} ({fund_amount_sats} sats)")
    print(f"  → Alice: {alice_amount} sats")
    print(f"  → Bob:   {bob_amount} sats")
    print(f"  → Fee:   {fee} sats")
    print(f"  Sighash: {sighash.hex()}")
    print()
    print("MuSig2 signing (BIP-327):")

    sig = musig2_sign(agg_ctx_tweaked, sighash)

    # Attach witness
    tx.witnesses.append(TxWitnessInput([sig.hex()]))

    signed_hex = tx.serialize()

    print()
    print(f"Witness structure:")
    print(f"  [0] Schnorr signature (64 bytes) — MuSig2 aggregated")
    print(f"  Total witness: 64 bytes")
    print()
    print("On-chain visibility:")
    print("  Observer sees: one 64-byte Schnorr signature")
    print("  Observer concludes: ordinary Taproot payment")
    print("  Observer CANNOT tell: this was a 2-party MuSig2 channel close")
    print()
    print(f"txid: {tx.get_txid()}")
    print(f"Raw hex ({len(signed_hex) // 2} bytes):")
    print(signed_hex)
    print()
    print(f"Broadcast: bitcoin-cli -testnet sendrawtransaction {signed_hex[:60]}...")

    return tx


def main():
    p = argparse.ArgumentParser(description="Taproot MuSig2 channel funding + cooperative close")
    p.add_argument("--fund-txid", default="", help="Funding UTXO txid")
    p.add_argument("--fund-vout", type=int, default=0, help="Funding UTXO vout")
    p.add_argument("--fund-amount", type=int, default=10000, help="Funding amount in sats")
    args = p.parse_args()

    agg_ctx_tweaked, funding_addr = build_funding()

    if args.fund_txid:
        build_cooperative_close(agg_ctx_tweaked, funding_addr,
                                args.fund_txid, args.fund_vout, args.fund_amount)
    else:
        print("Next step: send testnet coins to the Taproot address above, then re-run:")
        print(f"  python3 {sys.argv[0]} --fund-txid <txid> --fund-vout <n> --fund-amount <sats>")


if __name__ == "__main__":
    main()
