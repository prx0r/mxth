# Continue development from this ZIP

This repository is the canonical handoff. Do not rebuild the dashboard or source adapters from scratch.

## Stable interfaces

1. **Scientific source**: `specs/<ID>.json` + `source_bundle.files`.
2. **Immutable identity**: `app/source_bundles.py` hashes metadata **and actual source/runtime bytes** per variant.
3. **Interpretation search**: only keys declared under `interpretation_genes` may mutate.
4. **Renderer registry**: `app/static/js/sources/index.js`. Unknown registered array sequences use `arrayseq.js` automatically.
5. **Archive/event DB**: `app/archive.py`; migrations happen in `init_db()`.
6. **Formal experiments**: `experiments/registry/*.json` and `app/experiment_store.py`.
7. **Paper ingestion**: `paper2artist/`.
8. **Wild feedback**: `integrations/youtube/youtube_worker.py`.
9. **Optional open-ended backends**: `integrations/shinka/`, `integrations/pyribs/`; core must still run without them.

## Rules future agents must preserve

- Never mutate source equations, trained parameters, source data, reference trajectory bytes, or executable scientific runtime to improve aesthetics.
- If any frozen source byte changes, register a new source/version rather than continuing an old lineage.
- Rendering and interpretation code may evolve only if its allowed degrees of freedom are declared in the source spec.
- Rasa labels, QRI-inspired variables and YouTube retention are experimental measurements/hypotheses, not definitions of beauty or valence.
- Preserve `UPSTREAMS.lock.json`, provenance files and licenses.
- Add migrations; do not replace the archive schema destructively.
- Add a test for every new stable interface.

## Verify before editing

```bash
python scripts/verify_suite.py
```

Then inspect `VERSION`, `CHANGELOG.md`, `docs/ARCHITECTURE.md`, and this file.
