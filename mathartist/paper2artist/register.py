from __future__ import annotations
import json,subprocess,sys,shutil
from pathlib import Path
from .inspect_paper2agent import inspect

ROOT=Path(__file__).resolve().parents[1]

def register_manifest(manifest_path:Path):
    m=json.loads(manifest_path.read_text())
    agent_root=Path(m['paper2agent_output']).expanduser().resolve()
    inspection=inspect(agent_root)
    source=m.get('source',{})
    results=[]
    for obs in m.get('observables',[]):
        src=(manifest_path.parent/obs['file']).resolve()
        sid=obs['id'].upper().replace('-','_')
        cmd=[sys.executable,str(ROOT/'scripts/import_array_sequence.py'),str(src),'--id',sid,
             '--title',obs.get('title',sid),'--description',obs.get('description',source.get('description','Paper2Agent-derived immutable observable trajectory.')),
             '--fps',str(obs.get('fps',10)),'--provenance-level',obs.get('provenance_level','EXACT-RUNTIME')]
        if obs.get('array'):cmd+=['--array',obs['array']]
        if obs.get('sample') is not None:cmd+=['--sample',str(obs['sample'])]
        if obs.get('channel_names'):cmd+=['--channel-names',','.join(obs['channel_names'])]
        subprocess.run(cmd,check=True,cwd=ROOT)
        artifact=ROOT/'source_artifacts'/sid/'paper2agent-inspection.json'
        artifact.write_text(json.dumps(inspection,indent=2)+'\n')
        specp=ROOT/'specs'/f'{sid}.json';spec=json.loads(specp.read_text())
        spec['paper2agent']={
          'tree_sha256':inspection['tree_sha256'],
          'mcp_api':[{'name':x['name'],'kinds':x['kinds'],'file':x['file']} for x in inspection['mcp_api']],
          'usage_files':inspection['usage_files']
        }
        spec['source_bundle']['files'].append(str(artifact.relative_to(ROOT)))
        if source.get('paper'):spec['paper']=source['paper']
        if source.get('upstream'):spec['upstream']=source['upstream']
        specp.write_text(json.dumps(spec,indent=2)+'\n')
        results.append({'id':sid,'spec':str(specp),'tree_sha256':inspection['tree_sha256']})
    return results
