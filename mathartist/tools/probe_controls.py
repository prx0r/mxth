#!/usr/bin/env python3
"""Intervention screen for ART_PROGRAM controls.

This is a reference implementation:
- calls real AST classifier
- renders default and +/- perturbation with identical RNG/noise seed
- measures normalized pixel mean absolute difference
- labels candidates EFFECTFUL / NO_EFFECT / BRITTLE
"""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def stable_seed(s): return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4],"big")

def replacement(old,val):
    return str(int(round(val))) if "." not in old.lower() and "e" not in old.lower() else f"{val:.9g}"

def edit(code,c,val):
    return code[:c["start"]]+replacement(c["literal"],val)+code[c["end"]:]

def delta(c):
    v=float(c["value"]);r=c["role"]
    if r=="PHASE":return math.pi/12
    if r=="BRANCH_SELECTOR":return 1.0
    if abs(v)<1e-12:return .1
    return max(abs(v)*.10,.05)

def mad(a,b):
    A=np.asarray(Image.open(a).convert("L").resize((128,128)),dtype=np.float32)/255.
    B=np.asarray(Image.open(b).convert("L").resize((128,128)),dtype=np.float32)/255.
    return float(np.mean(np.abs(A-B)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("code_file");ap.add_argument("--out",default=None)
    ap.add_argument("--max-candidates",type=int,default=32);ap.add_argument("--frame",type=int,default=20)
    a=ap.parse_args();cf=Path(a.code_file);code=cf.read_text(errors="replace")
    cls=subprocess.run(["node",str(ROOT/"tools/classify_literals_ast.mjs"),str(cf)],capture_output=True,text=True,check=True)
    parsed=json.loads(cls.stdout);cands=parsed["candidates"][:a.max_candidates]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);jobs=[];seed=stable_seed(parsed["code_sha256"])
        base_id="default"
        jobs.append({"id":base_id,"code":code,"frame":a.frame,"random_seed":seed,"noise_seed":seed,"mode":"search"})
        for i,c in enumerate(cands):
            d=delta(c);v=float(c["value"])
            jobs.append({"id":f"c{i}-minus","code":edit(code,c,v-d),"frame":a.frame,"random_seed":seed,"noise_seed":seed,"mode":"search"})
            jobs.append({"id":f"c{i}-plus","code":edit(code,c,v+d),"frame":a.frame,"random_seed":seed,"noise_seed":seed,"mode":"search"})
        jf=td/"jobs.jsonl";jf.write_text("\n".join(json.dumps(j) for j in jobs)+"\n")
        imgdir=td/"images"
        r=subprocess.run(["node",str(ROOT/"tools/render_batch.cjs"),str(jf),"--out",str(imgdir),"--workers","2"],capture_output=True,text=True,check=True)
        rendered={x["id"]:x for x in map(json.loads,filter(str.strip,r.stdout.splitlines()))}
        base=rendered[base_id]
        controls=[]
        for i,c in enumerate(cands):
            m=rendered[f"c{i}-minus"];p=rendered[f"c{i}-plus"]
            status="BRITTLE" if not(m.get("ok") and p.get("ok")) else "NO_EFFECT"
            dm=dp=0.0
            if base.get("image_path") and m.get("image_path") and p.get("image_path"):
                dm=mad(base["image_path"],m["image_path"]);dp=mad(base["image_path"],p["image_path"])
                if status!="BRITTLE" and max(dm,dp)>=.01:status="EFFECTFUL"
            cc={**c,"probe":{"status":status,"delta":delta(c),"mad_minus":dm,"mad_plus":dp}}
            if status=="EFFECTFUL":
                v=float(c["value"]);d=max(delta(c)*4,abs(v)*.25,.1)
                cc["id"]=f"L{c.get('line','x')}C{c.get('column','x')}"
                cc["min"]=min(v-d,v+d);cc["max"]=max(v-d,v+d)
                controls.append(cc)
        out={"code_file":str(cf),"code_sha256":parsed["code_sha256"],"parser":parsed["parser"],
             "default_ok":base.get("ok",False),"candidates_probed":len(cands),
             "effectful_controls":len(controls),"controls":controls}
        text=json.dumps(out,indent=2)
        if a.out:Path(a.out).write_text(text)
        print(text)

if __name__=="__main__":main()
