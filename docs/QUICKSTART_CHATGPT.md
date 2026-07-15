# ChatGPT GPT Quick Start

## Create the GPT

1. Open the GPT builder and create a new GPT.
2. Suggested name: **Study the Lore — Corpus v1**.
3. Paste the complete contents of [`../SYSTEM_PROMPT.md`](../SYSTEM_PROMPT.md) into **Instructions**.
4. Keep web browsing disabled for the first closed-book test.

## Add knowledge

Upload all 10 files from [`../platforms/chatgpt-gpt`](../platforms/chatgpt-gpt):

1. `01-foundation-source-records.jsonl`
2. `02-lore-scrolls-early.jsonl`
3. `03-lore-scrolls-later.jsonl`
4. `04-community-commentary-early.jsonl`
5. `05-community-commentary-later.jsonl`
6. `06-questions-and-answers-early.jsonl`
7. `07-questions-and-answers-later.jsonl`
8. `08-codex-reflections-early.jsonl`
9. `09-codex-reflections-later.jsonl`
10. `10-corpus-manifest.json`

Upload the files themselves rather than a ZIP archive.

## Save and test

Save the GPT and begin a fresh conversation. Use the same questions used for the Gemini Gem so we can compare retrieval and evidence discipline across platforms:

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

## Public sharing

Before sharing the GPT publicly, verify that it cites relevant record IDs, labels interpretation, respects corrections and cancellations, avoids financial advice, and does not claim official authority over Tobyworld.
