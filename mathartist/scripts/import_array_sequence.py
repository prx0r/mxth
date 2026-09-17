#!/usr/bin/env python3
"""Register an immutable scalar/vector field trajectory as a MathArtist source.

Examples:
  python scripts/import_array_sequence.py vmem.npy --id LEVIN25_VMEM --title "Levin 2025 Vmem" --fps 20
  python scripts/import_array_sequence.py run.npz --array timeseriesVmem --sample 0 --id BIO_VMEM

Accepted arrays after selection: T×H×W, T×H×W×C, or T×N (N must be a square).
The source is globally normalized and quantized to uint8 only for browser display; SHA-256 of the
original file is recorded in the immutable core. Evolution never changes the imported values.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, math, shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--id',required=True);ap.add_argument('--title');ap.add_argument('--description',default='Imported immutable scientific field trajectory.');ap.add_argument('--array');ap.add_argument('--sample',type=int);ap.add_argument('--fps',type=float,default=10);ap.add_argument('--provenance-level',default='EXACT-DATA');ap.add_argument('--channel-names',default='');args=ap.parse_args()
    src=Path(args.input); raw=src.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if src.suffix.lower()=='.npy': a=np.load(src,allow_pickle=False)
    elif src.suffix.lower()=='.npz':
        z=np.load(src,allow_pickle=False); key=args.array or z.files[0]; a=z[key]
    else: raise SystemExit('Use .npy or .npz input')
    a=np.asarray(a)
    # Common simulator shape T×samples×cells×1; opt into sample dimension explicitly.
    if args.sample is not None and a.ndim>=3: a=a[:,args.sample]
    if a.ndim==2:
        T,N=a.shape; side=round(math.sqrt(N));
        if side*side!=N: raise SystemExit(f'T×N input has N={N}, not a square; reshape before import')
        a=a.reshape(T,side,side)
    if a.ndim==3: a=a[...,None]
    if a.ndim!=4: raise SystemExit(f'Expected T×H×W[×C] after selection, got {a.shape}')
    a=np.nan_to_num(a.astype(np.float64)); lo=float(a.min());hi=float(a.max());den=(hi-lo) or 1.0;q=np.clip(np.rint((a-lo)/den*255),0,255).astype(np.uint8)
    T,H,W,C=q.shape; sid=args.id.upper().replace('-','_'); names=[x.strip() for x in args.channel_names.split(',') if x.strip()]
    payload={'schema':'mathartist-arrayseq-v1','id':sid,'frames':T,'height':H,'width':W,'channels':C,'channel_names':names,'fps':args.fps,'source_min':lo,'source_max':hi,'sha256':sha,'data_b64':base64.b64encode(q.tobytes()).decode()}
    out=ROOT/'app/static/data/imported'/f'{sid}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,separators=(',',':')))
    artifact_dir=ROOT/'source_artifacts'/sid;artifact_dir.mkdir(parents=True,exist_ok=True);original=artifact_dir/src.name;shutil.copy2(src,original)
    spec={'id':sid,'short':sid[:12],'title':args.title or sid,'description':args.description,'provenance_level':args.provenance_level,'core_statement':'imported trajectory bytes fixed; observation only evolves','upstream':str(src),'renderer':'array-sequence','immutable_core':{'original_sha256':sha,'shape':list(a.shape),'source_min':lo,'source_max':hi},'source_variants':[{'id':'trajectory-0'}],
      'source_bundle':{'files':[str(out.relative_to(ROOT)),str(original.relative_to(ROOT))]},
      'interpretation_genes':{
       'rotation':{'type':'float','min':-3.1416,'max':3.1416,'default':0,'sigma':.2},'zoom':{'type':'float','min':.55,'max':2.1,'default':1,'sigma':.1},'threshold':{'type':'float','min':0,'max':.85,'default':.08,'sigma':.06},'gamma':{'type':'float','min':.25,'max':3,'default':1,'sigma':.18},'exposure':{'type':'float','min':.2,'max':1,'default':.75,'sigma':.08},'trail':{'type':'float','min':0,'max':.92,'default':.2,'sigma':.08},'sample':{'type':'float','min':.25,'max':1.5,'default':1,'sigma':.12},'point_size':{'type':'float','min':.45,'max':2.4,'default':1,'sigma':.13},'time_rate':{'type':'float','min':.2,'max':2.4,'default':1,'sigma':.12},'contours':{'type':'float','min':1,'max':14,'default':5,'sigma':.7},'channel':{'type':'int','min':0,'max':max(0,C-1),'default':0},'observable':{'type':'enum','values':['field','contour','edge'],'default':'field'}}}
    (ROOT/'specs'/f'{sid}.json').write_text(json.dumps(spec,indent=2));print(f'Registered {sid}: {a.shape} -> {out.relative_to(ROOT)}');print('Restart/reload MathArtist; the source will appear in the selector.')
if __name__=='__main__':main()
