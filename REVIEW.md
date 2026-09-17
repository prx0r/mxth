# Technical review

## Executive assessment

MathArtist's strongest architectural choice is the boundary between immutable scientific source material and the parameters exposed for artistic exploration. The v3 line makes that boundary explicit: freeze the source-backed model `M(theta)`, search only the evidence-backed control surface `theta`, and keep observation separate from generation. This is a sound foundation for reproducible mathematical art.

The latest runnable archive, `mathartist-suite-v3.3.0.zip`, remains the canonical working snapshot. `mathartist-v4-coding-agent-correction-pack.zip` is the implementation and acceptance plan for the next release, not a completed runtime. Older releases remain useful as design history and regression references.

## V4 direction

The correction pack focuses development on the actual emergence experiment rather than further source or dashboard expansion. Its hard gates require at least 25 attributed executable seeds, at least 1,000 blind descendants per seed, evidence for every mutable control, stronger morphology coverage, browser-tested human branching, retained failures and fully reproducible lineage/runtime identity. This directly addresses the most important gap in v3.3: strong infrastructure without yet demonstrating the complete large-scale experiment.

The companion human-aesthetic dashboard is a working static interaction prototype, not a replacement for the real generators. It cleanly separates the creative loop—mark potential, inspect, choose stepping stones, select mutation pressure and branch—from downstream Study/Analysis metrics. Production integration still needs to connect it to the real `OPEN_BLIND`, branch and fresh-root endpoints.

## V5 rescue direction

The V5 pack reviews repository head `248034f` and identifies concrete blockers in the emerging B25 implementation: regex-based literal classification presented as AST-based, an unverified seed list with silent filling, one Chromium launch per descendant, a non-Sobol sampler, unstable Python-hash seeding, inverted negative-literal ranges, full-page rather than canvas hashing, timing-field mismatch, missing image/embedding artifacts and incorrect p5 loading order. Its instruction is deliberately narrow: fix these issues without replatforming, then complete the 25-seed/25,000-descendant experiment and connect its outputs to the human branch loop.

## Verification performed

| Check | Result |
|---|---|
| ZIP container integrity | 11/11 passed `unzip -t` |
| Suite unit tests | v0.3: 5; v1.0: 5; v2.0: 7; v2.1: 7; v3.0: 10; v3.1: 12; v3.2: 14; v3.3: 16 — all passed |
| Official suite verifier | Passed through v3.0; v3.1–v3.3 stop only because `pytest` is not installed by the archive itself |
| V1 web build | `npm install` and `vite build` passed |
| Lab V2 JSON | All JSON files parsed successfully |
| Embedded release hashes | Megapack hashes for v3.0, v3.1 and v3.2 match the preserved archives exactly |
| Common secret patterns | No GitHub token, private-key, or AWS-secret pattern found in the archives |
| V4 dashboard static validation | ZIP integrity, JavaScript syntax and JSON manifest validation passed |
| V5 rescue-pack validation | ZIP integrity, JSON and JavaScript validation passed; packaged report records 4/4 tests passing |

The direct suite test counts above were obtained by loading each test module and invoking every no-fixture `test_*` function. This validates the bundled unit logic without changing the releases.

## Strengths

- Reproducibility is treated as a first-class feature through deterministic seeds, source bundles and hashes of causal files.
- Provenance becomes progressively stronger across releases, culminating in evidence-backed parameter controls rather than invented equations.
- The system distinguishes open-ended machine discovery from human response measurement, reducing feedback leakage into the search process.
- The adapter vocabulary — generate, measure, intervene, render and verify — gives external scientific engines a coherent integration boundary.
- The archive contains runnable examples and tests rather than only conceptual specifications.

## Limitations and release-hygiene issues

- The tests verify local logic and integrity, not live end-to-end integrations with Paper2Agent, Sakana, BETSE or YouTube.
- The YouTube path is observational; it cannot establish that an artwork caused a measured behavioral response. Controlled local experiments remain necessary for causal claims.
- NS26 is marked as derived, and the bioelectric components are equation-level demonstrations rather than full scientific reproductions. Those labels should remain prominent.
- README headings in v3.2 and v3.3 still identify the suite as V3.1.
- Later release archives contain generated `__pycache__` files that should be excluded from future release builds.
- The v3.1–v3.3 verifier invokes `pytest`, but the release does not declare or install that development dependency. Add a dev requirements file or make the verifier self-contained.
- `preview.png` / `preview(1).png` and `contact-sheet(3).png` / `contact-sheet(4).png` are byte-identical. They are preserved intentionally as separate chat outputs.

## Recommended next step

Make v3.3 the clean baseline: correct version strings, remove generated caches, declare test dependencies, and add one reproducible end-to-end adapter fixture with a recorded source bundle and expected render hash. That would turn the current strong conceptual boundary into a release process that is equally rigorous.
