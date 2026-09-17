from __future__ import annotations
import math

SAFE_ROLES={"family","initial_condition","boundary_condition","phase","time","scale","seed","branch","sampling","numerical","observation"}


def surface_for_spec(spec, variant=None):
    """Return the admitted V3 control surface.

    V3.1 supports variant-specific surfaces so one source can expose several fixed
    mathematical programs without pretending they share the same free variables.
    Legacy V2 interpretation genes remain a compatibility fallback only.
    """
    if variant and spec.get("control_surfaces"):
        return spec["control_surfaces"].get(variant, {})
    if spec.get("control_surface"):
        return spec["control_surface"]
    if spec.get("control_surfaces"):
        # Without a chosen variant there is no honest merged surface.
        return {}
    return spec.get("interpretation_genes",{})


def validate_control_surface(spec):
    errors=[]
    surfaces=[]
    if spec.get("control_surface"):
        surfaces=[("*",spec["control_surface"])]
    elif spec.get("control_surfaces"):
        declared={v["id"] for v in spec.get("source_variants",[])}
        missing=declared-set(spec["control_surfaces"])
        extra=set(spec["control_surfaces"])-declared
        for v in sorted(missing): errors.append(f"{v}: missing control surface")
        for v in sorted(extra): errors.append(f"{v}: control surface has no source variant")
        surfaces=list(spec["control_surfaces"].items())
    else:
        return errors  # legacy compatibility source
    for variant,surface in surfaces:
        for name,d in surface.items():
            prefix=f"{variant}/{name}" if variant!="*" else name
            if d.get("type") not in {"float","int","enum"}: errors.append(f"{prefix}: unsupported type")
            if not d.get("provenance"): errors.append(f"{prefix}: missing provenance")
            if d.get("role") not in SAFE_ROLES: errors.append(f"{prefix}: invalid role")
            if d.get("claim_scope") not in {"same-family","observation-only","numerical-only"}: errors.append(f"{prefix}: invalid claim_scope")
            if d.get("type") in {"float","int"}:
                if "min" not in d or "max" not in d: errors.append(f"{prefix}: missing bounds")
                elif d["min"]>d["max"]: errors.append(f"{prefix}: invalid bounds")
            if d.get("type")=="enum" and not d.get("values"): errors.append(f"{prefix}: empty enum")
    return errors


def _clamp(x,lo,hi): return max(lo,min(hi,x))


def _sample_one(d,rng):
    typ=d["type"]
    if typ=="enum":
        vals=d["values"]; default=d.get("default")
        return default if default in vals and rng.random()<.35 else rng.choice(vals)
    lo,hi=d["min"],d["max"]
    default=d.get("default",(lo+hi)/2)
    explore=float(d.get("root_explore",.42))
    if d.get("mutation")=="log" and lo>0:
        return math.exp(rng.uniform(math.log(lo),math.log(hi))) if rng.random()<explore else _clamp(default*math.exp(rng.gauss(0,d.get("sigma",.18))),lo,hi)
    if typ=="int": return rng.randint(int(lo),int(hi)) if rng.random()<explore else int(_clamp(round(default+rng.gauss(0,d.get("sigma",1))),lo,hi))
    return rng.uniform(lo,hi) if rng.random()<explore else _clamp(default+rng.gauss(0,d.get("sigma",(hi-lo)*.12)),lo,hi)


def random_controls(spec,rng,variant=None):
    return {k:_sample_one(d,rng) for k,d in surface_for_spec(spec,variant).items()}


def mutate_controls(spec,parent,rng,strength=1.0,variant=None):
    surface=surface_for_spec(spec,variant); g=dict(parent); touched=0
    for name,d in surface.items():
        if rng.random()>min(.92,float(d.get("mutation_rate",.28))*strength): continue
        touched+=1; typ=d["type"]
        if typ=="enum":
            vals=[v for v in d["values"] if v!=g.get(name)]
            if vals:g[name]=rng.choice(vals)
        elif typ=="int":
            step=max(1,int(round(d.get("step",1)*strength)))
            g[name]=int(_clamp(int(g.get(name,d.get("default",d["min"])))+rng.choice([-step,step]),d["min"],d["max"]))
        elif d.get("mutation")=="log" and d["min"]>0:
            g[name]=_clamp(float(g.get(name,d.get("default",d["min"]))) * math.exp(rng.gauss(0,d.get("sigma",.15)*strength)),d["min"],d["max"])
        else:
            g[name]=_clamp(float(g.get(name,d.get("default",0)))+rng.gauss(0,d.get("sigma",(d["max"]-d["min"])*.08)*strength),d["min"],d["max"])
    if not touched and surface:
        name=rng.choice(list(surface)); d=surface[name]; g[name]=_sample_one(d,rng)
    # Remove stale controls if a caller supplied a genome from another variant/version.
    return {k:g[k] for k in surface if k in g}
