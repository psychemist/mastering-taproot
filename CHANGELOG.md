# Changelog

Engineering updates: new chapters, code releases, script changes.

---

## Up to Feb 14, 2026

**Published Chapters 10–12 manuscripts and Chapter 8 code**

Three new manuscript chapters completing the book's advanced application arc:

- Chapter 10 — RGB: Client-Side Validation & Taproot Commitments
- Chapter 11 — Lightning Network Channels: From P2WSH Multisig to Taproot Privacy Channels
- Chapter 12 — Silent Payments: Elliptic Curve Arithmetic and Address Privacy

These chapters explore four dimensions of Taproot's advanced capabilities:

| Chapter | Application | Taproot Capability |
|---------|-------------|---------------------|
| Ch 9 | Ordinals & BRC-20 | Witness space as data container |
| Ch 10 | RGB | Script path commitments anchoring off-chain state |
| Ch 11 | Lightning Network | Key aggregation + script trees for privacy protocols |
| Ch 12 | Silent Payments | EC arithmetic + output indistinguishability |

Chapter 8 code examples now published — full four-leaf MAST construction with all 7 spending paths:

- `01_create_four_leaf_taproot.py` — Build a 4-leaf Taproot script tree
- `02`–`05` — HashLock, Multisig, CSV Timelock, Simple Signature spending paths
- `06_key_path_spending.py` — Cooperative key path spend
- `07_verify_control_blocks.py` — Control block validation for all paths

> Ch 10–12 manuscripts are structural drafts — narrative and technical framework complete, code examples not yet fully tested. Feedback, issues, and PRs welcome.

---

## [2026-01-09] – [2026-02-08]

Added code examples for Chapters 6–8:

- Single-leaf and dual-leaf Taproot script tree construction
- Key Path and Script Path spending
- Control block verification
- Complete testnet-verified transactions

---

## [2025-12-09] – [2026-1-08]

Added code examples for Chapters 1–5:

- Key generation
- P2PKH/P2WPKH signing
- P2SH spend flows
- SegWit transaction construction
- Taproot key tweaking (BIP340/341 math)
