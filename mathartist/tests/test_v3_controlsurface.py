import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from controlsurface.engine import random_controls, mutate_controls, validate_control_surface

SPEC={"control_surface":{
 "h":{"type":"float","min":.001,"max":.05,"default":.006,"sigma":.002,"role":"family","claim_scope":"same-family","provenance":"paper eq X"},
 "branch":{"type":"enum","values":["a","b"],"default":"a","role":"branch","claim_scope":"same-family","provenance":"construction cases"},
 "n":{"type":"int","min":1,"max":8,"default":3,"role":"sampling","claim_scope":"observation-only","provenance":"sampling contract"}
}}
def test_surface_valid(): assert validate_control_surface(SPEC)==[]
def test_random_and_mutation_stay_in_surface():
 r=random.Random(7); g=random_controls(SPEC,r)
 for _ in range(100): g=mutate_controls(SPEC,g,r)
 assert .001<=g['h']<=.05 and g['branch'] in ['a','b'] and 1<=g['n']<=8

def test_provenance_required():
 bad={"control_surface":{"x":{"type":"float","min":0,"max":1,"role":"family","claim_scope":"same-family"}}}
 assert any('provenance' in x for x in validate_control_surface(bad))

def test_variant_specific_surface():
 from app.archive import load_specs
 spec=load_specs()['TINYMAPS']
 assert validate_control_surface(spec)==[]
 r=random.Random(9)
 a=random_controls(spec,r,variant='radial-warp')
 b=random_controls(spec,r,variant='torus-lattice')
 assert 'k_base' in a and 'major' not in a
 assert 'major' in b and 'k_base' not in b
 for _ in range(50):
  a=mutate_controls(spec,a,r,variant='radial-warp')
 assert set(a)==set(spec['control_surfaces']['radial-warp'])

def test_open_parent_sampler_is_blind_to_human_events(tmp_path=None):
 import pathlib,tempfile,sys
 sys.path.insert(0,str(ROOT/'app'))
 import archive
 from explorers import sakana_archive_parent_ids
 old=archive.DB
 with tempfile.TemporaryDirectory() as td:
  archive.DB=pathlib.Path(td)/'x.sqlite3';archive.init_db()
  archive.create_population('TINYMAPS','frontier',40,seed=51)
  spec=archive.load_specs()['TINYMAPS']
  with archive.conn() as c:
   before=sakana_archive_parent_ids(c,'TINYMAPS',spec,random.Random(123),limit=30)
   ids=[r[0] for r in c.execute("SELECT id FROM phenotypes WHERE source_id='TINYMAPS' LIMIT 10")]
   for pid in ids:
    c.execute("INSERT INTO events(phenotype_id,session_id,event_type,value,metadata_json,created_at) VALUES(?,?,?,?,?,0)",(pid,'s','favorite',1,'{}'))
    c.execute("INSERT INTO events(phenotype_id,session_id,event_type,value,metadata_json,created_at) VALUES(?,?,?,?,?,0)",(pid,'s','dwell',999999,'{}'))
   after=sakana_archive_parent_ids(c,'TINYMAPS',spec,random.Random(123),limit=30)
  assert before==after
 archive.DB=old
