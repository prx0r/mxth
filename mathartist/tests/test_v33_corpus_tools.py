import importlib.util, pathlib, json, tempfile, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def test_candidate_extractor_separates_canvas_constants():
 m=load('ecc',ROOT/'tools/extract_control_candidates.py')
 xs=m.extract("t=0;draw=_=>{createCanvas(400,400);for(i=1e4;i--;)point(99*sin(i/40),200)}")
 assert any(x['role']=='observer_or_runtime' and x['literal']=='400' for x in xs)
 assert any(x['role']=='math_candidate' and x['literal']=='99' for x in xs)
def test_ingest_normalizes_and_hashes():
 m=load('ing',ROOT/'tools/ingest_tsubuyaki.py');x=m.normalize({'artist':'ア','code':'point(1,2)','tweet_url':'https://x.test/1'})
 assert x['artist']['name']=='ア' and len(x['code_sha256'])==64 and x['original_url']
def test_ingest_handles_archive_author_objects():
 m=load('ing',ROOT/'tools/ingest_tsubuyaki.py')
 x=m.normalize({'id':'1','author':{'name':'きんぞ','username':'TakagiHitoshi','url':'https://x.com/TakagiHitoshi'},'tweet_url':'https://x.test/1','code_file':'sketches/1.js','language':'p5js','tsubuyaki':{'code_chars':195},'runtime':{'engine':'p5.js'}})
 assert x['artist']['username']=='TakagiHitoshi' and x['archive_url'].endswith('sketch.html?id=1')
 assert x['code_url']=='https://tsubuyaki.art/sketches/1.js' and x['tsubuyaki']['code_chars']==195
 assert x['code_sha256'] is None and 'do not republish' in x['redistribution_status']
