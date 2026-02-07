# Mastering Taproot (Public Draft)

<p align="center">
  <img src="images/cover.jpg" width="260">
</p>

### About the Book

*Mastering Taproot* is a developer-focused, reproducible guide to Bitcoin’s most powerful upgrade — Taproot.

This manuscript emphasizes:

- full code samples
- real testnet transactions
- precise stack execution
- minimal abstractions

The goal is not to “explain concepts”, but to **engineer them** — from single-leaf script spends, to multi-path Merkle tree constructions, to privacy-preserving control blocks.

Foundational Bitcoin engineering knowledge should be reproducible, inspectable, and forkable — therefore this work is published open-access.

---

### Audience

This project is intended for:

- Developers learning Bitcoin programming through hands-on construction (Chapters 1–8 provide a complete on-ramp)
- Bitcoin protocol engineers and Script / Taproot developers
- Wallet and key management system designers
- Researchers studying Schnorr signatures, Merkle commitments, or Taproot privacy
- Anyone interested in Taproot's advanced applications: Ordinals, RGB, Lightning, and Silent Payments (Chapters 9–12)

---

### Status

This is an active public draft. The full 12-chapter structure is now published.

| Chapters | Manuscript | Code | Maturity |
|----------|-----------|------|----------|
| Ch 1–8 | ✅ Published | ✅ Tested & published | **Stable** — all code tested on testnet |
| Ch 9 | ✅ Published | ✅ Published | **Stable** — code tested on testnet |
| Ch 10–12 | ✅ Published | 📝 In progress | **Draft** — structure and narrative complete; code examples in manuscripts not yet fully tested. Issues and PRs welcome. |

The framework-first, code-iterative approach: the complete narrative arc from private keys to Silent Payments is in place. Code for Chapters 10–12 will be refined and uploaded incrementally.

⸻

### Educational Use

Parts of this repository will also be used in future Bitcoin developer onboarding sessions, further supporting newcomers entering Script, Taproot, and protocol-level engineering.

**Notebook Edition (Early Preview):**

An early MyST-based notebook version is being developed alongside this repository, enabling interactive execution of the core chapters (real testnet flows) as the project continues to mature.

---

### Repository Structure

Manuscripts (12 chapters):  
[`book/manuscript/`](./book/manuscript/)

Table of contents:  
[`book/manuscript/SUMMARY.md`](./book/manuscript/SUMMARY.md)

Code examples (Ch 1–8 published):  
[`code/`](./code/)

---

### How to Use This Repository

1. **Read the Manuscript**

   All chapters:
   
   [`book/manuscript/`](./book/manuscript/)
   
   Start with `SUMMARY.md` for the full outline.

2. **Run the Code**

   Every chapter's runnable examples live in [`code/`](./code/).
   
   All scripts include:
   
   - deterministic key generation
   - raw transaction hex construction
   - witness stack building
   - sighash verification
   - control block validation (Taproot)
   
   Scripts target Bitcoin testnet and require only Python 3.

3. **Verify Against the Network**

   Most examples produce:
   
   - a real testnet transaction ID
   - a decodeable raw transaction
   - validation steps you can run in Core (`decoderawtransaction`, `testmempoolaccept`, etc.)

---

### How to Contribute

Pull requests are welcome.

Typical contribution areas:

- typo fixes / formatting
- improved explanations / diagrams
- corrections to code samples
- additional reproducible testnet transactions

If you open an Issue, please include:

- chapter + section
- reproduction steps (if code)
- expected vs actual behavior

This project values *precision and reproducibility* above abstraction or opinions.

---

## 🔄 Recent Public Updates

*(latest development activity)*

**Feb 6, 2026 — Published Chapters 10–12 manuscripts and Chapter 8 code**

Three new manuscript chapters completing the book's advanced application arc:

• Chapter 10 — RGB: Client-Side Validation & Taproot Commitments

• Chapter 11 — Lightning Network Channels: From P2WSH Multisig to Taproot Privacy Channels

• Chapter 12 — Silent Payments: Elliptic Curve Arithmetic and Address Privacy

These chapters explore four dimensions of Taproot's advanced capabilities:

| Chapter | Application | Taproot Capability |
|---------|------------|-------------------|
| Ch 9 | Ordinals & BRC-20 | Witness space as data container |
| Ch 10 | RGB | Script path commitments anchoring off-chain state |
| Ch 11 | Lightning Network | Key aggregation + script trees for privacy protocols |
| Ch 12 | Silent Payments | EC arithmetic + output indistinguishability |

Chapter 8 code examples now published — full four-leaf MAST construction with all 7 spending paths:

• 01_create_four_leaf_taproot.py — Build a 4-leaf Taproot script tree

• 02–05 — HashLock, Multisig, CSV Timelock, Simple Signature spending paths

• 06_key_path_spending.py — Cooperative key path spend

• 07_verify_control_blocks.py — Control block validation for all paths

> **Note**: Ch 10–12 manuscripts are structural drafts — narrative and technical framework complete, code examples not yet fully tested. Feedback, issues, and PRs are welcome.

---

Jan 6–8, 2026 — Added code examples for Chapters 6–7, covering single-leaf and dual-leaf Taproot script tree construction, Key Path and Script Path spending, control block verification, and complete testnet-verified transactions.

---

Dec 5–20, 2025 — Added code examples for Chapters 1–5, covering key generation, P2PKH/P2WPKH signing, P2SH spend flows, SegWit transaction construction, and Taproot key tweaking (BIP340/341 math).

---

### Roadmap

Upcoming work:

• Code examples for Chapters 9–12 (incremental uploads as they reach testnet-verified stability)

• Interactive notebook edition (MyST-based, early preview)

---

### Acknowledgements

This project is supported by [OpenSats](https://opensats.org/).

---

### License

- Text: **CC-BY-SA 4.0**
- Code: **MIT**

This repository is developed in the open to support reproducible Bitcoin Script engineering education.