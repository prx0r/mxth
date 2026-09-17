#!/usr/bin/env python3
"""High-volume V3.2 discovery sweep.
Generates blindly, renders exact browser output, removes only technical failures,
then keeps a morphology-coverage atlas for human inspection. No beauty signal.
"""
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile,math
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'app')]
import archive
from aesthetics.descriptors import descriptor,sequence_descriptor
from aesthetics.viability import gate
from morphology import novelty,farthest_first,fertility

def sheet(records,frames,out,title):
    T=176;C=12;H=52;R=math.ceil(len(records)/C);im=Image.new('RGB',(C*T,H+R*T),(3,3,3));d=ImageDraw.Draw(im)
    d.text((10,8),title,fill=(220,220,220));d.text((10,27),'machine coverage only · human decides POTENTIAL',fill=(110,110,110))
    for j,r in enumerate(records):
        p=Image.open(frames/r['id']/'t2.png').convert('RGB').resize((T,T));x=j%C*T;y=H+j//C*T;im.paste(p,(x,y));d.text((x+4,y+4),f"{r['source_variant'][:9]} n={r.get('novelty',0):.1f}",fill=(170,190,170))
    im.save(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='TINYMAPS');ap.add_argument('--count',type=int,default=512);ap.add_argument('--keep',type=int,default=96);ap.add_argument('--seed',type=int,default=3201);ap.add_argument('--out',default=str(ROOT/'docs/benchmarks/v3.2-discovery'));a=ap.parse_args()
    out=Path(a.out);shutil.rmtree(out,ignore_errors=True);out.mkdir(parents=True);frames=out/'frames'
    with tempfile.TemporaryDirectory() as td:
        archive.DB=Path(td)/'d.sqlite3';archive.init_db();pop=archive.create_population(a.source,'frontier',a.count,seed=a.seed)
        (out/'population.json').write_text(json.dumps(pop,indent=2))
        subprocess.run(['node',str(ROOT/'tools/render_population.cjs'),str(ROOT),str(out/'population.json'),str(frames),'176','3,9,17,25'],check=True,cwd=ROOT)
        rec=[]
        for p in pop:
            img=frames/p['id']/'t2.png'; d=descriptor(img); integ=gate(d); rec.append({'id':p['id'],'source_variant':p['source_variant'],'genome':p['genome'],'frame':d,'integrity':integ})
        ns=novelty(rec)
        for r,n in zip(rec,ns):r['novelty']=float(n)
        valid=[r for r in rec if r['integrity']['pass']]
        # seed with most novel specimen, then max-min cover morphology space
        seed_idx=max(range(len(valid)),key=lambda i:valid[i]['novelty']) if valid else 0
        idx=farthest_first(valid,min(a.keep,len(valid)),seed_idx); atlas=[valid[i] for i in idx]
        summary={'source':a.source,'generated':len(rec),'technically_valid':len(valid),'kept_for_human_review':len(atlas),'fertility':fertility(rec),'principle':'blind volume -> technical gate -> morphology coverage -> human POTENTIAL; no beauty/attention/valence/rasa optimization'}
        (out/'audit.json').write_text(json.dumps({'summary':summary,'records':rec,'atlas_ids':[r['id'] for r in atlas]},indent=2))
        (out/'human-review.json').write_text(json.dumps([{'id':r['id'],'source_variant':r['source_variant'],'genome':r['genome'],'potential':None,'notes':''} for r in atlas],indent=2))
        sheet(atlas,frames,out/'contact-sheet.png',f'MATHARTIST V3.2 DISCOVERY · {len(rec)} BLIND SAMPLES -> {len(atlas)} COVERAGE PICKS')
        shutil.rmtree(frames);print(json.dumps(summary,indent=2));print(out/'contact-sheet.png')
if __name__=='__main__':main()
