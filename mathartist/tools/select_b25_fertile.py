#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib
from collections import defaultdict
from pathlib import Path

def stable_key(x): return hashlib.sha256(x["seed_id"].encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("probe_jsonl")
    ap.add_argument("--out",default="seeds/B25_FERTILE.json")
    ap.add_argument("--count",type=int,default=25)
    ap.add_argument("--min-controls",type=int,default=3)
    ap.add_argument("--max-render-ms",type=float,default=5000)
    ap.add_argument("--max-per-artist",type=int,default=4)
    a=ap.parse_args()
    rows=[json.loads(x) for x in Path(a.probe_jsonl).read_text().splitlines() if x.strip()]
    eligible=[r for r in rows if r.get("reproduce_ok") and r.get("render_nonblank",True)
              and int(r.get("candidate_count",0))>=a.min_controls
              and not r.get("unsupported",False)
              and float(r.get("median_render_ms",0) or 0)<=a.max_render_ms]
    eligible.sort(key=stable_key)
    by=defaultdict(list)
    for r in eligible: by[r.get("mechanism_class") or "unknown"].append(r)
    selected=[];ac=defaultdict(int);mechs=sorted(by)
    while len(selected)<a.count:
        progressed=False
        for mech in mechs:
            while by[mech]:
                r=by[mech].pop(0); artist=r.get("artist") or "unknown"
                if ac[artist]>=a.max_per_artist: continue
                selected.append(r);ac[artist]+=1;progressed=True;break
            if len(selected)>=a.count: break
        if not progressed: break
    if len(selected)<a.count:
        raise SystemExit(f"only {len(selected)} eligible seeds; probe more corpus rows instead of lowering integrity gates")
    out={"id":"B25_FERTILE","selection":"eligibility then deterministic stratified round-robin; no aesthetic ranking",
         "eligibility":{"reproduce_ok":True,"min_effectful_controls":a.min_controls,
                        "max_median_render_ms":a.max_render_ms,"unsupported":False},
         "seeds":selected[:a.count]}
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False))
    print(p)

if __name__=="__main__": main()
