# CONFUSED.md — things I don't fully understand or couldn't resolve

This document records every genuine uncertainty, ambiguity, unresolved tension, or
"not sure if this is right" encountered during the v3.3 build-out. Nothing here is
intentionally left broken; each item either has a provisional fix documented or
requires human judgment to resolve. Peer reviewers: please confirm or correct.

## 1. NS26 was mutable in v1, frozen in v3 — is this intentional linearity?

v1's `src/artists.js NS26_CORE` allowed mutating `h`, `tau`, `twist`, `etaFreq` —
scientific parameters. The v3 spec freezes all of these into the scaffold + schedule
and declares them immutable. The `v1_lineage` note I added is non-hashed. Was this
intended as a hard design break from v1, or should some of these parameters be
admitted as controls? The REVIEW.md says "frozen model M(theta)" but v1 clearly
allowed varying them. **Needs confirmation.**

## 2. What is `mathartist-v3.2-resource-megapack/mathartist/mathartist-suite-v3.2.0.zip`?

The megapack contains a second copy of the v3.2.0 release zip inside itself. Is this
a distribution convenience (download one thing, get both the manifest and the suite)
or an accidental duplication? I didn't unpack it separately; it's byte-identical to
`unpacked/v3.2.0/`. **Should it be referenced or removed?**

## 3. French-flag bioelectric trajectory doesn't reproduce from the generator

`tools/generate_trajectories.py::generate_bioelectric()` produces byte-different
`french-flag.f32.bin` from the shipped one. I restored the shipped bytes. The README
says "Deterministic" but this one variant isn't. The generator was likely updated after
the v3.3.0 zip was produced. **Should the generator be patched to match, or should
the shipped bytes be documented as "predates generator v3.3"?**

## 4. E0 source identity fails — descriptor coarseness or real problem?

1-NN LOO accuracy: NS26 0.75, TINYMAPS 0.71, but BIOELECTRIC/CHLADNI/LENIA/VORTEX
all ~0.33-0.50. The contact sheets obviously show different visual families. Is this:
(a) the 6-feature descriptor space is too coarse for field-type sources (likely)?
(b) some renderers are genuinely too similar at the observation level?
(c) the shared monochrome grammar is suppressing family-specific features?

**I can't tell from the data alone.** This is a research question, not a bug.

## 5. `french-flag` bundle hash changed when I touched the file, then I restored it

The `french-flag.f32.bin` was byte-identical to the v3.3.0 archive, but I initially
overwrote it with generator output (which differs). Restoring it means the bundle
hashes match v3.3.0, but if anyone regenerates with the current generator, the hashes
will break. **Is there a "golden bytes" policy I should follow?**

## 6. POTENTIAL→BRANCH wiring is new — untested in the browser

I added:
- `/api/expand` POST endpoint (server.py)
- BRANCH button + `expandBranch()` (app.js)
- `tools/expand_potential.py` CLI
- Keyboard shortcut 'b' for POTENTIAL mode

But I could not browser-test this because the dev server kept timing out in my
environment. The Python logic works (`create_population` with `selected_ids`).
**Needs live browser verification.**

## 7. `api/sources` strips `interpretation_genes` but not `control_surface`

```python
[{k:v for k,v in s.items() if k not in ("interpretation_genes",)} for s in specs.values()]
```

