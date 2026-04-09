#!/usr/bin/env python3
"""
Chapter 10 — Tapret leaf construction (no dependencies required).

Builds the 64-byte Tapret unspendable leaf that RGB inserts into
the Taproot script tree at depth 1. Prints the byte-by-byte structure
and shows how it changes the output key via HashTapTweak.

No rgb CLI, no bitcoinutils, no pip. Python 3.9+ stdlib only.

The leaf structure (current RGB implementation, rgb-wallet 0.11.0-beta.9):
  29 bytes  OP_RESERVED (0x50) × 29
   1 byte   OP_RETURN  (0x6A)
   1 byte   OP_PUSHBYTES_33 (0x21)
  32 bytes  MPC commitment
   1 byte   nonce
  ─────────────────────────────────
  64 bytes  total  (leaf version 0xC0)

Usage:
  python3 03_tapret_leaf.py
  python3 03_tapret_leaf.py --commitment <64-hex-bytes> --nonce <0-255>
"""

from __future__ import annotations

import argparse
import hashlib
import os

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

LEAF_VERSION = 0xC0          # Tapscript leaf version (BIP-341)
OP_RESERVED  = 0x50          # "unspendable" filler
OP_RETURN    = 0x6A
OP_PUSH33    = 0x21          # OP_PUSHBYTES_33


# ---------------------------------------------------------------------------
# tagged hash (BIP-340 / BIP-341)
# ---------------------------------------------------------------------------

def tagged_hash(tag: str, data: bytes) -> bytes:
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


# ---------------------------------------------------------------------------
# Tapret leaf
# ---------------------------------------------------------------------------

def build_tapret_leaf(mpc_commitment: bytes, nonce: int) -> bytes:
    """
    Construct the 64-byte Tapret leaf script.

    Layout:
      [0:29]   29 × OP_RESERVED  (0x50)
      [29]     OP_RETURN          (0x6A)
      [30]     OP_PUSHBYTES_33    (0x21)
      [31:63]  32-byte MPC commitment
      [63]     1-byte nonce
    """
    assert len(mpc_commitment) == 32, "MPC commitment must be 32 bytes"
    assert 0 <= nonce <= 255,         "nonce must be 0–255"

    leaf = (
        bytes([OP_RESERVED] * 29) +
        bytes([OP_RETURN]) +
        bytes([OP_PUSH33]) +
        mpc_commitment +
        bytes([nonce])
    )
    assert len(leaf) == 64
    return leaf


def tapleaf_hash(leaf_script: bytes) -> bytes:
    """BIP-341 TapLeaf hash: tagged_hash('TapLeaf', version || compact_size || script)."""
    # compact_size for 64 bytes = 0x40
    data = bytes([LEAF_VERSION, 0x40]) + leaf_script
    return tagged_hash("TapLeaf", data)


def taptweak(internal_key_xonly: bytes, merkle_root: bytes) -> bytes:
    """BIP-341 output key tweak."""
    return tagged_hash("TapTweak", internal_key_xonly + merkle_root)


# ---------------------------------------------------------------------------
# pretty printer
# ---------------------------------------------------------------------------

def print_leaf_structure(leaf: bytes, mpc_commitment: bytes, nonce: int) -> None:
    print("=" * 60)
    print("Tapret Leaf Structure (64 bytes, leaf version 0xC0)")
    print("=" * 60)
    print()

    sections = [
        (0,  29, f"OP_RESERVED × 29  (0x50 × 29)  — unspendable filler"),
        (29, 30, f"OP_RETURN          (0x6A)        — leaf is unspendable"),
        (30, 31, f"OP_PUSHBYTES_33    (0x21)        — push 33 bytes"),
        (31, 63, f"MPC commitment     (32 bytes)    — RGB state anchor"),
        (63, 64, f"nonce              ({nonce})            — collision avoidance"),
    ]

    for start, end, label in sections:
        chunk = leaf[start:end].hex()
        if len(chunk) > 32:
            chunk = chunk[:32] + "..."
        print(f"  [{start:2d}:{end:2d}]  {chunk:<36s}  {label}")

    print()
    print(f"  Full hex:")
    print(f"  {leaf[:32].hex()}")
    print(f"  {leaf[32:].hex()}")
    print()


def print_tweak_derivation(internal_key: bytes, leaf: bytes) -> None:
    leaf_hash   = tapleaf_hash(leaf)
    merkle_root = leaf_hash          # single-leaf tree: root = leaf hash
    tweak       = taptweak(internal_key, merkle_root)

    print("=" * 60)
    print("Output Key Derivation (single Tapret leaf)")
    print("=" * 60)
    print()
    print(f"  internal key (x-only):  {internal_key.hex()}")
    print()
    print(f"  TapLeaf hash:           {leaf_hash.hex()}")
    print(f"  (= merkle root for single-leaf tree)")
    print()
    print(f"  TapTweak input:         internal_key || merkle_root")
    print(f"  tweak t:                {tweak.hex()}")
    print()
    print(f"  output key Q = internal_key + t·G")
    print(f"  (same formula as Ch5: P' = P + t·G,")
    print(f"   but t now encodes an RGB state commitment)")
    print()
    print(f"  On-chain: OP_1 <Q_xonly>   — indistinguishable from any P2TR output")
    print()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Build and inspect a Tapret leaf (no dependencies)"
    )
    p.add_argument(
        "--commitment",
        default=None,
        help="32-byte MPC commitment as hex (default: random)"
    )
    p.add_argument(
        "--nonce",
        type=int,
        default=0,
        help="1-byte nonce 0-255 (default: 0)"
    )
    p.add_argument(
        "--internal-key",
        default="50be5fc44ec580c387bf45df275aaa8b27e2d7716af31f10eeed357d126bb4d3",
        help="32-byte x-only internal pubkey as hex (default: Alice's key from the book)"
    )
    args = p.parse_args()

    # MPC commitment: use provided or random
    if args.commitment:
        mpc = bytes.fromhex(args.commitment)
        assert len(mpc) == 32, "--commitment must be 32 bytes (64 hex chars)"
    else:
        mpc = os.urandom(32)
        print(f"MPC commitment (random): {mpc.hex()}")
        print()

    internal_key = bytes.fromhex(args.internal_key)
    assert len(internal_key) == 32

    leaf = build_tapret_leaf(mpc, args.nonce)

    print_leaf_structure(leaf, mpc, args.nonce)
    print_tweak_derivation(internal_key, leaf)

    print("=" * 60)
    print("Key properties")
    print("=" * 60)
    print()
    print("  - Leaf is UNSPENDABLE: OP_RETURN in script body")
    print("  - Leaf is INVISIBLE:   it lives in the script tree,")
    print("    not as a transaction output")
    print("  - Output key is INDISTINGUISHABLE from any other P2TR key")
    print("  - Only a party with the consignment can find and")
    print("    verify the MPC commitment")
    print()


if __name__ == "__main__":
    main()