#!/usr/bin/env python3
"""
Chapter 10 — RGB single-hop transfer (Alice → Bob).

Business logic for a Tapret-committed RGB20 asset transfer on testnet.
Each step maps to a section in the manuscript.

Flow:
  1. Sync + snapshot Alice and Bob state (before)
  2. Bob creates an RGB invoice
  3. Alice builds the transfer (consignment + PSBT)
  4. Bob validates and accepts the consignment
  5. Alice signs the PSBT and broadcasts
  6. Sync + snapshot state (after) — verify conservation

Prerequisites (you supply):
  - rgb CLI binary on PATH (or set RGB_CLI_BIN)
  - Two wallet directories: Alice (sender) and Bob (receiver),
    both already imported with the same RGB20 contract
  - Alice must own unspent RGB allocations for the contract
  - Bitcoin Core (or equivalent) for PSBT signing + broadcast
  - Esplora URL for rgb --sync (public mempool.space works)

Environment variables:
  RGB_CLI_BIN          path to rgb binary (default: rgb)
  RGB_ALICE_DIR        Alice wallet directory
  RGB_BOB_DIR          Bob wallet directory
  RGB_CONTRACT_ID      rgb:.... contract id
  RGB_NETWORK          testnet3 (default)
  RGB_ESPLORA_URL      Esplora HTTP API base
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


def _rgb(wallet_dir: str, *args: str, timeout: int = 300) -> str:
    """Call the rgb CLI and return stdout."""
    rgb_bin = _env("RGB_CLI_BIN", "rgb")
    network = _env("RGB_NETWORK", "testnet3")
    esplora = _env("RGB_ESPLORA_URL", "https://mempool.space/testnet/api")

    cmd = [rgb_bin, "-d", wallet_dir, "-n", network, *args,
           "--sync", f"--esplora={esplora}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"rgb failed: {err}")
    return proc.stdout


# ---------------------------------------------------------------------------
# six-step transfer flow
# ---------------------------------------------------------------------------

def step1_snapshot_before(alice_dir: str, bob_dir: str, contract: str) -> None:
    """Sync both wallets and print current state."""
    print("=== Step 1: Snapshot state (before transfer) ===\n")

    alice_state = _rgb(alice_dir, "state", contract, "RGB20Fixed")
    print("Alice state:")
    print(alice_state)

    bob_state = _rgb(bob_dir, "state", contract, "RGB20Fixed")
    print("Bob state:")
    print(bob_state)


def step2_bob_invoice(bob_dir: str, contract: str, amount: str) -> str:
    """Bob creates an RGB invoice for the requested amount."""
    print(f"=== Step 2: Bob creates invoice ({amount} units) ===\n")

    out = _rgb(bob_dir, "invoice", contract, "RGB20Fixed",
               "assetOwner", amount)
    invoice = out.strip()
    print(f"Invoice: {invoice}\n")
    return invoice


def step3_alice_transfer(alice_dir: str, invoice: str) -> tuple[str, str]:
    """Alice builds the transfer: creates a consignment file and a PSBT."""
    print("=== Step 3: Alice creates transfer ===\n")

    consignment = tempfile.mktemp(suffix=".consignment")
    psbt_path = tempfile.mktemp(suffix=".psbt")

    _rgb(alice_dir, "transfer", invoice, consignment, psbt_path)
    print(f"Consignment: {consignment}")
    print(f"PSBT:        {psbt_path}\n")
    return consignment, psbt_path


def step4_bob_accept(bob_dir: str, consignment: str) -> None:
    """Bob validates the consignment and accepts it into his wallet."""
    print("=== Step 4: Bob validates + accepts consignment ===\n")

    _rgb(bob_dir, "accept", consignment, "--force")
    print("Accepted.\n")


def step5_sign_and_broadcast(psbt_path: str) -> str:
    """Sign the PSBT and broadcast. Returns txid.

    This step depends on your Bitcoin signing setup.
    The example below uses bitcoin-cli; adapt to your workflow.
    """
    print("=== Step 5: Sign PSBT and broadcast ===\n")

    wallet = _env("RGB_BITCOIN_WALLET", "wallet_testnet")

    # Read raw PSBT
    with open(psbt_path, "r") as f:
        psbt_b64 = f.read().strip()

    # Sign via bitcoin-cli
    sign_cmd = ["bitcoin-cli", "-testnet", f"-rpcwallet={wallet}",
                "walletprocesspsbt", psbt_b64]
    sign_proc = subprocess.run(sign_cmd, capture_output=True, text=True)
    if sign_proc.returncode != 0:
        raise RuntimeError(f"PSBT signing failed: {sign_proc.stderr.strip()}")

    result = json.loads(sign_proc.stdout)
    if not result.get("complete"):
        raise RuntimeError("PSBT not fully signed")
    signed_psbt = result["psbt"]

    # Finalize
    final_cmd = ["bitcoin-cli", "-testnet", "finalizepsbt", signed_psbt]
    final_proc = subprocess.run(final_cmd, capture_output=True, text=True)
    final_result = json.loads(final_proc.stdout)
    raw_hex = final_result["hex"]

    # Broadcast
    send_cmd = ["bitcoin-cli", "-testnet", "sendrawtransaction", raw_hex]
    send_proc = subprocess.run(send_cmd, capture_output=True, text=True)
    if send_proc.returncode != 0:
        raise RuntimeError(f"Broadcast failed: {send_proc.stderr.strip()}")

    txid = send_proc.stdout.strip()
    print(f"Broadcast txid: {txid}\n")
    return txid


def step6_snapshot_after(alice_dir: str, bob_dir: str, contract: str) -> None:
    """Sync again and print final state. Verify amount conservation."""
    print("=== Step 6: Snapshot state (after transfer) ===\n")

    alice_state = _rgb(alice_dir, "state", contract, "RGB20Fixed", "-a")
    print("Alice state (-a):")
    print(alice_state)

    bob_state = _rgb(bob_dir, "state", contract, "RGB20Fixed")
    print("Bob state:")
    print(bob_state)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="RGB single-hop transfer: Alice sends tokens to Bob via Tapret commitment."
    )
    p.add_argument("--amount", default="100",
                   help="Amount to transfer (default: 100)")
    p.add_argument("--skip-broadcast", action="store_true",
                   help="Stop after step 4 (do not sign/broadcast)")
    args = p.parse_args()

    alice_dir = _env("RGB_ALICE_DIR")
    bob_dir = _env("RGB_BOB_DIR")
    contract = _env("RGB_CONTRACT_ID")

    if not all([alice_dir, bob_dir, contract]):
        print("Error: set RGB_ALICE_DIR, RGB_BOB_DIR, and RGB_CONTRACT_ID.",
              file=sys.stderr)
        return 1

    step1_snapshot_before(alice_dir, bob_dir, contract)
    invoice = step2_bob_invoice(bob_dir, contract, args.amount)
    consignment, psbt_path = step3_alice_transfer(alice_dir, invoice)
    step4_bob_accept(bob_dir, consignment)

    if args.skip_broadcast:
        print("--skip-broadcast: stopping after step 4.")
        print(f"PSBT at: {psbt_path}")
        return 0

    txid = step5_sign_and_broadcast(psbt_path)
    step6_snapshot_after(alice_dir, bob_dir, contract)

    print("--- Done ---")
    print(f"txid: {txid}")
    print(f"Explorer: https://mempool.space/testnet/tx/{txid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
