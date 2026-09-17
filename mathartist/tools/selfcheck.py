#!/usr/bin/env python3
from __future__ import annotations
import json, pathlib, subprocess, sys, time, urllib.request, urllib.parse, os, signal
ROOT=pathlib.Path(__file__).resolve().parents[1]
PORT=8879

def get(path):
    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}{path}',timeout=6) as r:return r.status,r.read(),r.headers.get_content_type()
def post(path,obj):
    req=urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=json.dumps(obj).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=6) as r:return r.status,json.loads(r.read())

def main():
    env=os.environ.copy();env['MATHARTIST_DB']=str(ROOT/'data'/'selfcheck.sqlite3')
    for q in [ROOT/'data'/'selfcheck.sqlite3',ROOT/'data'/'selfcheck.sqlite3-wal',ROOT/'data'/'selfcheck.sqlite3-shm']:
        q.unlink(missing_ok=True)
    p=subprocess.Popen([sys.executable,str(ROOT/'app/server.py'),str(PORT)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        for _ in range(40):
            try:
                s,b,_=get('/api/health')
                if s==200:break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('server did not start')
        s,b,_=get('/api/sources');sources=json.loads(b);assert len(sources)>=4
        s,b,_=get('/api/population?source=LENIA&mode=frontier&count=16&session=selfcheck');pop=json.loads(b);assert len(pop)>=12
        s,study=post('/api/event',{'phenotype_id':pop[0]['id'],'session_id':'selfcheck','event_type':'impression','value':1,'metadata':{'environment':'selfcheck'}});assert study['ok']
        s,b,_=get('/api/study?source=BIOELECTRIC&count=12&session=selfcheck&study=smoke');study=json.loads(b);assert len(study)==12 and all('study_arm' in x for x in study)
        s,kids=post('/api/evolve',{'source_id':'LENIA','mode':'open','count':8,'selected_ids':[pop[0]['id']],'session_id':'selfcheck','seed':11});assert len(kids)==8 and all(k['source_variant']==pop[0]['source_variant'] for k in kids)
        s,b,ct=get('/');assert s==200 and ct=='text/html' and b'MATHARTIST' in b
        s,b,ct=get('/js/app.js');assert s==200 and b'first-party-lab' in b
        s,b,ct=get('/data/lenia/orbium.u8.bin');assert s==200 and len(b)>10000
        print(json.dumps({'ok':True,'sources':len(sources),'population':len(pop),'study':len(study),'children':len(kids)},indent=2))
    finally:
        p.terminate()
        try:p.wait(timeout=3)
        except: p.kill()
        for q in [ROOT/'data'/'selfcheck.sqlite3',ROOT/'data'/'selfcheck.sqlite3-wal',ROOT/'data'/'selfcheck.sqlite3-shm']:
            q.unlink(missing_ok=True)
if __name__=='__main__':main()
