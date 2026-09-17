"""Skeleton evaluator for ShinkaEvolve.
Keep SCIENCE_CORE outside Shinka's mutable task directory. The candidate may alter only interpretation.py.
"""
import hashlib, json, os, pathlib, sys
CORE = pathlib.Path(os.environ.get("MATHARTIST_CORE", "../../specs/NS26.json")).resolve()
EXPECTED = os.environ.get("MATHARTIST_CORE_SHA256")
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if EXPECTED and digest(CORE) != EXPECTED:
    print(json.dumps({"score":-1e9,"error":"immutable core hash changed"})); raise SystemExit(1)
# Replace with controlled-lab / visual-descriptor objective for the current experiment.
score=float(os.environ.get("MATHARTIST_EXTERNAL_SCORE","0"))
print(json.dumps({"score":score,"core_sha256":digest(CORE)}))
