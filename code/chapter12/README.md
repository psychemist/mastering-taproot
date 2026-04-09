# Chapter 12 — Silent Payments: ECDH + One-Time Taproot Addresses

Alice pays to Bob's static Silent Payment address; the chain sees an ordinary P2TR transfer. Bob scans the chain with his scan key, finds the payment, and spends it — no coordination required.

## What this is / is not

- **Is:** A complete Silent Payment derivation, send, scan, and spend flow on **testnet**, demonstrating the ECDH shared secret, one-time address construction, and spending key recovery.
- **Is not:** A full BIP352 implementation with `A_sum` optimization, BIP158 light-client filtering, or multi-input aggregation. Alice's input pubkey is passed between scripts via JSON rather than parsed from the chain — a simplification for clarity (see note in `03`).

## Layout

| File | Role |
|------|------|
| `01_silent_payment_derive.py` | Bob generates SP keys; Alice derives one-time address via ECDH; Bob verifies; spending key computed. Writes `sp_derived.json`. |
| `02_send_testnet.py` | Alice builds a Taproot transaction sending to the one-time address. Reads `sp_derived.json`, writes `sp_send_result.json`. |
| `03_bob_scan_and_spend.py` | Bob scans (re-derives P from chain), matches output, computes spending key, signs a spend transaction. |

## Setup

```bash
cd code/chapter12
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Or reuse Chapter 11's venv (the symlink `venv -> ../chapter11/venv` works if Chapter 11 is already set up).

## Run

### Step 1: Derive the one-time address

```bash
python3 01_silent_payment_derive.py
```

Prints Bob's SP keys, ECDH shared secret, tweak, one-time pubkey, and Taproot address. Saves `sp_derived.json`.

### Step 2: Send testnet coins to the one-time address

```bash
python3 02_send_testnet.py --fund-txid <txid> --fund-vout <n> --fund-amount <sats>
```

Alice's key-path Taproot address (for faucet funding): `tb1p060z97qusuxe7w6h8z0l9kam5kn76jur22ecel75wjlmnkpxtnls6vdgne`

### Step 3: Bob scans and spends

```bash
# Scan only (verify derivation, no spend):
python3 03_bob_scan_and_spend.py

# Scan + build spend transaction:
python3 03_bob_scan_and_spend.py --sp-txid <txid> --sp-vout <n> --sp-amount <sats>
```

## Reference transactions (chapter)

| Step | txid | Notes |
|------|------|-------|
| Alice send #1 | `b93523c5784080f1ca402bca39edda109e6e64c0df576c964e64630fb0f778e8` | 5,000 sats to one-time address |
| Alice send #2 (same SP addr) | `c880a89f9eb8aa193cb9a4d936a85f35eac0afd38b48639eb0ece493cbe5b017` | Different one-time output — unlinkable |
| Bob spends | `11774714227d2c8c787372efff666dd0a27b044766e503a6241d28d2e1b8d91b` | 4,846 sats to Bob's regular address |

Explorer: `https://mempool.space/testnet/tx/<txid>`

## Security warning

These scripts use **testnet** keys and wallets for educational purposes only. **Do not** use for mainnet or production.
