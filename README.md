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

## Platform-specific prompts

The two supported platforms use separate instruction files:

- [`GEM_SYSTEM_PROMPT.md`](GEM_SYSTEM_PROMPT.md) — full prompt for Gemini Gems
- [`GPT_INSTRUCTIONS_PROMPT.md`](GPT_INSTRUCTIONS_PROMPT.md) — compact prompt for ChatGPT GPTs

Do not combine both prompts into one agent.

Both prompts use the same public corpus and evidence principles, but each is adapted to the behavior and instruction limits of its platform.

## Quick start

### Gemini Gem

1. Open [`platforms/gemini-gem`](platforms/gemini-gem).
2. Download and upload **all 10 files** to the Gem's Knowledge section.
3. Paste [`GEM_SYSTEM_PROMPT.md`](GEM_SYSTEM_PROMPT.md) into the Gem's Instructions field.
4. Keep the default tool disabled for the first closed-book lore test.
5. Save the Gem and begin a fresh conversation.

Gemini may display platform-generated source chips for uploaded knowledge files. Those interface elements are separate from the Guardian's written answer and may not be controlled by the prompt.

Full guide: [`docs/QUICKSTART_GEMINI.md`](docs/QUICKSTART_GEMINI.md)

### ChatGPT GPT

1. Open [`platforms/chatgpt-gpt`](platforms/chatgpt-gpt).
2. Download and upload **all 10 files** to the GPT's Knowledge section.
3. Paste [`GPT_INSTRUCTIONS_PROMPT.md`](GPT_INSTRUCTIONS_PROMPT.md) into the GPT's Instructions field.
4. Disable web browsing for the first closed-book lore test.
5. Save the GPT and begin a fresh conversation.

The GPT prompt is self-contained and designed to fit within the GPT Instructions character limit. Do not upload the Gemini prompt as an additional GPT knowledge file.

Full guide: [`docs/QUICKSTART_CHATGPT.md`](docs/QUICKSTART_CHATGPT.md)

## Suggested first tests

Run these tests in fresh conversations on both platforms:

```text
What is Toby?
```

```text
Why do I have to study the lore? What is the lore?
```

```text
What does “study frog life” mean?
```

```text
What happened to the proposed Rune3 Patience Vault?
```

```text
Show me the sources for your previous answer.
```

```text
Check this claim: Studying the lore guarantees future rewards.
```

A passing guardian should:

- answer ordinary questions plainly and proportionately
- distinguish Toby, `$TOBY`, Tobyworld, and Toadgang
- keep record IDs hidden unless sources are explicitly requested
- separate direct statements from community interpretation
- avoid promotional, devotional, and market-motivational language
- respect later corrections and cancellations
- avoid financial advice and reward guarantees

## Repository structure

```text
toad-lore-guardian-kit/
├── GEM_SYSTEM_PROMPT.md
├── GPT_INSTRUCTIONS_PROMPT.md
├── README.md
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

## Source visibility

Knowledge files should be used quietly for ordinary answers.

Record IDs and provenance details are opt-in and should appear only when a user explicitly requests sources, citations, evidence records, scroll IDs, repository references, or provenance.

Platform-generated source indicators may still appear in the Gemini or ChatGPT interface. Those interface elements are controlled by the platform rather than the repository prompt.

## Current-status handling

Historical proposals remain part of the archive, but later corrections and cancellations must be presented as later status updates.

In particular, the public v1 manifest flags the record stating that the proposed **Rune3 Patience Vault distribution was later cancelled**. A guardian must not describe that proposed vault as currently active or its planned actions as completed without separate execution evidence.

## Public boundary

Tobyworld is Toadgod's project and world.

ToadAid and Toadgang builders preserve, organize, study, and reflect the public lore. This repository does not claim ownership, authorship, control, endorsement, partnership, or official authority over Tobyworld.

Do not use the corpus to:

- invent canon, guarantees, rewards, or eligibility
- expose private information
- provide price predictions or financial advice
- present community interpretation as a direct Toadgod statement
- persuade users to buy, hold, believe, or expect future rewards

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
