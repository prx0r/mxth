#!/usr/bin/env python3
from pathlib import Path
import zipfile, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
version=(ROOT/'VERSION').read_text().strip()
out=ROOT.parent/f'mathartist-suite-v{version}.zip'
exclude_parts={'.git','__pycache__','.pytest_cache','external','.private','node_modules'}
exclude_names={'MANIFEST.sha256.json','mathartist.sqlite3','mathartist.sqlite3-wal','mathartist.sqlite3-shm','selfcheck.sqlite3','selfcheck.sqlite3-wal','selfcheck.sqlite3-shm'}
# License-unknown third-party sketch code: local research cache only, never shipped.
exclude_prefixes=('corpus/tsubuyaki/code/',)
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in exclude_parts for x in p.parts) and p.name not in exclude_names and not any(str(p.relative_to(ROOT)).startswith(x) for x in exclude_prefixes)]
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifest_path=ROOT/'MANIFEST.sha256.json';manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
files.append(manifest_path)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(files):z.write(p,Path('mathartist-suite')/p.relative_to(ROOT))
print(out)
