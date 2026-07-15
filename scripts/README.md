# Reproducible Builder

The full public v1 upload places `build_lore_pack.py` in this folder.

The builder accepts explicit source and output paths:

```bash
python scripts/build_lore_pack.py \
  --source-zip /path/to/lore-scrolls.zip \
  --legacy-json /path/to/toadgod-lore.json \
  --out-root build/toadgod-lore-agent-pack-public-v1 \
  --dist-dir dist
```

It rebuilds the Gemini and ChatGPT platform volumes, manifests, schema, record index, validation reports, and distributable ZIP bundles.
