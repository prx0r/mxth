# Controlled attention experiment
The dashboard already records local first-party events into SQLite:
- `impression`
- `horizon_5`, `horizon_10`, `horizon_20`
- `dwell` milliseconds
- `fullscreen`, `favorite`, `replay`

The 5s/10s/20s tabs rank using conditional survival where possible. This is a controlled-lab substrate,
not a claim that retention equals rasa. Before public experiments: randomize assignment, fix exposure
window and viewport, preregister hypotheses, separate exploratory from confirmatory runs, and record
anonymous session IDs only.

YouTube should be a second, observational environment because recommendation/distribution is a confound.
