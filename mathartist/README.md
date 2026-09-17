# MathArtist Suite V3.3 — search the controls, not the renderer

V3 treats a mathematical/scientific source as an executable family `M(theta)`. The main evolutionary genome is the **evidenced control surface `theta` already admitted by the source**: parameters, initial/boundary conditions, phases, seeds, branches and time. The hot loop deliberately does not invent equations.

```text
paper / proof / code / model
          |
          v
AI-assisted ingestion: what can legitimately vary?
          | evidence for every control
          v
     freeze M(theta)
          |
          v
 dumb stochastic search over theta
          |
          v
 minimal native observation
          |
   +------+------+----------------+
   |             |                |
 OPEN        human LAB       YouTube WILD
 novelty     attention        replication
 fertility  valence
            absorption/rasa
```

The key scientific rule is simple: **source equations/code remain immutable; V3 explores admitted controls rather than manufacturing an aesthetic transformation pipeline.** Legacy V2 observation genomes still run through a compatibility fallback while sources are upgraded. V3.1 includes the first fully native end-to-end family, `TINYMAPS`, with four fixed compact mathematical programs and variant-specific provenance-backed control surfaces.

See `docs/V3_THESIS.md`, `docs/DOMAIN_ADAPTERS_V3.md`, and `controlsurface/README.md`.

## Run

```bash
./run.sh
# http://127.0.0.1:8765
```

Core runtime requires only Python 3 and a modern browser. Optional research integrations are isolated.

## What V2/V2.1 adds

### 1. SourceBundle immutability

V1 hashed immutable metadata. V2 hashes the actual files that causally define each source variant: trajectory bytes, runtime/renderer source, licenses/provenance and pinned upstream commit metadata.

```bash
make bundles
```

Manifests live in `bundles/`. A descendant cannot silently continue if the bundle hash changed.

### 2. Real paper -> MathArtist handoff

Use upstream Paper2Agent to generate/verify a scientific agent, then:

```bash
python -m paper2artist.cli inspect /path/to/project-agent --out inspection.json
python -m paper2artist.cli register paper2artist-manifest.json
```

`paper2artist` fingerprints the delivered agent, discovers MCP-facing functions, copies exported scientific arrays into immutable source artifacts and registers them with the generic renderer. See `paper2artist/README.md`.

### 3. Open-ended archive search without taste leakage

OPEN mode is blind to favorites, dwell, fullscreen, retention, valence and rasa. It mixes recency, branch fertility, control-space diversity and random stepping stones, with explicit fresh-root injection. Human response is isolated to FOR YOU / attention / valence / rasa lineages.

Actual Sakana `ShinkaEvolve` remains an **optional program-level backend** for evolving observation code under a source-hash verifier; continuous parameters stay cheaper in the local archive / optional pyribs backend.

### 4. Formal human-aesthetics experiment layer

The first-party LAB records attention separately from:

- valence
- arousal
- absorption
- favorite/replay/return behavior
- retrospective rasa-category response

The UI does not reveal rasa categories until the viewer elects to respond after viewing. These are measurements/hypotheses, never optimizer definitions of beauty.

Experiment definitions are versioned JSON in `experiments/registry/`.

### 5. YouTube as wild feedback

YouTube is treated as observational ecological replication, not randomized evidence.

```bash
pip install -r requirements-research.txt
export MATHARTIST_YOUTUBE_CLIENT_SECRET=/secure/client_secret.json
python integrations/youtube/youtube_worker.py auth
python integrations/youtube/youtube_worker.py upload organism.mp4 --phenotype PHENOTYPE_ID
python integrations/youtube/youtube_worker.py sync VIDEO_ID --start 2026-09-01 --end 2026-09-30
```

Retention is decomposed into 5-second attention, 10|5 and 20|10 conditional holding, plus replay-area. It is never labelled as rasa.

### 6. Canonical video export

Install Node helper once:

```bash
npm install
python tools/render_video.py PHENOTYPE_ID --out organism.mp4 --seconds 30 --fps 10
```

This imports the same JS source renderers used by the dashboard via `skia-canvas`, then encodes with ffmpeg.

### 7. Technical integrity gate (V3.1)

The old V2.1 house-composition gate is retained only as history. V3.1 uses `integrity-gate-v3.1`, which rejects blank/flat/overexposed observations but does not penalize full-frame occupancy, asymmetry, off-center composition, or unusual edge density. Discovery should not inherit our aesthetic taste.

### 8. Structural aesthetics descriptors (V2.1)

`aesthetics/` computes approximate D4 symmetry, symmetry dynamics, spectral entropy, compressibility, recurrence and temporal-change descriptors. Browser equivalents are stored beside study events. These are QRI/STV-inspired hypothesis coordinates, never definitions of beauty, rasa or valence.

### 9. Abhinavagupta-inspired commonization experiment (V2.1)

`commonization-v1` randomizes the identical phenotype between PARTICULAR (scientific identity visible) and COMMONIZED (source/provenance withheld until after response). It measures attention, replay, liking, valence, arousal, absorption and retrospective rasa-category response. This is an operational analogy to sadharanikarana/commonization, not a direct measurement of the classical construct.

### 10. Improved scientific visual grammar (V2.1)

Lenia now auto-centers/scales its living support and supports temporal layers, contours and edges. Bioelectricity adds streamlines, equipotential contours, field vectors and tetrahedral/simplex-style projection while leaving frozen source trajectories unchanged.

## Current built-in mathematical/scientific families

- `TINYMAPS` — V3.1-native compact mathematical maps; four fixed programs with provenance-backed variant control surfaces and a minimal point observer.
- `LENIA` — exact reference Orbium runtime/trajectory.
- `CHLADNI` — actual Chladni/Bessel eigenmode mathematics.
- `BIOELECTRIC` — equation-level Manicka–Levin cellular-field reimplementation with fixed trajectories.
- `NS26` — intentionally labelled **DERIVED** until replaced by a fuller executable paper adapter.

## Add frontier mathematics

Preferred pipeline:

```text
paper + supplements + repo
        -> Paper2Agent
        -> verified MCP/skill workflow
        -> execute genuine paper observable
        -> export .npy/.npz trajectory/state sequence
        -> paper2artist register
        -> SourceBundle hash
        -> OPEN search / LAB study / YouTube replication
```

If a paper has no executable implementation, register it honestly as `EXACT-EQUATIONS` after an independently validated implementation, or `DERIVED` if only a mechanism/ratio is being represented.

For a direct numerical trajectory without Paper2Agent:

```bash
python scripts/import_array_sequence.py run.npy --id PAPER26_FIELD --title "Paper 2026 / field"
```

## Continue development

Start with **`docs/CONTINUE_HERE.md`**. It defines the interfaces future ZIPs should extend rather than replace.

## Verification

```bash
pytest -q
python scripts/verify_suite.py
python tools/audit_v3_controls.py --count 96 --seed 3131
```

The control audit uses the exact browser source renderer and reports only technical integrity and structural diversity; it is not a beauty score.

The package is designed so each later ZIP can copy this repository forward, add migrations/adapters/tests, and retain all prior source lineages and experiment data.

## V3.2: dumb discovery at volume

The default creative division of labor is now explicit: the machine blindly explores admitted parameter spaces at high volume; it may use technical validity and morphology coverage to avoid wasting review bandwidth, but it does not optimize beauty. The human marks **POTENTIAL**. See `docs/V3_2_DISCOVERY.md` and run `python tools/discover_at_volume.py --count 512 --keep 96`.
