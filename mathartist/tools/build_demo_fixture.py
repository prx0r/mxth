#!/usr/bin/env python3
from pathlib import Path
import json, random, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import archive
specs=archive.load_specs();rng=random.Random(260917)
sources=[{k:v for k,v in s.items() if k!='interpretation_genes'} for s in specs.values()]
pop=[]
for sid,s in specs.items():
    for i in range(72):
        variant=rng.choice(s['source_variants'])['id'];g=archive.random_genome(s,rng)
        pop.append({'id':f'{sid.lower()}-demo-{i:03d}','source_id':sid,'source_variant':variant,'generation':0,'parent_ids':[],
                    'genome':g,'mode':'frontier','created_at':0})
out=ROOT/'app'/'static'/'data';out.mkdir(parents=True,exist_ok=True)
(out/'sources.json').write_text(json.dumps(sources,separators=(',',':')))
(out/'demo-population.json').write_text(json.dumps(pop,separators=(',',':')))
print('wrote',len(pop),'demo phenotypes')
