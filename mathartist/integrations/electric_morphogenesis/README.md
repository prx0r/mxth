# ElectricMorphogenesis / Michael Levin biology source

Upstream: https://github.com/santamanicka/ElectricMorphogenesis
Paper: Manicka & Levin (2025), *Field-mediated bioelectric basis of morphogenetic prepatterning*.

## Working in this suite now
`tools/generate_trajectories.py` contains an independent NumPy implementation of the repository's
published/documented cellular-field equations and default physical parameters:

- voltage-gated hyperpolarizing/depolarizing channel currents,
- voltage-gated gap-junction conductance,
- gap-junction current through the lattice,
- charge `Q=C·Vmem`,
- screened Coulomb-like extracellular field,
- field feedback into ion-channel conductance.

It generates three fixed 11×11 source trajectories used by the browser:
`center-hyperpolarized`, `french-flag`, and `uniform-bistable`.

These are labeled **EXACT-EQUATIONS**, not exact reproductions of a trained paper figure. The authors'
pretrained learned-clamp files are PyTorch pickles and are not bundled here. The next fidelity upgrade is
to run the pinned upstream revision directly and import its genuine `timeseriesVmem` / `timeserieseV`
arrays with `scripts/import_array_sequence.py`.

Interpretation evolution never changes the electrical parameters or initial condition within a lineage.
