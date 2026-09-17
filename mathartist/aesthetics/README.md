# Aesthetics measurement layer

This package deliberately separates three concepts:

1. **SpecimenGrammar** — a source-agnostic viability/presentation gate (blank, clipped, overexposed, etc.).
2. **Structural descriptors** — symmetry-group similarity, spectral entropy, recurrence, compression and motion/change measurements.
3. **Human outcomes** — attention, liking, valence, arousal, absorption, replay and retrospective rasa labels.

No structural descriptor is named or treated as `beauty`. QRI/STV-inspired metrics are candidate predictors. Abhinavagupta-inspired constructs motivate experimental contrasts; they are not reduced to dashboard telemetry.

`descriptors.py` can analyze one image or a frame sequence. `specimen_grammar.v1.json` is versioned so changes to curation rules are auditable.