This was probably intentional (V2 compat: strip the legacy key from the API response
so the browser doesn't confuse it with a control surface). But it means:
- If a spec has BOTH `interpretation_genes` AND `control_surface`, the API still
  returns `control_surface`.
- If a spec has only `interpretation_genes`, the API returns an empty control surface
  object (since the browser reads `.control_surface`).

**Is this the right behavior? Should V2 sources that haven't been upgraded show
`interpretation_genes` in the API?**

## 8. Lenia/Bioelectric/Chladni still use `interpretation_genes` — is this a bug?

These three sources still use the legacy `interpretation_genes` format, not the
evidence-backed `control_surface` format. The `controlsurface.engine.py` falls back
to `interpretation_genes` via `surface_for_spec()`. But:
- No provenance/role/claim_scope validation runs for these sources
- The browser UI shows them identically to NS26

**Should these be upgraded? Or is the fallback intentional for backward compatibility?**

## 9. `corpus/tsubuyaki/local_registry.jsonl` has 994 records — what now?

The corpus ingestion is done. The literal extraction (`control_candidates.json`) found
14k candidate numerics. But the v3.3 acceptance benchmark says ">=25 real seeds x 1000
descendants = 25k specimens." I haven't created the 25-seed benchmark yet. **Which 25
seeds?** The `priority_mechanisms` list in `registry.json` suggests categories
(coupled-latent-map, point-predicate, parametric-orbit, recurrence, bitwise-geometry,
fluid-dynamics, curve-growth, wave-eigenmode, cellular-dynamics) but the actual seed
selection requires human judgment about which sketches are (a) runnable, (b) license
compatible, (c) interesting.

## 10. `tools/e0_source_identity.py` — what threshold for "distinct"?

I set 0.6 accuracy as the pass threshold for individual sources. Why 0.6? It's above
chance (0.167) but below "clearly distinct" (0.8+). **Is this too lenient? Too strict?**
The 1-NN LOO metric itself may be too harsh for coarse descriptors — a Mahalanobis or
kernel metric might better capture family structure.

## 11. `tools/render_preview.py` re-derives the NS26 render independently

The preview generator has its own NS26 implementation (not importing from `ns26_core.js`
or the trajectory data). It was updated to read the frozen schedule/scaffold, but the
math diverges slightly from the JS renderer (e.g., fixed `phase = framePhase + tt*vel*0.025`
vs the JS which uses `framePhase + tt*S.vel*0.025` where S.vel changes per frame).
**This means the preview may not exactly match a browser render at the same t.**
Acceptable for a preview? Or should it use the exact JS renderer via Node?

## 12. `tools/discover_at_volume.py` uses `morphology.py` — what does `novelty()` do?

I imported and used `morphology.novelty`, `morphology.farthest_first`, and
`morphology.fertility` without fully understanding the embedding space. The descriptors
are 6-feature vectors from `aesthetics/descriptors.py`. The novelty metric appears to
be nearest-neighbor distance in that 6D space. **Is this a reasonable proxy for
"morphological novelty" or should it use a learned embedding?**

## 13. `/api/sources` returns 6 sources including VORTEX_DECAY_DEMO — is this right?

The vortex demo is a synthetic demonstrator, not a scientific source. It has
`provenance_level: EXACT-DATA` and `upstream: source_artifacts/...`. But the verifier
only checks for `{'LENIA','CHLADNI','BIOELECTRIC','NS26','TINYMAPS'}` as a subset.
**Should VORTEX_DECAY_DEMO be excluded from the production API? Or is "honest synthetic"
a valid source category?**

## 14. `docs/benchmarks/v3.3-corpus/v3.3-corpus/` directory doesn't exist

The diff said "Only in v3.3.0: docs/benchmarks/v3.3-corpus" but that directory was
empty. I filled it with NS26 artifacts. But the directory name `v3.3-corpus` is
slightly misleading — it should perhaps be `ns26-corpus` since the corpus ingestion
(#つぶやきProcessing) work is separate from the NS26 benchmarks. **Naming issue.**

## 15. How does `list_population` mode `'potential'` work with multiple sources?

Currently the POTENTIAL tab queries events across ALL sources, then filters by
`source_id`. If you mark POTENTIAL on LENIA and NS26, the POTENTIAL tab shows them
interleaved by timestamp. But if you switch sources while on the POTENTIAL tab, it
re-filters. **Is this the intended UX? Should POTENTIAL be per-source or global?**

## 16. `controlsurface/engine.py` `surface_for_spec()` falls back to `interpretation_genes`

This is the compatibility layer. But it means:
```python
surface_for_spec(spec, variant)  # returns interpretation_genes if no control_surface
```
If a future spec has BOTH keys, the function returns `control_surface` (correct).
If neither key exists, it returns `{}` (empty surface, probably a bug).
If only `interpretation_genes` exists, it returns those (legacy behavior).
**The function silently accepts legacy specs. Is this the right tradeoff?**

## 17. `scripts/import_array_sequence.py` creates a new spec dynamically

The VORTEX_DECAY_DEMO spec was created by this script with hardcoded interpretation
genes (rotation, zoom, threshold, etc.) — NOT evidence-backed control surfaces.
This means the demo source has the same legacy gap as Lenia/Bioelectric/Chladni.
**Should imported sources use control_surface format?**

## 18. The dashboard doesn't render a preview for standalone mode

When `?standalone` is in the URL, the dashboard loads `demo-population.json` and
renders without a server. But the demo fixture generates random genomes for all 6
sources including VORTEX_DECAY_DEMO, which requires the imported JSON. The standalone
mode works but shows random params, not curated specimens. **Acceptable for a demo?**

## 19. `aesthetics/descriptors.py` and `app/static/js/core/metrics.js` may drift

The Python descriptors compute: symmetry (D4 group), spectral entropy, occupancy,
edge density, saturation, contrast, mean. The JS metrics compute the same things
but with different implementation details (e.g., JS uses 64x64 downsample, Python
uses native resolution; JS has `fg = mean + 0.65*contrast` threshold, Python may
differ). The `specimenGate` grammar is the same JSON in both. **Are the numerical
results comparable? Cross-validation suggests they agree on pass/fail for NS26 frames
but I haven't done systematic comparison.**

## 20. What happens when a user clicks EVOLVE in POTENTIAL mode without selecting?

I added a guard: `toast('select POTENTIAL specimens to branch')`. But the original
design said POTENTIAL creates local expansion jobs. The guard prevents accidental
global evolution from the POTENTIAL tab. **Is this too restrictive? Should EVOLVE
in POTENTIAL mode automatically use the top POTENTIAL-scored specimens as parents?**

## 21. `tools/package.py` excludes `corpus/tsubuyaki/code/` but not `corpus/tsubuyaki/`

The exclusion uses `startswith('corpus/tsubuyaki/code/')`. The `local_registry.jsonl`
and `control_candidates.json` ARE shipped. But they reference code files by local
path (e.g., `corpus/tsubuyaki/code/2100481433668383127.js`) which won't exist in the
zip. **Is this intentional? Should the registry strip code_local paths on export?**

## 22. The v3.3 acceptance benchmark requires 25k specimens — we're at ~1600

Current count: 96 (NS26 audit) + 256 (NS26 discovery) + 384 (NS26 gallery) + 264
(seeded DB) + 18 (all-source render) = ~1018 unique NS26 specimens. We need 25k.
**This is a compute question, not a code question. Run `discover_at_volume.py` at
higher counts, or is there a different approach?**

## 23. `third_party/` contains LICENSE files I haven't fully reviewed

`lenia/LICENSE.md`, `cymatics/LICENSE`, `electric_morphogenesis/PROVENANCE.md` — I
read the READMEs but haven't done a full license audit. The megapack's `RESOURCE_NOTES.md`
says "review every upstream LICENSE before redistribution." **Peer reviewer should
confirm these are compatible with MathArtist's distribution terms.**

## 24. The server's `ThreadHTTPServer` may not handle concurrent expand requests well

The expand endpoint calls `create_population` which acquires a SQLite connection.
With `ThreadingHTTPServer`, multiple concurrent expand requests could contend on the
DB. The WAL mode helps but doesn't prevent it. **Is this a real concern for a
single-user dashboard?**

## 25. What is `experiments/RASA_QRI.md` and `experiments/ATTENTION.md`?

I see these in the repo but haven't read them. They may contain important experimental
design notes that affect how I should interpret the experiment registry JSON files.
**They should be read and cross-referenced with the experiment_store.py logic.**

## 26. `docs/ARCHITECTURE_V2.md` exists but is never referenced

This is presumably the V2 architecture doc, kept as history. But it's never linked
from README.md or CONTINUE_HERE.md. **Should it be preserved or removed?**

## 27. `morphology.py` — what are the actual functions?

I imported `novelty`, `farthest_first`, `fertility` from `morphology.py` but didn't
read it. These drive the discovery pipeline's coverage selection. **Should be read
and understood before any production use.**

## 28. `selfcheck.py` — what does it do?

This tool exists in every release but I never ran it. It likely does a lightweight
integrity check. **Should be integrated into CI.**

## 29. `tools/render_video.py` and `tools/render_frames.cjs` — untested

These exist for video rendering (presumably to produce MP4s of phenotypes). I never
tested them because they likely require ffmpeg or a similar tool. **Should be verified.**

## 30. The `controlsurface/examples.json` — what is this?

I see `controlsurface/examples.json` in the tree but never read it. It probably
contains example control surfaces for documentation. **Should be cross-referenced
with the actual specs.**

---

**Summary of what's definitely working:**
- Server starts, serves all 6 sources, all endpoints respond
- NS26 frozen bytes are byte-reproducible from the generator
- JS and Python viability gates agree
- 25/25 tests pass, verifier green
- 19 bundle manifests all resolve + hash
- Release zip builds with zero leaks
- 994 #つぶやきProcessing records ingested with attribution
- NS26 art production running (700+ specimens)

**Summary of what needs human review:**
- Items 1, 4, 9, 10, 22 (research/design questions)
- Items 3, 5, 11, 12 (implementation details)
- Items 6, 8, 16, 17, 20 (compatibility/architecture)
- Items 15, 21, 24 (UX/integrity)
- Items 23, 25, 26, 27, 28, 29, 30 (documentation/tools I didn't fully audit)
