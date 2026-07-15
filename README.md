# 🐸 Toad Lore Guardian Kit

A portable, provenance-preserving lore corpus and agent kit for Toadgang builders creating **Gemini Gems**, **ChatGPT GPTs**, and other lore guardians.

> **One pond archive. Many guardians. The models may change; the scrolls remain.**

## What this repository provides

This repository turns the public Toadgod and Tobyworld scroll archive into platform-ready knowledge files while preserving the boundary between source statements, community commentary, interpretation, and unknown waters.

The public v1 corpus contains **4,690 records** derived from:

- 116 legacy records from the annotated `toadgod-lore.json` archive
- 4,574 included Markdown scroll records
- source IDs, dates, filenames, URLs, content hashes, tags, symbols, evidence layers, and status flags

The corpus is designed for lore study and agent building. It is not a price oracle, financial adviser, or claim of ownership or official authority over Tobyworld.

## Quick start

### Gemini Gem

1. Open [`platforms/gemini-gem`](platforms/gemini-gem).
2. Download and upload **all 10 files** to the Gem's Knowledge section.
3. Paste [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) into the Gem's Instructions field.
4. Keep the default tool disabled for a closed-book lore test.
5. Save the Gem and begin a fresh conversation.

Full guide: [`docs/QUICKSTART_GEMINI.md`](docs/QUICKSTART_GEMINI.md)

### ChatGPT GPT

1. Open [`platforms/chatgpt-gpt`](platforms/chatgpt-gpt).
2. Download and upload **all 10 files** to the GPT's Knowledge section.
3. Paste [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) into the GPT's Instructions field.
4. Disable web browsing for a closed-book lore test.
5. Save the GPT and begin a fresh conversation.

Full guide: [`docs/QUICKSTART_CHATGPT.md`](docs/QUICKSTART_CHATGPT.md)

## Suggested first tests

```text
What is Taboshi?
```

```text
Quick study: What is Rune3?
```

```text
Separate what Toadgod directly stated from what the archive interprets about Epoch 3.
```

```text
What happened to the proposed Patience Vault? Distinguish the original proposal from its later status.
```

## Repository structure

```text
toad-lore-guardian-kit/
├── README.md
├── SYSTEM_PROMPT.md
├── corpus/
│   └── record-index.json
├── docs/
│   ├── PROVENANCE.md
│   ├── QUICKSTART_CHATGPT.md
│   └── QUICKSTART_GEMINI.md
├── platforms/
│   ├── chatgpt-gpt/       # 10 JSONL/manifest knowledge files
│   └── gemini-gem/        # 10 JSON/manifest knowledge files
├── release/
│   └── v1/build-summary.json
├── reports/
│   ├── build-report.json
│   └── excluded-files.json
├── schema/
│   └── toadgod-lore-record-public-v1.schema.json
└── scripts/
    └── build_lore_pack.py
```

## Provenance model

The corpus does not flatten every scroll into one voice. It distinguishes:

- `source_material` — quoted or reproduced source statements
- `independently_verified_fact` — facts backed by independent evidence included in the record
- `community_commentary` — community-authored explanation or annotation
- `community_interpretation` — symbolic or spiritual interpretation
- `model_inference` — a connection reasoned by an agent
- `unknown` — not established by the supplied records

Read [`docs/PROVENANCE.md`](docs/PROVENANCE.md) for the evidence rules and current-status handling.

## Current-status handling

Historical proposals remain part of the archive, but later corrections and cancellations must be presented as later status updates. In particular, the public v1 manifest flags the record stating that the proposed **Rune3 Patience Vault distribution was later cancelled**. A guardian must not describe that proposed vault as currently active.

## Public boundary

Tobyworld is Toadgod's project and world. ToadAid, Mirror, and Toadgang builders preserve, study, and reflect the lore; this repository does not claim ownership, authorship, control, or official authority over Tobyworld.

Do not use the corpus to:

- invent canon, guarantees, rewards, or eligibility
- expose private information
- provide price predictions or financial advice
- present community interpretation as a direct Toadgod statement

## Build and validation

- [`schema/toadgod-lore-record-public-v1.schema.json`](schema/toadgod-lore-record-public-v1.schema.json) defines the public record contract.
- [`corpus/record-index.json`](corpus/record-index.json) provides a compact index of all included records.
- [`reports/build-report.json`](reports/build-report.json) records build statistics and checks.
- [`reports/excluded-files.json`](reports/excluded-files.json) documents deterministic exclusions and reasons.
- [`scripts/build_lore_pack.py`](scripts/build_lore_pack.py) is the reproducible corpus builder.

## License status

**No license has been added yet.** The repository is public for viewing and testing, but no broad reuse rights are granted until ToadAid publishes explicit terms.

Stillness is not absence.  
Study before speaking.  
Do not leap beyond the evidence.
