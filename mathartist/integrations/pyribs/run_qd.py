import json, pathlib, sys
try:
    import numpy as np
    from ribs.archives import GridArchive
    from ribs.emitters import EvolutionStrategyEmitter
    from ribs.schedulers import Scheduler
except ImportError:
    raise SystemExit("Install optional research deps: pip install ribs numpy")
# Generic interpretation vector order. In a real run, read bounds from specs/*.json.
archive=GridArchive(solution_dim=6,dims=[32,32],ranges=[(0,1),(0,1)])
emitters=[EvolutionStrategyEmitter(archive,np.full(6,.5),sigma0=.12) for _ in range(4)]
scheduler=Scheduler(archive,emitters)
print("pyribs QD backend ready; connect evaluate(solution)->objective, measures")
