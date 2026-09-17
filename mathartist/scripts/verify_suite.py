#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys,tempfile,time,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]

def sha(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()

def main():
    subprocess.run([sys.executable,'-m','pytest','-q'],check=True,cwd=ROOT)
    # Source bundle manifests must resolve and hash all frozen source/runtime files.
    sys.path.insert(0,str(ROOT/'app'))
    from archive import load_specs
    from source_bundles import bundle_manifest
    for sid,spec in load_specs().items():
        for v in spec.get('source_variants',[]):
            m=bundle_manifest(spec,v['id']);assert m['bundle_sha256'] and all(x['sha256'] for x in m['files'])
    # Syntax-check every browser module with Node when present.
    node=__import__('shutil').which('node')
    if node:
        for p in sorted((ROOT/'app/static/js').rglob('*.js')):
            subprocess.run([node,'--check',str(p)],check=True)
    # Deterministic source assets must be present and nontrivial.
    req=[ROOT/'app/static/data/lenia/orbium.u8.bin',
         ROOT/'app/static/data/bioelectric/center-hyperpolarized.f32.bin',
         ROOT/'app/static/data/bioelectric/french-flag.f32.bin']
    for p in req:
        assert p.exists() and p.stat().st_size>1000,p
    # HTTP smoke test on an ephemeral free port.
    import socket
    s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
    
    tmpdb=tempfile.TemporaryDirectory(); env=dict(__import__('os').environ); env['MATHARTIST_DB']=str(pathlib.Path(tmpdb.name)/'smoke.sqlite3')
    proc=subprocess.Popen([sys.executable,str(ROOT/'app/server.py'),str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
    try:
        for _ in range(40):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.5) as r:
                    health=json.load(r);break
            except Exception:time.sleep(.05)
        else:raise RuntimeError('server did not start')
        assert health['ok']
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/sources') as r:sources=json.load(r)
        assert {'LENIA','CHLADNI','BIOELECTRIC','NS26','TINYMAPS'}<= {x['id'] for x in sources}
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/population?source=TINYMAPS&mode=open&count=4') as r:pop=json.load(r)
        assert len(pop)==4 and all(x.get('spec_hash') and x.get('bundle_hash') and x.get('genome') for x in pop)
        assert all(x['source_variant'] in ('radial-warp','polar-warp','latent-19','torus-lattice') for x in pop)
        # Render the generated V3.1 mathematical family through the exact browser source renderer.
        if node:
            pf=pathlib.Path(tmpdb.name)/'tiny-pop.json';pf.write_text(json.dumps(pop))
            od=pathlib.Path(tmpdb.name)/'frames'
            subprocess.run([node,str(ROOT/'tools/render_population.cjs'),str(ROOT),str(pf),str(od),'96','3'],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
            assert all((od/x['id']/'t0.png').stat().st_size>100 for x in pop)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/experiments') as r:exps=json.load(r)
        assert any(x.get('id')=='attention-rasa-v2' for x in exps)
    finally:
        proc.terminate();proc.wait(timeout=5);tmpdb.cleanup()
    print(json.dumps({'ok':True,'sources':len(sources),'experiments':len(exps),'lenia_bytes':req[0].stat().st_size,'bio_bytes':req[1].stat().st_size},indent=2))
if __name__=='__main__':main()
