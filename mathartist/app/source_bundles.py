from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def _configured_files(spec: dict, variant: str) -> list[Path]:
    cfg=spec.get('source_bundle',{})
    out=[]
    for item in cfg.get('files',[]):
        rel=item.format(variant=variant,source_id=spec['id'])
        p=(ROOT/rel).resolve()
        if not str(p).startswith(str(ROOT.resolve())):
            raise ValueError(f'unsafe source bundle path: {rel}')
        if not p.exists():
            raise FileNotFoundError(f'source bundle file missing: {rel}')
        if p.is_file(): out.append(p)
    return out


def bundle_manifest(spec: dict, variant: str) -> dict:
    files=[]
    for p in _configured_files(spec,variant):
        files.append({
            'path':str(p.relative_to(ROOT)),
            'bytes':p.stat().st_size,
            'sha256':sha256_file(p),
        })
    payload={
        'format':'mathartist.source-bundle.v2',
        'source_id':spec['id'],
        'variant':variant,
        'provenance_level':spec.get('provenance_level'),
        'immutable_core':spec.get('immutable_core',{}),
        'upstream':spec.get('upstream'),
        'paper':spec.get('paper'),
        'upstream_commit':spec.get('source_bundle',{}).get('upstream_commit'),
        'files':files,
    }
    canonical=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    payload['bundle_sha256']=hashlib.sha256(canonical).hexdigest()
    return payload


def bundle_hash(spec: dict, variant: str) -> str:
    return bundle_manifest(spec,variant)['bundle_sha256']


def write_manifests(specs: dict | None=None, out_dir: Path|None=None) -> list[Path]:
    if specs is None:
        from archive import load_specs
        specs=load_specs()
    out_dir=out_dir or ROOT/'bundles'
    out_dir.mkdir(parents=True,exist_ok=True)
    written=[]
    for sid,spec in sorted(specs.items()):
        for v in spec.get('source_variants',[]):
            m=bundle_manifest(spec,v['id'])
            p=out_dir/f"{sid}--{v['id']}.bundle.json"
            p.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
            written.append(p)
    return written
