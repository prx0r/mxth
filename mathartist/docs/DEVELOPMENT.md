# Development map

Start here when continuing development from this ZIP.

## Runtime
- `app/server.py` — dependency-free HTTP/API server.
- `app/archive.py` — SQLite archive, lineage, event fitness and interpretation evolution.
- `app/static/` — specimen-grid dashboard and browser renderers.
- `specs/*.json` — immutable-source contract + allowed interpretation genome.
- `app/static/data/` — deterministic source trajectories.

## Scientific source layer
- `tools/generate_trajectories.py` — reproducibly regenerates Lenia and bioelectric trajectories.
- `scripts/import_array_sequence.py` — generic route for a new paper/model/experiment.
- `third_party/` — license/provenance notes for adapted upstream work.

## Search layer
- built-in archive evolution is deliberately small and inspectable.
- `integrations/pyribs/` is the QD/MAP-Elites replacement when scaling search.
- `integrations/shinka/` uses ShinkaEvolve only for interpretation-program evolution and protects the scientific core by hash.
- Sakana/Picbreeder-VLM is a design reference for archive sampling, phylogeny and stepping-stone preservation; CPPNs are not used as the genotype.

## Paper ingestion
- `integrations/paper2agent/` defines the handoff from Paper2Agent to MathArtist.
- The preferred new-source path is executable paper -> immutable observable trajectory -> generic source adapter.

## Experiment layer
- browser emits impression, 5/10/20 s survival, dwell, fullscreen, favorite and replay events.
- `integrations/youtube/` imports external YouTube attention measurements without confusing them with controlled-lab data.
- `experiments/` contains the current hypotheses / interpretation discipline.

## Immediate next upgrades
1. Run the authors' ElectricMorphogenesis pretrained models and import their genuine Vmem/eV trajectories.
2. Add tetrahedral/Laplacian-eigenmode observation operators as interpretations, not changes to source dynamics.
3. Add temporal recurrence and spectral concentration descriptors.
4. Replace browser mutation with pyribs for large offline sweeps; keep the same specs and archive schema.
5. Use Paper2Agent to add frontier papers automatically.
