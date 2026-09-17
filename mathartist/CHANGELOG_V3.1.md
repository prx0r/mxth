# MathArtist V3.1.0

V3.1 turns the V3 control-surface thesis into an end-to-end executable family rather than only infrastructure.

## Implemented

- Added `TINYMAPS`, four compact mathematical programs distilled from Processing sketches supplied in the design session:
  - `radial-warp`
  - `polar-warp`
  - `latent-19`
  - `torus-lattice`
- Each variant has its own provenance-backed `control_surfaces` schema. The fixed program topology is immutable; only declared coefficients, phases, and sampling controls vary.
- Added variant-specific control-surface support to the mutation engine. A lineage can no longer silently inherit controls from a different mathematical variant.
- Added a deliberately minimal TINYMAPS observer: evaluate point set -> robust 1%-99% framing -> one-pixel grayscale points. No evolved camera, exposure, contour, trail, or style parameters.
- OPEN parent selection no longer reads favorites, dwell, fullscreen, retention, valence, or rasa. It uses recency, branch fertility, parameter-space diversity, random stepping stones, and root injection.
- Demoted V2.1 `SpecimenGrammar` from aesthetic composition filter to `integrity-gate-v3.1`. The gate now rejects only technically unreadable outputs (blank/flat/overexposed); full-frame, asymmetric, off-center, or compositionally strange mathematics is not suppressed.
- Added `tools/audit_v3_controls.py`, which renders the exact browser source renderer and reports technical integrity, exact thumbnail duplicates, temporal change, and structural nearest-neighbor diversity. These are development diagnostics, not beauty/valence scores.
- Added tests proving variant-specific surfaces remain bounded and OPEN parent selection is invariant to injected favorite/dwell events.
- Verification now includes an HTTP-generated TINYMAPS population and exact Node/browser-renderer smoke test.

## Reproducible V3.1 benchmark

`python tools/audit_v3_controls.py --count 96 --seed 3131`

The shipped benchmark at `docs/benchmarks/v3.1-controls/` contains the exact sampled genomes, audit JSON, and contact sheet. In the release build it produced 96/96 technically readable specimens with zero exact 24x24 thumbnail duplicates. Structural diversity is reported without treating it as aesthetic quality.
