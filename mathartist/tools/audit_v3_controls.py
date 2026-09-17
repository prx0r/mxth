#!/usr/bin/env python3
"""V3.1 control-surface audit.

Exercises the actual browser renderer from generated parameter roots and reports only
technical integrity + structural diversity. It is intentionally NOT a beauty/valence score.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, subprocess, sys, tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'app')]
import archive
from aesthetics.descriptors import descriptor, sequence_descriptor
from aesthetics.viability import gate

FEATURES=('symmetry_best','occupancy','bbox_area_ratio','edge_density','spectral_entropy','compressibility')

def structural_nn(records):
    if len(records)<2:return 0.0
    X=np.array([[float(r['frame'][k]) for k in FEATURES] for r in records],dtype=float)
    sd=X.std(0);sd[sd<1e-9]=1;X=(X-X.mean(0))/sd
    D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1));np.fill_diagonal(D,np.inf)
    return float(np.mean(D.min(1)))

def thumb_hash(path):
    a=np.asarray(Image.open(path).convert('L').resize((24,24),Image.Resampling.BILINEAR))
    return hashlib.sha256(a.tobytes()).hexdigest()

def contact(pop,records,frames,out):
    T=176;C=12;header=54;R=math.ceil(len(pop)/C)
    sh=Image.new('RGB',(C*T,header+R*T),(3,3,3));d=ImageDraw.Draw(sh)
    passed=sum(r['integrity']['pass'] for r in records)
    d.text((12,10),f'MATHARTIST CONTROL-SURFACE AUDIT  |  {passed}/{len(records)} TECHNICALLY VALID',fill=(218,218,218))
    d.text((12,29),'not a beauty score · fixed programs, admitted parameters, exact browser renderer',fill=(110,110,110))
    rr={r['id']:r for r in records}
    for i,p in enumerate(pop):
        im=Image.open(frames/p['id']/'t2.png').convert('RGB').resize((T,T))
        x=(i%C)*T;y=header+(i//C)*T;sh.paste(im,(x,y));r=rr[p['id']]
        col=(175,205,175) if r['integrity']['pass'] else (205,100,100)
        d.text((x+4,y+4),p['source_variant'][:10],fill=col)
    sh.save(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='TINYMAPS');ap.add_argument('--count',type=int,default=96);ap.add_argument('--seed',type=int,default=3117);ap.add_argument('--out',default=str(ROOT/'docs/benchmarks/v3.1-controls'));args=ap.parse_args()
    out=Path(args.out);shutil.rmtree(out,ignore_errors=True);out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as td:
        archive.DB=Path(td)/'audit.sqlite3';archive.init_db();pop=archive.create_population(args.source,'frontier',args.count,seed=args.seed)
        (out/'population.json').write_text(json.dumps(pop,indent=2))
        frames=out/'frames';subprocess.run(['node',str(ROOT/'tools/render_population.cjs'),str(ROOT),str(out/'population.json'),str(frames),'176','3,9,17,25'],check=True,cwd=ROOT)
        records=[];by=defaultdict(list);hashes=Counter()
        for p in pop:
            imgs=[frames/p['id']/f't{i}.png' for i in range(4)];ds=[descriptor(x) for x in imgs];seq=sequence_descriptor(imgs);integ=gate(ds[2]);h=thumb_hash(imgs[2]);hashes[h]+=1
            r={'id':p['id'],'source_variant':p['source_variant'],'genome':p['genome'],'frame':ds[2],'sequence':seq,'integrity':integ,'thumbnail_hash':h};records.append(r);by[p['source_variant']].append(r)
        summary={'source':args.source,'n':len(records),'integrity_pass':sum(r['integrity']['pass'] for r in records),'integrity_pass_rate':sum(r['integrity']['pass'] for r in records)/max(1,len(records)),'exact_thumbnail_duplicates':sum(n-1 for n in hashes.values() if n>1),'structural_nn_distance':round(structural_nn(records),4),'by_variant':{},'note':'technical integrity + structural diversity only; not beauty, valence, or rasa'}
        for k,rs in by.items():summary['by_variant'][k]={'n':len(rs),'integrity_pass_rate':round(sum(r['integrity']['pass'] for r in rs)/len(rs),4),'structural_nn_distance':round(structural_nn(rs),4),'temporal_change_mean':round(float(np.mean([r['sequence'].get('change_mean') or 0 for r in rs])),5)}
        (out/'audit.json').write_text(json.dumps({'summary':summary,'records':records},indent=2));contact(pop,records,frames,out/'contact-sheet.png');shutil.rmtree(frames);print(json.dumps(summary,indent=2));print(out/'contact-sheet.png')
if __name__=='__main__':main()
