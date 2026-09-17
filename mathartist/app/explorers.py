from __future__ import annotations
import json,math
try:
    from controlsurface.engine import surface_for_spec
except ModuleNotFoundError:
    from pathlib import Path
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from controlsurface.engine import surface_for_spec


def _distance(spec,a,b,variant=None):
    acc=[]
    for k,d in surface_for_spec(spec,variant).items():
        av=a.get(k);bv=b.get(k)
        if av is None or bv is None:continue
        if d['type'] in ('float','int'):
            span=max(1e-12,float(d['max'])-float(d['min']));acc.append(((float(av)-float(bv))/span)**2)
        elif d['type']=='enum':acc.append(0 if av==bv else 1)
    return math.sqrt(sum(acc)/max(1,len(acc)))


def sakana_archive_parent_ids(c,source_id,spec,rng,limit=60):
    """Shared-archive sampler inspired by Picbreeder-VLM's ecology.

    Mixes recency, branching fertility, genotype diversity and random stepping stones.
    It never reads favorites, dwell, fullscreen, retention, rasa, or valence. It deliberately leaves a stochastic component so the archive does not
    converge on one aesthetic attractor. This is a local compatible sampler, not copied Sakana code.
    """
    rows=c.execute('SELECT id,genome_json,created_at,source_variant FROM phenotypes WHERE source_id=? ORDER BY created_at DESC LIMIT 1200',(source_id,)).fetchall()
    if not rows:return []
    items=[{'id':r['id'],'g':json.loads(r['genome_json']),'created_at':r['created_at'],'variant':r['source_variant']} for r in rows]
    ids=[x['id'] for x in items]
    branch={pid:c.execute('SELECT COUNT(*) FROM phenotypes WHERE parent_ids LIKE ?',(f'%"{pid}"%',)).fetchone()[0] for pid in ids}
    # OPEN is intentionally blind to human taste/attention. A branch survives because
    # it is recent, fertile, parameter-space-diverse, or a random stepping stone.
    recent=[x['id'] for x in items[:16]]
    branchy=sorted(ids,key=lambda x:branch[x],reverse=True)[:16]
    # Greedy farthest-point sample in interpretation-genome space.
    byid={x['id']:x for x in items};diverse=[]
    seed=rng.choice(ids);diverse=[seed]
    pool=set(ids)-{seed}
    while pool and len(diverse)<16:
        nxt=max(pool,key=lambda pid:min(_distance(spec,byid[pid]['g'],byid[q]['g'],byid[pid]['variant']) if byid[pid]['variant']==byid[q]['variant'] else 1.0 for q in diverse))
        diverse.append(nxt);pool.remove(nxt)
    randoms=rng.sample(ids,min(16,len(ids)))
    ordered=[];seen=set()
    streams=[recent,branchy,diverse,randoms]
    # Interleave instead of exhausting one source first.
    for i in range(max(map(len,streams))):
        for stream in streams:
            if i<len(stream) and stream[i] not in seen:
                seen.add(stream[i]);ordered.append(stream[i])
                if len(ordered)>=limit:return ordered
    return ordered
