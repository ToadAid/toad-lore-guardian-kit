# ChatGPT GPT Quick Start

## Create the GPT

1. Open the GPT builder and create a new GPT.
2. Suggested name: **Study the Lore — Corpus v1**.
3. Paste the complete contents of [`../GPT_INSTRUCTIONS_PROMPT.md`](../GPT_INSTRUCTIONS_PROMPT.md) into **Instructions**.
4. Keep web browsing disabled for the first closed-book test.

The compact GPT prompt is designed for the GPT Instructions character limit and is self-contained.

Do not paste the Gemini prompt into the GPT Instructions field, combine both prompts, or upload the Gemini prompt as an additional knowledge file.

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

Upload the extracted files themselves, not a ZIP archive.

## Save and test

Save the GPT and begin a fresh conversation for each important regression test:

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

A passing GPT should:

- answer simple questions directly and proportionately
- distinguish Toby, `$TOBY`, Tobyworld, and Toadgang
- avoid ceremonial introductions and automatic follow-up questions
- keep record IDs hidden unless sources are explicitly requested
- provide a compact Sources section only when requested
- separate direct statements from community interpretation
- respect later corrections and cancellations
- avoid promotional language, reward promises, and financial advice

## Public sharing

Before sharing the GPT publicly, test it in fresh conversations.

Record IDs should not appear automatically. They should be shown only when the user explicitly requests sources, citations, evidence records, scroll IDs, repository references, or provenance.

The GPT must not claim that ToadAid owns, controls, endorses, or officially represents Tobyworld.
