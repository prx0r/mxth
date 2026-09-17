#!/usr/bin/env python3
"""Validate MathArtist's minimal handoff from a Paper2Agent-generated project.

This does not assume Paper2Agent internals. The paper agent remains responsible for scientific
execution; this bridge validates a small observable manifest before data are imported.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,subprocess,sys

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('--root',default='.');ap.add_argument('--run-tests',action='store_true');args=ap.parse_args()
    m=json.loads(pathlib.Path(args.manifest).read_text());root=pathlib.Path(args.root).resolve();errs=[]
    for f in m.get('source_files',[]):
        p=root/f['path']
        if not p.exists():errs.append(f'missing {p}')
        elif f.get('sha256') and sha(p)!=f['sha256']:errs.append(f'hash mismatch {p}')
    if args.run_tests:
        for cmd in m.get('tests',[]):
            r=subprocess.run(cmd,shell=True,cwd=root)
            if r.returncode:errs.append(f'test failed: {cmd}')
    if not m.get('observables'):errs.append('manifest has no observables')
    if errs:
        print('\n'.join(errs),file=sys.stderr);raise SystemExit(1)
    print(json.dumps({'ok':True,'paper_id':m.get('paper_id'),'provenance':m.get('provenance'),'observables':m.get('observables')},indent=2))
if __name__=='__main__':main()
