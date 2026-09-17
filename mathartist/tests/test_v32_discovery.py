import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from morphology import novelty,farthest_first,fertility

def R(i,v='a',ok=True):
    return {'source_variant':v,'frame':{'symmetry_best':i/10,'occupancy':.1+i/100,'bbox_area_ratio':.2,'edge_density':.03*i,'spectral_entropy':.5,'compressibility':.4+i/50,'centroid_offset':.1,'contrast':.2},'integrity':{'pass':ok}}
def test_novelty_and_coverage_are_deterministic():
    rs=[R(i) for i in range(8)]; assert novelty(rs)==novelty(rs); assert farthest_first(rs,4)==farthest_first(rs,4); assert len(set(farthest_first(rs,4)))==4
def test_fertility_is_variant_local_and_not_human_scored():
    rs=[R(0,'a'),R(5,'a'),R(2,'b',False),R(7,'b')]; f=fertility(rs); assert set(f)=={'a','b'}; assert f['b']['valid_fraction']==.5
