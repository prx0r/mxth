# Adding a new mathematical / scientific artist

The extension boundary is intentionally narrow.

## Fast path: an immutable trajectory

If a paper, simulator or experiment can export a tensor, do **not** write a new renderer first.
Export `T×H×W`, `T×H×W×C`, or `T×N` (`N` square) as `.npy`/`.npz` and run:

```bash
python scripts/import_array_sequence.py run.npy \
  --id PAPER26_STATE \
  --title "Paper 2026 / state field" \
  --fps 12 \
  --provenance-level EXACT-DATA
```

That command:
1. hashes the original scientific artifact,
2. writes a display-quantized immutable trajectory,
3. creates a `MathArtistSpec`, and
4. makes it appear in the dashboard automatically through the generic array-sequence renderer.

The quantized browser copy is for display only. The original SHA-256 is retained in the immutable core.

## Paper2Agent path

Use Paper2Agent upstream to turn the paper/code/supplements into tested tools, then produce an
`observable-manifest.json` describing:

- source files + hashes,
- executable entry point,
- fixed scientific parameters,
- observables that may be exported,
- source tests.

MathArtist sits **downstream** of this manifest. It never asks an LLM to rewrite the source equations during evolution.

## Native renderer path

Only add `app/static/js/sources/<name>.js` when the scientific object has structure worth rendering
without rasterizing first (e.g. analytic eigenmodes, vector fields, 3-D trajectories). Add one dispatch
case in `sources/index.js`. The renderer receives only:

```js
render(canvas, phenotype, time)
```

`phenotype.source_variant` identifies a frozen valid source object and `phenotype.genome` contains
**interpretation genes only**.

## Non-negotiable invariant

A child may mutate sampling, observable, projection, temporal readout, exposure, persistence, camera,
and other declared observation operations. It may not mutate source equations, fitted scientific
parameters, source data, initial condition, or source variant.
