from __future__ import annotations
import json, sqlite3, time, uuid, math, random, hashlib, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path: __import__("sys").path.insert(0, str(ROOT))
from source_bundles import bundle_hash as source_bundle_hash
from explorers import sakana_archive_parent_ids
from controlsurface.engine import random_controls, mutate_controls, surface_for_spec

DB = Path(os.environ.get("MATHARTIST_DB", str(ROOT / "data" / "mathartist.sqlite3")))
SPEC_DIR = ROOT / "specs"


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS phenotypes(
          id TEXT PRIMARY KEY,
          source_id TEXT NOT NULL,
          source_variant TEXT NOT NULL,
          generation INTEGER NOT NULL,
          parent_ids TEXT NOT NULL,
          genome_json TEXT NOT NULL,
          mode TEXT NOT NULL,
          created_at REAL NOT NULL,
          spec_hash TEXT NOT NULL DEFAULT '',
          bundle_hash TEXT NOT NULL DEFAULT '',
          lineage_channel TEXT NOT NULL DEFAULT 'OPEN_BLIND'
        );
        CREATE INDEX IF NOT EXISTS idx_pheno_source ON phenotypes(source_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          phenotype_id TEXT NOT NULL,
          session_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          value REAL,
          metadata_json TEXT NOT NULL,
          created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_pheno ON events(phenotype_id, event_type);
        CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS study_assignments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          study_id TEXT NOT NULL,
          session_id TEXT NOT NULL,
          phenotype_id TEXT NOT NULL,
          source_id TEXT NOT NULL,
          arm TEXT NOT NULL,
          assigned_at REAL NOT NULL,
          UNIQUE(study_id, session_id, phenotype_id)
        );
        CREATE INDEX IF NOT EXISTS idx_study_session ON study_assignments(study_id, session_id, assigned_at);
        """)
        cols={r[1] for r in c.execute("PRAGMA table_info(phenotypes)")}
        if "spec_hash" not in cols:
            c.execute("ALTER TABLE phenotypes ADD COLUMN spec_hash TEXT NOT NULL DEFAULT ''")
        if "bundle_hash" not in cols:
            c.execute("ALTER TABLE phenotypes ADD COLUMN bundle_hash TEXT NOT NULL DEFAULT ''")
        if "lineage_channel" not in cols:
            c.execute("ALTER TABLE phenotypes ADD COLUMN lineage_channel TEXT NOT NULL DEFAULT 'OPEN_BLIND'")
        # Legacy rows are deterministically backfilled from the current source spec + frozen assets.
        # bundle_hash protects executable/source bytes as well as immutable metadata.
        specs=load_specs()
        for r in c.execute("SELECT id,source_id,source_variant,spec_hash,bundle_hash FROM phenotypes").fetchall():
            spec=specs.get(r["source_id"])
            if not spec: continue
            sh=r["spec_hash"] or core_hash(spec,r["source_variant"])
            try: bh=r["bundle_hash"] or source_bundle_hash(spec,r["source_variant"])
            except FileNotFoundError: bh=r["bundle_hash"] or ''
            c.execute("UPDATE phenotypes SET spec_hash=?,bundle_hash=? WHERE id=?",(sh,bh,r["id"]))


def load_specs():
    out = {}
    for p in sorted(SPEC_DIR.glob("*.json")):
        x = json.loads(p.read_text())
        out[x["id"]] = x
    return out


def core_hash(spec, source_variant):
    payload={"source_id":spec["id"],"source_variant":source_variant,"immutable_core":spec["immutable_core"]}
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def clamp(x, lo, hi): return lo if x < lo else hi if x > hi else x


def random_genome(spec, rng, variant=None):
    # V3.1: genome == admitted source control surface. No equation synthesis in the hot loop.
    return random_controls(spec, rng, variant=variant)


def mutate_genome(spec, parent, rng, strength=1.0, variant=None):
    return mutate_controls(spec, parent, rng, strength, variant=variant)


def event_scores(c, source_id, objective, session_id=None):
    rows = c.execute("SELECT id FROM phenotypes WHERE source_id=?", (source_id,)).fetchall()
    ids = [r[0] for r in rows]
    if not ids: return {}
    scores = {}
    for pid in ids:
        params = [pid]
        sess = ""
        if session_id:
            sess = " AND session_id=?"; params.append(session_id)
        ev = c.execute(f"SELECT event_type, COUNT(*) n, COALESCE(SUM(value),0) v FROM events WHERE phenotype_id=?{sess} GROUP BY event_type", params).fetchall()
        m = {r["event_type"]:(r["n"],r["v"]) for r in ev}
        imp = max(1, m.get("impression", (0,0))[0])
        h5 = m.get("horizon_5", (0,0))[0]
        h10 = m.get("horizon_10", (0,0))[0]
        h20 = m.get("horizon_20", (0,0))[0]
        if objective == "5s": s = h5 / imp
        elif objective == "10s": s = h10 / max(1,h5)
        elif objective == "20s": s = h20 / max(1,h10)
        elif objective == "replay": s = m.get("replay",(0,0))[0]/imp
        elif objective in ("youtube-5s","youtube-10s","youtube-20s","youtube-replay"):
            key={"youtube-5s":"youtube_5s","youtube-10s":"youtube_10_given_5",
                 "youtube-20s":"youtube_20_given_10","youtube-replay":"youtube_replay"}[objective]
            n,v=m.get(key,(0,0))
            if not n: continue
            s=v/n
        elif objective == "for-you":
            fav = m.get("favorite",(0,0))[0]
            fs = m.get("fullscreen",(0,0))[0]
            dwell = m.get("dwell",(0,0))[1] / 1000.0
            s = 2.5*fav + .8*fs + min(2.0,dwell/20.0)
        else:
            # Open archive: branch popularity + tiny recency-independent behavior signal.
            children = c.execute("SELECT COUNT(*) FROM phenotypes WHERE parent_ids LIKE ?", (f'%"{pid}"%',)).fetchone()[0]
            s = math.log1p(children) + .1*m.get("fullscreen",(0,0))[0]
        scores[pid] = float(s)
    return scores


def get_phenotype(c, pid):
    r = c.execute("SELECT * FROM phenotypes WHERE id=?", (pid,)).fetchone()
    if not r: return None
    return {"id":r["id"],"source_id":r["source_id"],"source_variant":r["source_variant"],"generation":r["generation"],
            "parent_ids":json.loads(r["parent_ids"]),"genome":json.loads(r["genome_json"]),"mode":r["mode"],"created_at":r["created_at"],
            "spec_hash":r["spec_hash"] if "spec_hash" in r.keys() else "",
            "bundle_hash":r["bundle_hash"] if "bundle_hash" in r.keys() else "",
            "lineage_channel":r["lineage_channel"] if "lineage_channel" in r.keys() else "OPEN_BLIND"}


def create_population(source_id, mode="open", count=72, selected_ids=None, session_id=None, seed=None, lineage_channel="OPEN_BLIND"):
    specs = load_specs(); spec = specs[source_id]
    rng = random.Random(seed if seed is not None else time.time_ns())
    selected_ids = selected_ids or []
    created = []
    with conn() as c:
        explicit = [get_phenotype(c,p) for p in selected_ids]
        parents = [p for p in explicit if p and p["source_id"] == source_id]
        for p in parents:
            expected_core=core_hash(spec,p["source_variant"])
            expected_bundle=source_bundle_hash(spec,p["source_variant"])
            if p.get("spec_hash") and p["spec_hash"] != expected_core:
                raise ValueError(f"immutable core changed for {p['id']}; fork/register a new source id instead of silently continuing this lineage")
            if p.get("bundle_hash") and p["bundle_hash"] != expected_bundle:
                raise ValueError(f"source bundle bytes changed for {p['id']}; fork/register a new source id instead of silently continuing this lineage")
        if not parents and mode not in ("frontier", "open"):
            # Personal preference is session-local; public attention niches are aggregate.
            score_session = session_id if mode == "for-you" else None
            scores = event_scores(c, source_id, mode, session_id=score_session)
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:max(12,count//3)]
            parents = [get_phenotype(c,pid) for pid,_ in ranked if get_phenotype(c,pid)]
        if not parents and mode == "open":
            ids=sakana_archive_parent_ids(c,source_id,spec,rng,limit=max(48,count))
            parents=[get_phenotype(c,pid) for pid in ids]
            parents=[p for p in parents if p]
        for i in range(count):
            root = (not parents) or (mode == "open" and rng.random() < 0.15)
            if root:
                variant = rng.choice(spec["source_variants"])["id"]
                genome = random_genome(spec, rng, variant=variant)
                generation = 0
                pids = []
            else:
                p = rng.choice(parents)
                # Preserve source variant: evolution sees the same scientific object/trajectory.
                variant = p["source_variant"]
                genome = mutate_genome(spec, p["genome"], rng, strength=.7 if mode == "for-you" else 1.0, variant=variant)
                generation = p["generation"] + 1
                pids = [p["id"]]
                # occasional crossover changes only admitted controls and only within same source variant
                compatible = [q for q in parents if q["source_variant"] == variant and q["id"] != p["id"]]
                if compatible and rng.random() < .22:
                    q = rng.choice(compatible)
                    for k in genome:
                        if rng.random() < .35: genome[k] = q["genome"][k]
                    pids.append(q["id"])
            pid = f"{source_id.lower()}-{uuid.uuid4().hex[:10]}"
            now = time.time()
            sh=core_hash(spec,variant); bh=source_bundle_hash(spec,variant)
            c.execute("INSERT INTO phenotypes(id,source_id,source_variant,generation,parent_ids,genome_json,mode,created_at,spec_hash,bundle_hash,lineage_channel) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (pid,source_id,variant,generation,json.dumps(pids),json.dumps(genome,sort_keys=True),mode,now,sh,bh,lineage_channel))
            created.append({"id":pid,"source_id":source_id,"source_variant":variant,"generation":generation,"parent_ids":pids,"genome":genome,"mode":mode,"created_at":now,"spec_hash":sh,"bundle_hash":bh})
    return created


def list_population(source_id, mode="open", count=72, session_id=None):
    with conn() as c:
        if mode == "potential":
            rows=c.execute("SELECT phenotype_id,MAX(created_at) t FROM events WHERE event_type='potential' AND value>0 GROUP BY phenotype_id ORDER BY t DESC LIMIT ?",(count*4,)).fetchall()
            out=[get_phenotype(c,r[0]) for r in rows]; return [x for x in out if x and x["source_id"]==source_id][:count]
        if mode in ("5s","10s","20s","replay","for-you","youtube-5s","youtube-10s","youtube-20s","youtube-replay"):
            score_session = session_id if mode == "for-you" else None
            scores=event_scores(c,source_id,mode,session_id=score_session)
            ids=[x[0] for x in sorted(scores.items(),key=lambda kv:kv[1],reverse=True)[:count]]
            out=[]
            for p in ids:
                x=get_phenotype(c,p)
                if x:
                    x["score"]=scores.get(p,0.0)
                    out.append(x)
            out=[x for x in out if x]
            if len(out)>=min(12,count): return out
        rows=c.execute("SELECT id FROM phenotypes WHERE source_id=? ORDER BY created_at DESC LIMIT ?",(source_id,count)).fetchall()
        out=[get_phenotype(c,r[0]) for r in rows]
        if len(out)<min(12,count):
            out=create_population(source_id,mode,count,session_id=session_id)
        return out[:count]


def get_many(ids):
    """Fetch exact phenotype IDs while preserving caller order."""
    ids=[x for x in ids if x][:256]
    with conn() as c:
        return [x for x in (get_phenotype(c,pid) for pid in ids) if x]


def add_event(payload):
    with conn() as c:
        c.execute("INSERT INTO events(phenotype_id,session_id,event_type,value,metadata_json,created_at) VALUES(?,?,?,?,?,?)",
          (payload.get("phenotype_id",""),payload.get("session_id","anon"),payload.get("event_type","unknown"),payload.get("value"),json.dumps(payload.get("metadata",{})),time.time()))


def lineage(pid, max_nodes=64):
    with conn() as c:
        start=get_phenotype(c,pid)
        if not start:return []
        out=[]; queue=[start]; seen=set()
        while queue and len(out)<max_nodes:
            x=queue.pop(0)
            if x["id"] in seen:continue
            seen.add(x["id"]);out.append(x)
            for p in x["parent_ids"]:
                y=get_phenotype(c,p)
                if y:queue.append(y)
        return out



def study_sample(source_id, session_id, count=36, study_id="attention-v1", seed=None):
    """Balanced random assignment for the first-party attention study.

    It samples existing phenotypes without using their behavioral score. Previously assigned
    phenotypes for the same session/study are avoided. If the archive is small, fresh random
    interpretation roots are added. The scientific source core remains immutable.
    """
    count=max(1,min(128,int(count)))
    rng=random.Random(seed if seed is not None else f"{study_id}:{session_id}:{time.time_ns()}")
    specs=load_specs()
    if source_id not in specs: raise KeyError(source_id)
    with conn() as c:
        seen={r[0] for r in c.execute("SELECT phenotype_id FROM study_assignments WHERE study_id=? AND session_id=?",(study_id,session_id))}
        rows=c.execute("SELECT id,source_variant,generation FROM phenotypes WHERE source_id=? ORDER BY created_at DESC LIMIT 2000",(source_id,)).fetchall()
    pool=[dict(r) for r in rows if r['id'] not in seen]
    if len(pool)<count:
        create_population(source_id,'frontier',max(count*2,48),seed=rng.randrange(1<<31))
        with conn() as c:
            rows=c.execute("SELECT id,source_variant,generation FROM phenotypes WHERE source_id=? ORDER BY created_at DESC LIMIT 2000",(source_id,)).fetchall()
        pool=[dict(r) for r in rows if r['id'] not in seen]
    # round-robin across frozen source variants so a study page is not accidentally dominated by one variant
    buckets={}
    for r in pool:buckets.setdefault(r['source_variant'],[]).append(r['id'])
    for xs in buckets.values():rng.shuffle(xs)
    chosen=[]; keys=list(buckets);rng.shuffle(keys)
    while len(chosen)<count and any(buckets.values()):
        for k in list(keys):
            if buckets[k] and len(chosen)<count:chosen.append(buckets[k].pop())
    rng.shuffle(chosen)
    with conn() as c:
        out=[]
        for pid in chosen:
            x=get_phenotype(c,pid)
            if not x:continue
            # presentation framing is independently randomized for experiments that study
            # commonization / contextual disclosure. It never changes the phenotype or source.
            presentation='particular'
            if study_id=='commonization-v1':
                presentation='commonized' if rng.random()<0.5 else 'particular'
            arm=f"{source_id}:{x['source_variant']}|{presentation}"
            c.execute("INSERT OR IGNORE INTO study_assignments(study_id,session_id,phenotype_id,source_id,arm,assigned_at) VALUES(?,?,?,?,?,?)",(study_id,session_id,pid,source_id,arm,time.time()))
            x['study_id']=study_id;x['study_arm']=arm;x['presentation_arm']=presentation;out.append(x)
    return out


def export_all():
    with conn() as c:
        ps=[get_phenotype(c,r[0]) for r in c.execute("SELECT id FROM phenotypes ORDER BY created_at")]
        es=[dict(r) for r in c.execute("SELECT * FROM events ORDER BY created_at")]
    return {"phenotypes":ps,"events":es}


def correlation_report(source_id=None):
    """Exploratory correlation table between rendered structural descriptors and behavior.

    This is deliberately descriptive: it does not claim causality, rasa, or valence. Structural
    descriptors are generated by the browser from rendered phenotypes; behavioral outcomes come from
    first-party events. Only phenotypes with at least one structural event are included.
    """
    with conn() as c:
        if source_id:
            rows=c.execute("SELECT id FROM phenotypes WHERE source_id=?",(source_id,)).fetchall()
        else:
            rows=c.execute("SELECT id FROM phenotypes").fetchall()
        records=[]
        for rr in rows:
            pid=rr[0]
            st=c.execute("SELECT metadata_json FROM events WHERE phenotype_id=? AND event_type='structural' ORDER BY created_at DESC LIMIT 1",(pid,)).fetchone()
            if not st: continue
            try: m=json.loads(st[0])
            except Exception: continue
            ev=c.execute("SELECT event_type,COUNT(*) n,COALESCE(SUM(value),0) v FROM events WHERE phenotype_id=? GROUP BY event_type",(pid,)).fetchall()
            e={r['event_type']:(r['n'],r['v']) for r in ev}
            imp=max(1,e.get('impression',(0,0))[0]);h5=e.get('horizon_5',(0,0))[0];h10=e.get('horizon_10',(0,0))[0];h20=e.get('horizon_20',(0,0))[0]
            dwell_n,dwell_v=e.get('dwell',(0,0))
            rec={k:float(m.get(k,0)) for k in ('symmetry','entropy','occupancy','edge','mean') if k in m}
            rec.update({
              'survival_5':h5/imp,
              'survival_10_cond':h10/max(1,h5),
              'survival_20_cond':h20/max(1,h10),
              'favorite_rate':e.get('favorite',(0,0))[0]/imp,
              'fullscreen_rate':e.get('fullscreen',(0,0))[0]/imp,
              'replay_rate':e.get('replay',(0,0))[0]/imp,
              'dwell_s':(dwell_v/max(1,dwell_n))/1000.0,
            })
            records.append(rec)
    metrics=('symmetry','entropy','occupancy','edge','mean')
    outcomes=('survival_5','survival_10_cond','survival_20_cond','favorite_rate','fullscreen_rate','replay_rate','dwell_s')
    def pearson(xs,ys):
        n=len(xs)
        if n<3:return None
        mx=sum(xs)/n;my=sum(ys)/n
        dx=[x-mx for x in xs];dy=[y-my for y in ys]
        vx=sum(x*x for x in dx);vy=sum(y*y for y in dy)
        if vx<=0 or vy<=0:return None
        return sum(x*y for x,y in zip(dx,dy))/math.sqrt(vx*vy)
    corr={}
    for a in metrics:
        corr[a]={}
        for b in outcomes:
            pairs=[(r[a],r[b]) for r in records if a in r and b in r]
            v=pearson([x for x,_ in pairs],[y for _,y in pairs])
            corr[a][b]=None if v is None else round(v,4)
    return {'source_id':source_id,'n_phenotypes':len(records),'note':'exploratory Pearson correlations; observational/descriptive, not causal or a measure of rasa/valence','correlations':corr}
