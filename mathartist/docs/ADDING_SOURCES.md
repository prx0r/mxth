# Adding a new scientific artist

A source has two independent layers:

1. **immutable source** — equations / author simulator / data / fixed source variant;
2. **interpretation** — the only layer evolution may mutate.

## Minimal source

1. Add `specs/NAME.json`.
2. Add `app/static/js/sources/name.js` exporting `render(canvas, phenotype, t)`.
3. Register it in `app/static/js/sources/index.js`.
4. Add a test asserting that every interpretation gene is absent from `immutable_core`.

If the source is expensive, precompute deterministic source states into `app/static/data/NAME/` and
check in the generator under `tools/`. The checked-in trajectory is source data, not an artwork.

## Paper2Agent route

`paper + supplements + author code -> Paper2Agent -> observable-manifest.json -> MathArtist spec`

The manifest must identify exact source files/SHAs, executable entry points, fixed parameters, source
variants, observables and validation tests. `integrations/paper2agent/observable-manifest.example.json`
is the contract. Do not label a source EXACT until its manifest can recreate the source state.

## Provenance levels

- `EXACT-RUNTIME`: author equations/data/runtime reproduced or wrapped with tests.
- `EXACT-EQUATIONS`: equations and declared parameters reproduced, but not every author artifact/trained state.
- `INVARIANT`: transformed representation with a validated invariant-preservation claim.
- `DERIVED`: genuinely downstream of the source result but not a complete implementation.
- `HYBRID` / `FREE`: reserved for later cross-source experiments and must never masquerade as exact.
