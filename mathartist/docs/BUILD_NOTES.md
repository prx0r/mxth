# MathArtist Build Notes — Session Handover

## What this is

MathArtist is a system for exploring mathematical art through controlled parameter search. The core idea: take real mathematical/scientific sources, expose their legitimate control surfaces, search them blindly, and let humans select stepping stones for further exploration.

The project's primary source is **NS26** — the 2026 forced Navier-Stokes blow-up construction. The similarity scaling relations (radial ~ tau^1/2, axial ~ tau^(1/2-h), velocity ~ tau^(-1/2-h)) are immutable. The parameters h, tau, twist, etaFreq are the search space.

## What was built in this session

### Starting point
- `prx0r/mxth` repo with 11 original ZIP archives (v1 through v3.3 + megapack) and chat-assets
- `mathartist-v3.3.0.zip` was the latest working snapshot

### v3.3 build-out (commits `3d5ac3f`)
- Unpacked all 11 zips into `unpacked/`
- Promoted v3.3 to canonical `mathartist/` tree
- Fixed version strings, removed caches, verified tests
- NS26 initially frozen as DERIVED (observation-only)
- Built corpus ingestion: 994 #つぶやきProcessing records with attribution + code hashes
- Dashboard working with 6 sources (LENIA, CHLADNI, BIOELECTRIC, NS26, TINYMAPS, VORTEX_DECAY_DEMO)
- 25/25 tests passing, verifier green

### V4 correction pack (commit `0e58b78`)
Senior agent sent correction pack with 20 documents. Key message: "stop building platform, run the experiment."

### V4 P0 work (commit `832eafc`)
- Split OPEN_BLIND from HUMAN_OPEN_ENDED (lineage_channel column)
- Strict control_surface mode (LegacySourceError)
- VORTEX marked SYNTHETIC_TEST_FIXTURE
- Playwright p5.js execution harness (`reproduce_seed.cjs`)
- B25_UNBIASED + B25_REFERENCE seed manifests
- AST literal-role classifier (`classify_literals.py` — later replaced)

### V4 dashboard (commits `2ed89d1`, `f9ed669`)
- Received v4-human-aesthetic-dashboard.zip from senior agent
- Integrated into `v4-dashboard/`
- Wired to real MathArtist API (no synthetic data)
- Real renderers loaded from `app/static/js/sources/`
- `/api/branch`, `/api/root` endpoints added
- POTENTIAL/SAVED/LINEAGE tabs wired to real events

### BLOCKERS.md (commit `248034f`)
Honest assessment of drift. Five blockers identified.

### V5 rescue pack (commit `4807102`)
Senior agent sent rescue pack with 42 files. Key message: "finish the real emergence experiment."

### V5 tools (commit `a0d7163`)
- Installed Acorn AST parser
- Replaced regex classifier with `classify_literals_ast.mjs` (real AST via Acorn)
- Copied `render_batch.cjs` (persistent Chromium batch renderer)
- Copied `run_b25_v5.py` (real Sobol via scipy, SHA-derived seeds)
- 3-seed proof: 300 specimens, 3 families, visually verified

### B25_FERTILE (commit `ca05ed4`)
- Probed all 994 corpus seeds with AST classifier
- 973/994 have >=3 mutation candidates
- Built B25_FERTILE: 25 seeds with 3-8 admitted controls each
- 25×10 smoke test: 250 specimens, 242 ok, contact sheet built

### NS26 restored (commit `0535f45`)
- NS26 restored as primary source with mutable h/tau/twist/etaFreq
- Renderer uses v1 math with live scientific parameters
- Dashboard default switched to NS26
- Status changed from DERIVED to ART_PROGRAM

## Current state

### What works
- Server: `http://127.0.0.1:8765` with all endpoints
- Dashboard: `http://127.0.0.1:8765/v4/` (V4 human aesthetic dashboard)
- NS26: mutable h/tau/twist/etaFreq producing real plume/vortex structures
- AST classifier: finds 7-27 candidates per corpus seed
- Batch renderer: persistent Chromium, 300 specimens in ~5 minutes
- B25_FERTILE: 25 seeds with admitted controls
- 678 total specimens rendered across all runs

### What's not done
- 25×1000 full benchmark (only 25×10 done)
- Morphology coverage atlas
- Dashboard wired to NS26 run output
- V5_RESULTS.md
- Integration of NS26 as a B25_FERTILE seed (it's a separate source, not in the corpus)

### Key files
- `specs/NS26.json` — the real control surface (h, tau, twist, etaFreq, density, trail, exposure)
- `app/static/js/sources/ns26.js` — v1 math renderer with mutable parameters
- `tools/classify_literals_ast.mjs` — Acorn AST literal classifier
- `tools/run_b25_v5.py` — batch orchestrator with real Sobol
- `tools/render_batch.cjs` — persistent Chromium renderer
- `seeds/B25_FERTILE.json` — 25 fertile corpus seeds
- `v4-dashboard/` — human aesthetic dashboard
- `docs/BLOCKERS.md` — honest assessment of what's stuck
- `docs/CONFUSED.md` — 30 open questions for peer review

### How to run
```bash
cd mathartist
# Start server
PYTHONPATH=app python3 -c "from server import main; main()"
# Dashboard at http://127.0.0.1:8765/v4/
# NS26 breeding at http://127.0.0.1:8765/

# Render 25×10 for any source
python3 tools/run_b25_v5.py seeds/B25_FERTILE.json --descendants 10 --out runs/test

# AST classify a sketch
node tools/classify_literals_ast.mjs corpus/tsubuyaki/code/<id>.js

# Render population
node tools/render_population.cjs . population.json outdir 176 '9'
```

## The project's idea (don't lose this again)

NS26 is the primary source. The Navier-Stokes blow-up construction has a similarity scaling with real scientific parameters (h, tau). These enter the equations as power-law exponents. The search space is: what lives in the legitimate parameter space of this mathematical result?

The #つぶやきProcessing corpus was supposed to be a benchmark — prove the pipeline works on simpler creative-math seeds before graduating to real frontier math. Don't let the benchmark become the main event again.

## Git remote
```
origin: https://github.com/prx0r/mxth.git
Token: ask the user for the GitHub token (stored in agent-vault or provided directly)
```

## Dependencies
- Python: numpy, scipy, Pillow, pytest
- Node: playwright, acorn, acorn-loose, acorn-walk, magic-string, skia-canvas
- External: p5.js v1.11.3 (pinned in external/p5.js/)
