#!/usr/bin/env python3
"""Render an exact-browser specimen audit and measure presentation viability.

This is a development benchmark, not a beauty metric. It checks whether the house grammar has
reduced blank/tiny/clipped/full-frame outputs while preserving morphological diversity.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'));sys.path.insert(0,str(ROOT))
from archive import init_db,create_population
from aesthetics.descriptors import descriptor,sequence_descriptor
from aesthetics.viability import gate

SOURCES=['BIOELECTRIC','LENIA','CHLADNI','NS26']

def make_population(count,seed,tmpdb):
    os.environ['MATHARTIST_DB']=str(tmpdb)
    # archive module's DB constant is import-time; override it directly for the isolated audit.
    import archive;archive.DB=Path(tmpdb);init_db()
    out=[]
    for i,sid in enumerate(SOURCES):out.extend(create_population(sid,'frontier',count,seed=seed+i*10007))
    return out

def contact(pop,frames,records,out):
    tile=192;cols=12;header=52
    rows=(len(pop)+cols-1)//cols
    sh=Image.new('RGB',(cols*tile,header+rows*tile),(3,4,4));d=ImageDraw.Draw(sh)
    passed=sum(1 for r in records if r['viability']['pass'])
    d.text((12,10),f'MATHARTIST V2.1 / EXACT RUNTIME AUDIT  |  {passed}/{len(records)} PASS SPECIMEN GRAMMAR',fill=(205,210,208))
    d.text((12,29),'house grammar = viability only; not a beauty score or valence model',fill=(77,82,80))
    rec={r['id']:r for r in records}
    for i,p in enumerate(pop):
        im=Image.open(frames/p['id']/'t2.png').convert('RGB').resize((tile,tile))
        x=(i%cols)*tile;y=header+(i//cols)*tile;sh.paste(im,(x,y))
        rr=rec[p['id']];col=(195,205,200) if rr['viability']['pass'] else (92,62,62)
        d.text((x+5,y+5),p['source_id'][:4],fill=col)
    sh.save(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--count',type=int,default=24);ap.add_argument('--seed',type=int,default=2101);ap.add_argument('--out',default=str(ROOT/'docs/benchmarks/v2.1-audit'));args=ap.parse_args()
    out=Path(args.out);shutil.rmtree(out,ignore_errors=True);out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as td:
        pop=make_population(args.count,args.seed,Path(td)/'audit.sqlite3')
        popfile=out/'population.json';popfile.write_text(json.dumps(pop,indent=2))
        frames=out/'frames'
        cmd=['node',str(ROOT/'tools/render_population.cjs'),str(ROOT),str(popfile),str(frames),'192','3,9,17,25']
        subprocess.run(cmd,check=True,cwd=ROOT)
        records=[]
        for p in pop:
            imgs=[frames/p['id']/f't{i}.png' for i in range(4)]
            ds=[descriptor(x) for x in imgs];seq=sequence_descriptor(imgs);vi=gate(ds[2])
            records.append({'id':p['id'],'source_id':p['source_id'],'source_variant':p['source_variant'],'genome':p['genome'],'frame':ds[2],'sequence':seq,'viability':vi})
        reasons=Counter(r for z in records for r in z['viability']['reasons'])
        by=defaultdict(lambda:{'n':0,'pass':0})
        for z in records:by[z['source_id']]['n']+=1;by[z['source_id']]['pass']+=int(z['viability']['pass'])
        summary={'n':len(records),'pass':sum(x['viability']['pass'] for x in records),'pass_rate':sum(x['viability']['pass'] for x in records)/len(records),
                 'by_source':{k:{**v,'pass_rate':v['pass']/v['n']} for k,v in by.items()},'reject_reasons':dict(reasons),
                 'note':'development viability audit using exact JS renderers; not a beauty/valence score'}
        (out/'audit.json').write_text(json.dumps({'summary':summary,'records':records},indent=2))
        contact(pop,frames,records,out/'contact-sheet.png')
        # Avoid shipping hundreds of generated frames; keep the reproducible population, audit and sheet.
        shutil.rmtree(frames)
        print(json.dumps(summary,indent=2));print(out/'contact-sheet.png')
if __name__=='__main__':main()
