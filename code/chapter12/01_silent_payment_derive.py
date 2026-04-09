#!/usr/bin/env python3
"""
Chapter 12 — Silent Payments: ECDH + One-Time Address Derivation

Complete flow:
  1. Bob generates Silent Payment keys (B_scan, B_spend)
  2. Alice uses her input key + Bob's SP address to derive a one-time P2TR address
  3. Bob independently derives the same address (verification)
  4. Bob computes the spending private key

Uses the same Alice/Bob keys as previous chapters.
All math is the same as Chapter 5's key tweaking: P = Q + t·G

Usage:
  python3 01_silent_payment_derive.py
"""

import hashlib
from coincurve import PrivateKey as CPrivateKey, PublicKey as CPublicKey

# ===== Curve order =====
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def tagged_hash(tag: str, data: bytes) -> bytes:
    """BIP340/BIP352 tagged hash."""
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


# =====================================================
# Step 1: Bob generates Silent Payment key pairs
# =====================================================
# In production: derived from BIP32 at m/352'/coin_type'/account'/...
# Here: deterministic from the book's Bob WIF for reproducibility

bob_scan_priv = CPrivateKey(hashlib.sha256(b"bob_scan_secret_mastering_taproot").digest())
bob_spend_priv = CPrivateKey(hashlib.sha256(b"bob_spend_secret_mastering_taproot").digest())
bob_scan_pub = bob_scan_priv.public_key
bob_spend_pub = bob_spend_priv.public_key

print("=" * 70)
print("Step 1: Bob's Silent Payment Keys")
print("=" * 70)
print(f"  b_scan (privkey):  {bob_scan_priv.secret.hex()}")
print(f"  B_scan (pubkey):   {bob_scan_pub.format().hex()}")
print(f"  b_spend (privkey): {bob_spend_priv.secret.hex()}")
print(f"  B_spend (pubkey):  {bob_spend_pub.format().hex()}")
print()
print(f"  Silent Payment address would encode: B_scan + B_spend")
print(f"  Format: sp1q<B_scan><B_spend>  (Bech32m, 117+ chars)")


# =====================================================
# Step 2: Alice derives one-time address (sender side)
# =====================================================
# Alice's input key — from the UTXO she's spending
# Using the book's Alice WIF
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey

setup('testnet')
alice_btc_priv = PrivateKey('cRxebG1hY6vVgS9CSLNaEbEJaXkpZvc6nFeqqGT7v6gcW7MbzKNT')

# Extract raw 32-byte secret for EC operations
alice_secret = bytes.fromhex(alice_btc_priv.to_bytes().hex())
alice_input_priv = CPrivateKey(alice_secret)
alice_input_pub = alice_input_priv.public_key

print()
print("=" * 70)
print("Step 2: Alice Derives One-Time Address (Sender Side)")
print("=" * 70)
print(f"  Alice input pubkey (A): {alice_input_pub.format().hex()}")

# 2a. ECDH: Alice computes shared_secret = a · B_scan
shared_secret_alice = bob_scan_pub.multiply(alice_input_priv.secret)
print(f"  ECDH shared secret:     {shared_secret_alice.format().hex()}")

# 2b. Derive tweak: t_k = TaggedHash("BIP0352/SharedSecret", shared_secret || k)
k = 0  # first output
t_k = tagged_hash(
    "BIP0352/SharedSecret",
    shared_secret_alice.format() + k.to_bytes(4, 'big')
)
print(f"  Tweak t_k:              {t_k.hex()}")

# 2c. One-time public key: P = B_spend + t_k · G
tweak_point = CPrivateKey(t_k).public_key
one_time_pubkey = CPublicKey.combine_keys([bob_spend_pub, tweak_point])

# x-only (strip prefix byte for Taproot)
x_only = one_time_pubkey.format(compressed=True)[1:]

print(f"  t_k · G:                {tweak_point.format().hex()}")
print(f"  P = B_spend + t_k·G:   {one_time_pubkey.format().hex()}")
print(f"  x-only (32 bytes):      {x_only.hex()}")

# 2d. Taproot address
from bitcoinutils.keys import PublicKey
one_time_btc_pub = PublicKey("02" + x_only.hex())
one_time_addr = one_time_btc_pub.get_taproot_address()

