#!/usr/bin/env python3
"""V5 batch orchestrator reference.

Manifest seeds must contain:
- seed_id
- code_file (repo-relative preferred)
- controls: [{id,start,end,value,role,min,max}]

This tool uses a genuine scipy.stats.qmc.Sobol sequence and calls render_batch.cjs
once for the whole seed batch rather than once per specimen.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,subprocess,sys,time
from pathlib import Path

try:
    from scipy.stats import qmc
except Exception as e:
    raise SystemExit("V5 requires scipy for a real Sobol sampler: pip install scipy") from e

ROOT=Path(__file__).resolve().parents[1]

def stable_seed(text:str)->int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:4],"big")

def fmt_like(old:str,val:float)->str:
    low=old.lower()
    if "." not in old and "e" not in low:
        return str(int(round(val)))
    return f"{val:.9g}"

def apply_theta(code:str,controls:list[dict],theta:dict[str,float])->str:
    edits=[]
    byid={str(c.get("id",i)):c for i,c in enumerate(controls)}
    for cid,val in theta.items():
        c=byid[cid];edits.append((int(c["start"]),int(c["end"]),fmt_like(str(c["value"]),float(val))))
    out=code
    for start,end,new in sorted(edits,reverse=True):
        out=out[:start]+new+out[end:]
    return out

def control_bounds(c:dict)->tuple[float,float]:
    if "min" in c and "max" in c:
        return tuple(sorted((float(c["min"]),float(c["max"]))))
    v=float(c["value"]);role=c.get("role","MATHEMATICAL_COEFFICIENT")
    if role=="PHASE": return (v-math.pi,v+math.pi)
    if role=="EXPONENT":
        lo=max(-6.0,v-2.0);hi=min(8.0,v+2.0);return (lo,hi)
    if role=="BRANCH_SELECTOR" and float(v).is_integer(): return (v-3,v+3)
    if abs(v)<1e-12: return (-1.0,1.0)
    if v>0: return (v/3.0,v*3.0)
    return tuple(sorted((v*3.0,v/3.0)))

def variations(seed_id:str,controls:list[dict],count:int)->list[tuple[str,dict]]:
    d=len(controls); s=stable_seed(seed_id); rng=random.Random(s)
    if d==0:return []
    bounds=[control_bounds(c) for c in controls]
    n_global=int(count*.6); n_local=int(count*.3); n_boundary=count-n_global-n_local
    sobol_n=1<<math.ceil(math.log2(max(1,n_global)))
    sampler=qmc.Sobol(d=d,scramble=True,seed=s)
    U=sampler.random_base2(int(math.log2(sobol_n)))[:n_global]
    out=[]
    for row in U:
        th={}
        for i,(c,(lo,hi)) in enumerate(zip(controls,bounds)):
            th[str(c.get("id",i))]=float(lo+row[i]*(hi-lo))
        out.append(("sobol",th))
    for _ in range(n_local):
        th={}
        for i,(c,(lo,hi)) in enumerate(zip(controls,bounds)):
            v=float(c["value"]);sd=max((hi-lo)*.08,1e-12)
            th[str(c.get("id",i))]=max(lo,min(hi,rng.gauss(v,sd)))
        out.append(("local",th))
    for _ in range(n_boundary):
        th={}
        for i,(c,(lo,hi)) in enumerate(zip(controls,bounds)):
            th[str(c.get("id",i))]=rng.choice((lo,hi,(lo+hi)/2))
        out.append(("boundary",th))
    return out[:count]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--descendants",type=int,default=1000)
    ap.add_argument("--run-id",default=None)
    ap.add_argument("--out",default="runs/v5")
    ap.add_argument("--workers",type=int,default=2)
    ap.add_argument("--frame",type=int,default=20)
    ap.add_argument("--resume",action="store_true")
    a=ap.parse_args()
    manifest_path=Path(a.manifest)
    man=json.loads(manifest_path.read_text())
    run_id=a.run_id or time.strftime("v5-%Y%m%d-%H%M%S")
    out=Path(a.out)/run_id;images=out/"images";out.mkdir(parents=True,exist_ok=True);images.mkdir(exist_ok=True)
    jobs_path=out/"jobs.jsonl";meta={}
    existing=set()
    results_path=out/"descendants.jsonl"
    if a.resume and results_path.exists():
        for line in results_path.read_text().splitlines():
            if line.strip():
                try:existing.add(json.loads(line)["specimen_id"])
                except Exception:pass
    jobs=[]
    for seed in man["seeds"]:
        sid=seed["seed_id"];controls=seed.get("controls") or seed.get("admitted_controls") or []
        if len(controls)<3:
            print(f"SKIP {sid}: {len(controls)} admitted controls",file=sys.stderr);continue
        cf=Path(seed["code_file"])
        if not cf.is_absolute(): cf=(ROOT/cf).resolve()
        code=cf.read_text(errors="replace")
        source_sha=hashlib.sha256(code.encode()).hexdigest()
        for i,(sampler,theta) in enumerate(variations(sid,controls,a.descendants)):
            specimen=f"{sid}-v5-{i:04d}"
            if specimen in existing:continue
            mutated=apply_theta(code,controls,theta)
            rseed=stable_seed(specimen)
            job={"id":specimen,"code":mutated,"frame":a.frame,"width":400,"height":400,
                 "random_seed":rseed,"noise_seed":rseed,"mode":"search"}
            jobs.append(job)
            meta[specimen]={"specimen_id":specimen,"run_id":run_id,"seed_id":sid,
                "source_code_sha256":source_sha,"parameterization_sha256":hashlib.sha256(
                    json.dumps(controls,sort_keys=True).encode()).hexdigest(),
                "theta":theta,"parent_ids":[],"lineage_channel":"OPEN_BLIND",
                "sampler":sampler,"sampler_index":i,"rng_seed":rseed,"noise_seed":rseed,
                "capture_frame":a.frame,"renderer_mode":"search",
                "mutation_metadata":{"controls":[c.get("id",j) for j,c in enumerate(controls)]}}
    with jobs_path.open("w") as f:
        for j in jobs:f.write(json.dumps(j,ensure_ascii=False)+"\n")
    if not jobs:
        print("no new jobs");return
    cmd=["node",str(ROOT/"tools/render_batch.cjs"),str(jobs_path),"--out",str(images),"--workers",str(a.workers)]
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with results_path.open("a") as fout:
        for line in proc.stdout:
            if not line.strip():continue
            rr=json.loads(line);base=meta[rr["id"]]
            rec={**base,**{
              "technical_status":rr.get("technical_status","crash"),
              "render_sha256":rr.get("render_sha256"),
              "image_path":rr.get("image_path"),
              "execution_ms":rr.get("execution_ms",0),
              "error":rr.get("error")
            }}
            fout.write(json.dumps(rec,ensure_ascii=False)+"\n");fout.flush()
    err=proc.stderr.read();rc=proc.wait()
    if err:print(err,file=sys.stderr)
    if rc:raise SystemExit(rc)
    run_manifest={"run_id":run_id,"source_manifest":str(manifest_path),
                  "source_manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                  "descendants_per_seed":a.descendants,"workers":a.workers,"frame":a.frame,
                  "jobs_this_invocation":len(jobs)}
    (out/"run_manifest.json").write_text(json.dumps(run_manifest,indent=2))
    print(out)

if __name__=="__main__":main()
