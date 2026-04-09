# Mastering Taproot (Public Draft)

<p align="center">
  <img src="images/cover.jpg" width="260">
</p>

👉 Looking for the Mastering Taproot Lab? See [LAB.md](LAB.md)

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

The **book text and figures** can still change. The **code under [`code/`](./code/)** for all **12 chapters** is **complete and stable**: each folder has Python scripts, a README, and—if a flow needs the network—notes for reproducing it on **testnet**.

| Chapters | Manuscript | Code | Maturity |
|----------|-----------|------|----------|
| Ch 1–8 | ✅ Published | ✅ Tested & published | **Stable** — examples verified on testnet |
| Ch 9 | ✅ Published | ✅ Tested & published | **Stable** — examples verified on testnet |
| Ch 10–12 | ✅ Published | ✅ Tested & published | **Stable** — Tapret / RGB tooling, MuSig2-style cooperative close, and Silent Payments; setup and reference txids are in each chapter README |

⸻

### Interactive Notebooks

> **Try it live** — Run real Bitcoin Script examples step by step, modify parameters, and experiment with Taproot constructions interactively:
>
> **[bitcoincoding.dev](https://bitcoincoding.dev)** | [Source repo](https://github.com/aaron-recompile/mastering-taproot-interactive)

---

### Early Testers Welcome

If you're experimenting with the code examples, infrastructure tooling, or regtest scenarios and would like to provide feedback, early testers are very welcome.

See:  
👉 [Issue #38: Early testers welcome for btcaaron / btcrun](https://github.com/aaron-recompile/mastering-taproot/issues/38)

Small feedback such as installation experience, example execution results, or documentation clarity is extremely helpful at this stage.


---

### Repository Structure

```
mastering-taproot/
├── book/
│   ├── manuscript/        # 12 chapters (English)
│   └── translations/      # Community translations
├── code/
│   ├── chapter01/–12/    # Runnable Python examples (README + requirements.txt each)
├── images/                # Cover art
└── LICENSES/              # CC-BY-SA 4.0 (text) + MIT (code)
```

Manuscripts (12 chapters):  
[`book/manuscript/`](./book/manuscript/)

Table of contents:  
[`book/manuscript/SUMMARY.md`](./book/manuscript/SUMMARY.md)

Code examples (Chapters 1–12):  
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

### Recent Updates

For chapters, code releases, and script changes: [CHANGELOG.md](CHANGELOG.md)

---

### Roadmap

Upcoming work:

• Manuscript polish (wording, diagrams, cross-links)  
• Optional extra reproducible testnet transactions and README notes where they help readers  
• Issue-driven fixes and small improvements across all chapters

---

### Acknowledgements

This project is supported by [OpenSats](https://opensats.org/).

---

### License

- Text: **CC-BY-SA 4.0**
- Code: **MIT**

This repository is developed in the open to support reproducible Bitcoin Script engineering education.