print()
print(f"  One-time Taproot address: {one_time_addr.to_string()}")
print(f"  ScriptPubKey: {one_time_addr.to_script_pub_key().to_hex()}")
print(f"  Format: OP_1 <32-byte-x-only-key>")
print(f"  Looks like: any ordinary Taproot address")


# =====================================================
# Step 3: Bob independently derives the same address
# =====================================================
print()
print("=" * 70)
print("Step 3: Bob Verifies (Receiver Side — Scanning)")
print("=" * 70)

# Bob computes: shared_secret = b_scan · A
shared_secret_bob = alice_input_pub.multiply(bob_scan_priv.secret)
print(f"  Bob's ECDH (b_scan · A): {shared_secret_bob.format().hex()}")
print(f"  Match with Alice:        {shared_secret_bob.format() == shared_secret_alice.format()}")

# Bob derives the same tweak and one-time pubkey
bob_t_k = tagged_hash(
    "BIP0352/SharedSecret",
    shared_secret_bob.format() + k.to_bytes(4, 'big')
)
bob_tweak_point = CPrivateKey(bob_t_k).public_key
bob_one_time_pubkey = CPublicKey.combine_keys([bob_spend_pub, bob_tweak_point])

print(f"  Bob derives P:           {bob_one_time_pubkey.format().hex()}")
print(f"  Match with Alice:        {bob_one_time_pubkey.format() == one_time_pubkey.format()}")


# =====================================================
# Step 4: Bob computes the spending private key
# =====================================================
print()
print("=" * 70)
print("Step 4: Bob's Spending Key")
print("=" * 70)

# p = b_spend + t_k  (mod n)
b_spend_int = int.from_bytes(bob_spend_priv.secret, 'big')
t_k_int = int.from_bytes(t_k, 'big')
one_time_privkey_int = (b_spend_int + t_k_int) % SECP256K1_ORDER
one_time_privkey_bytes = one_time_privkey_int.to_bytes(32, 'big')

# Verify
one_time_privkey = CPrivateKey(one_time_privkey_bytes)
derived_pub = one_time_privkey.public_key

print(f"  b_spend:                 {bob_spend_priv.secret.hex()}")
print(f"  t_k:                     {t_k.hex()}")
print(f"  p = b_spend + t_k:       {one_time_privkey_bytes.hex()}")
print(f"  p · G:                   {derived_pub.format().hex()}")
print(f"  Matches one-time P:      {derived_pub.format() == one_time_pubkey.format()}")
print()
print("  Mathematical proof:")
print("    P = B_spend + t_k·G")
print("    p = b_spend + t_k")
print("    p·G = (b_spend + t_k)·G = B_spend + t_k·G = P  ✓")
print()
print("  Same math as Taproot tweak (Chapter 5):")
print("    Taproot: output_key = internal_key + H(internal_key||merkle_root)·G")
print("    SP:      P          = B_spend      + H(shared_secret||k)·G")

# =====================================================
# Summary
# =====================================================
print()
print("=" * 70)
print("Summary")
print("=" * 70)
print(f"  Bob's Silent Payment pubkeys: B_scan + B_spend (published once)")
print(f"  Alice sends to: {one_time_addr.to_string()}")
print(f"  Chain observer sees: ordinary P2TR output, unlinkable to Bob")
print(f"  Bob scans chain: uses b_scan to recompute P, finds the match")
print(f"  Bob spends: uses p = b_spend + t_k as private key")
print()

# Export for use by 02_send_testnet.py
import json
result = {
    "one_time_address": one_time_addr.to_string(),
    "one_time_scriptpubkey": one_time_addr.to_script_pub_key().to_hex(),
    "one_time_x_only": x_only.hex(),
    "one_time_privkey": one_time_privkey_bytes.hex(),
    "bob_scan_pub": bob_scan_pub.format().hex(),
    "bob_spend_pub": bob_spend_pub.format().hex(),
    "alice_input_pub": alice_input_pub.format().hex(),
    "tweak": t_k.hex(),
}
with open("sp_derived.json", "w") as f:
    json.dump(result, f, indent=2)
print(f"  Saved derivation data to sp_derived.json")
