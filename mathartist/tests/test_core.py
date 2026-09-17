import json, sys, pathlib, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import archive

def test_specs():
    specs=archive.load_specs();assert {'LENIA','CHLADNI','BIOELECTRIC','NS26','TINYMAPS'}<=set(specs)
    for s in specs.values():
        assert s['immutable_core'] and s['source_variants']
        assert s.get('interpretation_genes') or s.get('control_surface') or s.get('control_surfaces')
        assert all('id' in v for v in s['source_variants'])

def test_mutation_never_has_core_keys():
    specs=archive.load_specs();r=__import__('random').Random(1)
    for s in specs.values():
        variants=[v['id'] for v in s['source_variants']]
        for variant in variants:
            g=archive.random_genome(s,r,variant=variant)
            for _ in range(100):g=archive.mutate_genome(s,g,r,variant=variant)
            assert not (set(g)&set(s['immutable_core']))
            if s.get('control_surfaces'):
                assert set(g)==set(s['control_surfaces'][variant])

def test_variant_and_core_hash_frozen_in_descendants():
    old=archive.DB
    with tempfile.TemporaryDirectory() as td:
        archive.DB=pathlib.Path(td)/'x.sqlite3';archive.init_db()
        roots=archive.create_population('CHLADNI','open',4,seed=1);p=roots[0]
        kids=archive.create_population('CHLADNI','frontier',20,[p['id']],seed=2)
        assert kids and all(k['source_variant']==p['source_variant'] for k in kids)
        assert all(k['spec_hash']==p['spec_hash'] for k in kids)
    archive.DB=old

def test_core_change_blocks_lineage():
    old_db,old_specdir=archive.DB,archive.SPEC_DIR
    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td);archive.DB=td/'x.sqlite3';archive.SPEC_DIR=td/'specs';archive.SPEC_DIR.mkdir();archive.init_db()
        original=json.loads((ROOT/'specs/CHLADNI.json').read_text());
        (archive.SPEC_DIR/'CHLADNI.json').write_text(json.dumps(original))
        p=archive.create_population('CHLADNI','frontier',1,seed=3)[0]
        modified=json.loads(json.dumps(original));modified['immutable_core']['square']='changed'
        (archive.SPEC_DIR/'CHLADNI.json').write_text(json.dumps(modified))
        try:
            archive.create_population('CHLADNI','frontier',1,[p['id']],seed=4)
        except ValueError as e:
            assert 'immutable core changed' in str(e)
        else: raise AssertionError('lineage continued after immutable core changed')
    archive.DB,archive.SPEC_DIR=old_db,old_specdir

def test_source_assets():
    assert (ROOT/'app/static/data/lenia/orbium.u8.bin').stat().st_size>10000
    for v in ('center-hyperpolarized','french-flag','uniform-bistable'):
        assert (ROOT/f'app/static/data/bioelectric/{v}.f32.bin').stat().st_size>10000


def test_bundle_hash_covers_source_bytes():
    old_db=archive.DB
    from source_bundles import bundle_hash
    with tempfile.TemporaryDirectory() as td:
        archive.DB=pathlib.Path(td)/'x.sqlite3';archive.init_db()
        spec=archive.load_specs()['LENIA'];h1=bundle_hash(spec,'orbium')
        p=archive.create_population('LENIA','frontier',1,seed=11)[0]
        assert p['bundle_hash']==h1
        # Do not mutate real source bytes here; instead verify manifest actually includes trajectory bytes.
        from source_bundles import bundle_manifest
        paths={x['path'] for x in bundle_manifest(spec,'orbium')['files']}
        assert 'app/static/data/lenia/orbium.u8.bin' in paths
    archive.DB=old_db

def test_experiment_response_store():
    old=archive.DB
    with tempfile.TemporaryDirectory() as td:
        archive.DB=pathlib.Path(td)/'x.sqlite3';archive.init_db()
        import experiment_store
        experiment_store.init_experiment_db()
        p=archive.create_population('CHLADNI','frontier',1,seed=12)[0]
        experiment_store.add_response({'experiment_id':'attention-rasa-v2','phenotype_id':p['id'],'session_id':'t','valence':.4,'absorption':.8,'rasa_label':'adbhuta'})
        r=experiment_store.experiment_report('attention-rasa-v2')
        assert r['n_responses']==1 and r['rasa_labels']['adbhuta']==1
    archive.DB=old

if __name__=='__main__':
    test_specs();test_mutation_never_has_core_keys();test_variant_and_core_hash_frozen_in_descendants();test_core_change_blocks_lineage();test_source_assets();test_bundle_hash_covers_source_bytes();test_experiment_response_store();print('ok')
