#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys,pathlib,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from archive import init_db,add_event

def emit(pid,typ,val,meta):
    add_event({'phenotype_id':pid,'session_id':'youtube','event_type':typ,'value':float(val),'metadata':meta})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('jsonl');args=ap.parse_args();init_db();n=0
    for line in pathlib.Path(args.jsonl).read_text().splitlines():
        if not line.strip():continue
        x=json.loads(line);pid=x['phenotype_id'];views=max(0,float(x.get('views',0)))
        meta={'environment':'youtube','video_id':x.get('video_id'),'observed_at':x.get('observed_at')}
        # Aggregate YouTube measurements are stored as value-bearing observations rather than
        # faked individual browser events.
        emit(pid,'youtube_views',views,meta)
        for k in ('retention_5','retention_10','retention_20','replay_rate','like_rate','comment_rate','share_rate'):
            if k in x: emit(pid,'youtube_'+k,x[k],meta)
        n+=1
    print(f'imported {n} YouTube metric records')
if __name__=='__main__':main()
