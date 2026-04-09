# Chapter 11 — Lightning Network Channels: P2WSH to Taproot

Side-by-side comparison of traditional P2WSH Lightning channels and Taproot MuSig2 channels. Same two parties, same balances — completely different on-chain footprint.

## What this is / is not

- **Is:** Working P2WSH and Taproot channel funding + cooperative close transactions on **testnet**, with a real BIP-327 MuSig2 signing flow and a direct witness comparison.
- **Is not:** A Lightning node implementation. These scripts build individual transactions to illustrate the on-chain structure; they do not manage channel state or route payments.

## Layout

| File | Role |
|------|------|
| `01_p2wsh_funding_and_close.py` | P2WSH 2-of-2 multisig funding address + cooperative close (both sign, 4-element witness) |
| `02_taproot_funding_and_close.py` | MuSig2 KeyAgg + BIP86 funding address + cooperative close (single 64-byte Schnorr signature) |
| `03_compare_witness.py` | Builds both close transactions in memory and prints a side-by-side comparison table |
| `musig2_ref.py` | BIP-327 reference implementation (imported as a library by `02`; **do not run directly** — it requires official test vectors not included in this repository) |

## Setup

```bash
cd code/chapter11
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

### Quick comparison (no testnet funds needed)

```bash
python3 03_compare_witness.py
```

Prints a table comparing P2WSH vs Taproot witness size, structure, and privacy.

### P2WSH funding + close

```bash
# Show funding address
python3 01_p2wsh_funding_and_close.py

# With a funded UTXO: build and sign the cooperative close
python3 01_p2wsh_funding_and_close.py --fund-txid <txid> --fund-vout <n> --fund-amount <sats>
```

### Taproot MuSig2 funding + close

```bash
# Show funding address
python3 02_taproot_funding_and_close.py

# With a funded UTXO: full MuSig2 4-round signing
python3 02_taproot_funding_and_close.py --fund-txid <txid> --fund-vout <n> --fund-amount <sats>
```

## Reference transactions (chapter)

| Step | txid | Notes |
|------|------|-------|
| P2WSH funding | `7c512abcdc86e48837e6e5ba57524c3ee25f1c4bd4bf7d42f7db084b2d09767a` | 10,000 sats, P2WSH 2-of-2 |
| P2WSH cooperative close | `bd6da1cdd3740661875b2568c2b4494f818c3c3742f809e23512c43f52840461` | 4-element witness, 214 bytes |
| Taproot MuSig2 funding | `b7efde1f1659a6a48d998c7860d9a586ac65c6069e73ded9779f1f6e1898aace` | 10,000 sats, P2TR (BIP86) |
| Taproot MuSig2 close | `af6fdae8c2731b2b83e74b8dd79bc2c241dea8aee8c8cfb6f094e44c13b39d1f` | 1-element witness, 64 bytes |

Explorer: `https://mempool.space/testnet/tx/<txid>`

## Security warning

These scripts use **testnet** keys and wallets for educational purposes only. **Do not** use for mainnet or production.
