# BETSE bridge
Upstream: https://github.com/betsee/betse (BSD-2-Clause)
BETSE is a real 2D bioelectric tissue simulator associated with Alexis Pietak / Michael Levin work.
Recommended workflow: run BETSE externally, export Vmem/current/concentration arrays, ingest snapshots
as immutable source state. Never evolve BETSE's biological parameters in the interpretation search.
