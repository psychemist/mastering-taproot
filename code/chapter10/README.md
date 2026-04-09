# Chapter 10 — RGB and Tapret: Commitments Inside the Script Tree

RGB embeds state commitments inside the Taproot script tree (Tapret scheme). On-chain, a transfer looks like an ordinary P2TR spend — no OP_RETURN, no visible data. Verification is entirely client-side. This folder contains the business logic for a single-hop RGB20 transfer, a chain-side verification script, and a standalone Tapret leaf constructor.

## What this is / is not

- **Is:** A readable six-step RGB transfer flow (invoice → transfer → accept → sign → broadcast → verify), a standalone on-chain verifier, and a pure-Python Tapret leaf builder that requires no external dependencies.
- **Is not:** A packaged RGB environment. RGB requires external infrastructure (CLI binary, wallet directories, Esplora indexer, testnet funds). You install those yourself; the scripts here are the business logic that runs on top.

## Layout

| File | Role |
|------|------|
| `01_rgb_transfer_single_hop.py` | Alice → Bob transfer: six steps, each calling `rgb` CLI via subprocess |
| `02_verify_tx_onchain.py` | Fetch a txid from Esplora, confirm outputs are P2TR (no rgb needed) |
| `03_tapret_leaf.py` | Build the 64-byte Tapret leaf from scratch; print byte-by-byte structure (no dependencies) |
| `requirements.txt` | Stdlib only; Python 3.9+ |

## Prerequisites

### For `02_verify_tx_onchain.py` (no install)

- Python 3.9+ (stdlib only, no pip)
- A web connection to `mempool.space/testnet/api` (Esplora)

### For `03_tapret_leaf.py` (no install)

- Python 3.9+ (stdlib only, no pip)
- **No network** — runs fully offline; builds and prints the 64-byte leaf from local hex / random bytes

### For `01_rgb_transfer_single_hop.py` (full flow)

| Component | What to install | Notes |
|-----------|----------------|-------|
| **`rgb` CLI** | A released RGB CLI binary from the LNP/BP project | Put on `PATH` or set `RGB_CLI_BIN` |
| **Wallet directories** | Two dirs (Alice, Bob) created by `rgb` with an imported RGB20 contract | Alice must hold unspent allocations |
| **Bitcoin Core** | `bitcoin-cli` for PSBT signing and broadcast | Testnet, with a loaded descriptor wallet |
| **Testnet funds** | Enough sats for transaction fees | From any testnet faucet |
| **Esplora** | Public `mempool.space/testnet/api` works | Or self-hosted |

## Setup

```bash
cd code/chapter10
```

No virtual environment needed — all scripts use stdlib only.

## Run

### Quick verify (no rgb required)

Confirm the chapter's reference transaction is an ordinary Taproot spend:

```bash
python3 02_verify_tx_onchain.py 64a1455125724ce79d4914d7af5e0226f465c7522b8dd6f048440b8935c20b6b
```

Expected output (matches `02_verify_tx_onchain.py`):

```
txid: 64a1455125724ce79d4914d7af5e0226f465c7522b8dd6f048440b8935c20b6b
inputs: 1

  vout[0]  type=v1_p2tr  value=600 sats  tb1pd057tgt4u38ur4znyszme79lhqjg8zluhx9x4erdmc6zey2nqzjq02w5sv
  vout[1]  type=v1_p2tr  value=2000 sats  tb1p9yjaffzhuh9p7d9gnwfunxssngesk25tz7rudu4v69dl6e7w7qhqellhrw

All outputs are P2TR. No OP_RETURN. Indistinguishable from a normal Taproot spend.

Explorer: https://mempool.space/testnet/tx/64a1455125724ce79d4914d7af5e0226f465c7522b8dd6f048440b8935c20b6b
```

### Build a Tapret leaf (no rgb required)

Construct the 64-byte Tapret leaf structure and inspect it byte by byte:

```bash
python3 03_tapret_leaf.py
```

Optional: fixed commitment and nonce (reproducible output; no random line):

```bash
python3 03_tapret_leaf.py --commitment <64-hex-chars> --nonce 0
```

### Full transfer flow

Set environment variables for your RGB setup:

```bash
export RGB_CLI_BIN="rgb"                                    # or absolute path
export RGB_ALICE_DIR="/path/to/alice_wallet"
export RGB_BOB_DIR="/path/to/bob_wallet"
export RGB_CONTRACT_ID="rgb:...."
export RGB_NETWORK="testnet3"
export RGB_ESPLORA_URL="https://mempool.space/testnet/api"
export RGB_BITCOIN_WALLET="wallet_testnet"                  # bitcoin-cli -rpcwallet name
```

Run the six-step transfer:

```bash
python3 01_rgb_transfer_single_hop.py --amount 100
```

To stop before signing (inspect the PSBT yourself):

```bash
python3 01_rgb_transfer_single_hop.py --amount 100 --skip-broadcast
```

## Reference transaction (chapter)

Transfer (Alice → Bob, 100 units RGB20):

- txid: `64a1455125724ce79d4914d7af5e0226f465c7522b8dd6f048440b8935c20b6b`
- Explorer: `https://mempool.space/testnet/tx/64a1455125724ce79d4914d7af5e0226f465c7522b8dd6f048440b8935c20b6b`
- vout:0 — P2TR, 600 sats (Alice change)
- vout:1 — P2TR, 2000 sats (Bob receipt)

Both outputs are standard P2TR. The Tapret commitment is inside the script tree, invisible on-chain.

## Implementation note: Tapret leaf byte layout

The Tapret leaf structure in this chapter follows the current RGB implementation (rgb-wallet 0.11.0-beta.9), verified against PSBT output on testnet and consistent with [RGB Docs: Tapret](https://docs.rgb.info/commitment-layer/deterministic-bitcoin-commitments-dbc/tapret):

```
29 bytes  OP_RESERVED (0x50) × 29   — padding, makes leaf unspendable with OP_RETURN
 1 byte   OP_RETURN (0x6A)
 1 byte   OP_PUSHBYTES_33 (0x21)
32 bytes  MPC commitment
 1 byte   nonce
─────────────────────────────────
64 bytes  total (leaf version 0xC0)
```

The original LNPBP-12 draft describes a slightly different layout (28 bytes `OP_INVALIDOPCODE`, nonce before `OP_RETURN`). Both produce a 64-byte unspendable leaf. If you are using a different RGB version, decode your own PSBT output to verify the actual structure — `03_tapret_leaf.py` shows how the bytes are assembled.

## Security Warning

These scripts use **testnet** keys and wallets for educational purposes only. **DO NOT** use for mainnet or production.