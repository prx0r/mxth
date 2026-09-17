#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,collections
from pathlib import Path
REQ={"specimen_id","run_id","seed_id","source_code_sha256","theta","lineage_channel","sampler","sampler_index","renderer_mode","technical_status","execution_ms"}
STAT={"valid","crash","blank","timeout","oom","nan"}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("jsonl");a=ap.parse_args()
    bad=[];counts=collections.Counter();n=0
    for i,line in enumerate(Path(a.jsonl).read_text().splitlines(),1):
        if not line.strip():continue
        n+=1
        try:r=json.loads(line)
        except Exception as e:bad.append((i,f"json: {e}"));continue
        miss=REQ-r.keys()
        if miss:bad.append((i,f"missing {sorted(miss)}"))
        st=r.get("technical_status");counts[st]+=1
        if st not in STAT:bad.append((i,f"bad status {st!r}"))
        if st=="valid" and not (r.get("image_path") or r.get("morphology_vector")):
            bad.append((i,"valid row has neither image_path nor morphology_vector"))
    print(json.dumps({"records":n,"status_counts":dict(counts),"errors":bad[:100],"pass":not bad},indent=2))
    raise SystemExit(1 if bad else 0)
if __name__=="__main__":main()
