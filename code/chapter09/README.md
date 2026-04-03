# Chapter 9 — BRC-20 mint (commit / reveal)

Minimal **bitcoinutils** example for the book: build a single-leaf Ordinals-style inscription envelope, fund a temporary taproot output (commit), then spend it script-path (reveal). Same pattern as Chapter 9 in the manuscript.

## What this is / is not

- **Is:** A working Taproot script-path + witness layout for a **mint-shaped** BRC-20 JSON payload on **testnet**, using the same fee order of magnitude as the chapter’s reference transactions.
- **Is not:** A guarantee that you will reproduce the **exact txids** in the book (those came from one UTXO and fee snapshot). Your txids will differ unless you replay the same inputs and amounts.
- **Is not:** A wallet or indexer. Whether third-party software shows a balance depends on **off-chain** rules and software versions.

## Layout

| File | Role |
|------|------|
| `1_commit_mint_brc20.py` | Key-path spend → temporary address; writes `commit_mint_info.json` |
| `2_reveal_mint_brc20.py` | Script-path spend → reveals inscription in witness |
| `tools/brc20_config.py` | Network, fees, JSON payload, inscription constants |
| `tools/utxo_scanner.py` | Lists UTXOs for your funding address via Blockstream testnet API |

## Setup

```bash
cd code/chapter09
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

- Default testnet WIF matches the **public** example in the book. For your own keys:

  ```bash
  export BRC20_WIF='your_testnet_wif_here'
  ```

- You need **testnet coins** on the **key-path** taproot address printed by script 1. Fund that address from a faucet, then run commit.

## Run

1. **Commit** (builds, signs, prints raw hex; saves `commit_mint_info.json`):

   ```bash
   python3 1_commit_mint_brc20.py
   ```

2. Broadcast the raw hex (your own node or a testnet pushtx service). Wait until the commit is **confirmed**.

3. **Reveal**:

   ```bash
   python3 2_reveal_mint_brc20.py
   ```

4. Broadcast the reveal hex. Inspect the transaction on a testnet explorer: witness stack = signature, inscription script, control block.

## Reference transactions (chapter)

These are **historical** testnet transactions for comparison (same pattern as the scripts):

- Commit: `515ddcfc2ddb5ebadb6be493a955e490c54d399cf2cc528cecc302e41f950aa0`
- Reveal: `2fc169a5eb2f096bc8e64cb946380869ee2a2099f67cc3d5e719fbe9fff57547`

Explorer (example): `https://mempool.space/testnet/tx/<txid>`

## Archive

Older experiments (including btcaaron variants) live under `code/chapter09-archive/` and are **not** required for the book’s main line.
