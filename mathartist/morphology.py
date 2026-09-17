"""Morphology-only coverage utilities. No beauty, attention, valence or rasa signal."""
from __future__ import annotations
import numpy as np
FEATURES=("symmetry_best","occupancy","bbox_area_ratio","edge_density","spectral_entropy","compressibility","centroid_offset","contrast")

def matrix(records):
    X=np.asarray([[float(r.get("frame",{}).get(k,0) or 0) for k in FEATURES] for r in records],dtype=float)
    if not len(X): return X
    med=np.median(X,axis=0); mad=np.median(np.abs(X-med),axis=0); mad[mad<1e-8]=1.0
    return (X-med)/mad

def novelty(records):
    X=matrix(records)
    if len(X)<2:return [0.0]*len(X)
    D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1));np.fill_diagonal(D,np.inf)
    return D.min(1).tolist()

def farthest_first(records,k,seed_index=0):
    """Deterministic morphology coverage subset; never reads human events."""
    X=matrix(records); n=len(X)
    if not n:return []
    k=min(max(1,int(k)),n); chosen=[seed_index%n]
    mind=np.full(n,np.inf)
    for _ in range(1,k):
        d=np.sqrt(((X-X[chosen[-1]])**2).sum(1));mind=np.minimum(mind,d);mind[chosen]=-1
        chosen.append(int(np.argmax(mind)))
    return chosen

def fertility(records,variant_key="source_variant"):
    """Coverage proxy per frozen seed variant: median NN novelty + valid fraction."""
    out={}
    for v in sorted({r.get(variant_key) for r in records}):
        rs=[r for r in records if r.get(variant_key)==v]; ns=novelty(rs)
        valid=np.mean([bool(r.get("integrity",{}).get("pass")) for r in rs]) if rs else 0
        out[v]={"n":len(rs),"valid_fraction":float(valid),"median_local_novelty":float(np.median(ns)) if ns else 0.0,"p90_local_novelty":float(np.quantile(ns,.9)) if ns else 0.0}
    return out
