from __future__ import annotations
import ast,hashlib,json,os
from pathlib import Path

SKIP={'.git','.venv','venv','__pycache__','.pytest_cache','node_modules','dist'}

def sha256_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()

def tree_manifest(root:Path):
    files=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or any(x in SKIP for x in p.parts):continue
        try: rel=str(p.relative_to(root))
        except: continue
        files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    raw=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
    return files,hashlib.sha256(raw).hexdigest()

def decorated_api(py:Path):
    try: tree=ast.parse(py.read_text(errors='ignore'))
    except Exception:return []
    out=[]
    for n in ast.walk(tree):
        if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        kinds=[]
        for d in n.decorator_list:
            text=ast.unparse(d) if hasattr(ast,'unparse') else ''
            low=text.lower()
            for k in ('tool','resource','prompt'):
                if k in low:kinds.append(k)
        if kinds:out.append({'name':n.name,'kinds':sorted(set(kinds)),'file':str(py)})
    return out

def inspect(root:Path):
    root=root.resolve();files,tree_hash=tree_manifest(root)
    api=[]
    for p in root.rglob('*.py'):
        if any(x in SKIP for x in p.parts):continue
        for x in decorated_api(p):
            x['file']=str(p.relative_to(root));api.append(x)
    usage=[str(p.relative_to(root)) for p in root.rglob('USAGE.md')]
    return {
      'schema':'mathartist.paper2agent-inspection.v2',
      'root':str(root),'tree_sha256':tree_hash,'file_count':len(files),
      'usage_files':sorted(usage),'mcp_api':api,'files':files,
      'note':'Inspection fingerprints the delivered Paper2Agent output. It does not claim every discovered function is a valid MathArtist observable.'
    }
