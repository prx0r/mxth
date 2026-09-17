from __future__ import annotations
import json,time,math
from pathlib import Path
from archive import conn

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'experiments'/'registry'


def init_experiment_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS experiment_responses(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          experiment_id TEXT NOT NULL,
          phenotype_id TEXT NOT NULL,
          session_id TEXT NOT NULL,
          valence REAL,
          arousal REAL,
          absorption REAL,
          rasa_label TEXT,
          free_text TEXT,
          metadata_json TEXT NOT NULL,
          created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_exp_resp ON experiment_responses(experiment_id,phenotype_id,created_at);
        CREATE TABLE IF NOT EXISTS youtube_videos(
          video_id TEXT PRIMARY KEY,
          phenotype_id TEXT NOT NULL,
          experiment_id TEXT NOT NULL,
          duration_s REAL,
          published_at REAL,
          metadata_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_yt_pheno ON youtube_videos(phenotype_id,experiment_id);
        CREATE TABLE IF NOT EXISTS youtube_retention(
          video_id TEXT NOT NULL,
          elapsed_ratio REAL NOT NULL,
          audience_watch_ratio REAL,
          relative_retention REAL,
          started_watching REAL,
          stopped_watching REAL,
          segment_impressions REAL,
          fetched_at REAL NOT NULL,
          PRIMARY KEY(video_id,elapsed_ratio)
        );
        ''')


def list_experiments():
    out=[]
    if not REGISTRY.exists(): return out
    for p in sorted(REGISTRY.glob('*.json')):
        x=json.loads(p.read_text());x['_file']=p.name;out.append(x)
    return out


def get_experiment(exp_id:str):
    for x in list_experiments():
        if x.get('id')==exp_id:return x
    return None


def add_response(payload:dict):
    exp=payload.get('experiment_id','attention-rasa-v2')
    if not get_experiment(exp): raise KeyError(f'unknown experiment: {exp}')
    def bounded(name,lo=-1,hi=1):
        v=payload.get(name)
        if v is None:return None
        v=float(v);return max(lo,min(hi,v))
    with conn() as c:
        c.execute('''INSERT INTO experiment_responses(
          experiment_id,phenotype_id,session_id,valence,arousal,absorption,rasa_label,free_text,metadata_json,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?)''',(
          exp,payload.get('phenotype_id',''),payload.get('session_id','anon'),
          bounded('valence'),bounded('arousal'),bounded('absorption'),
          payload.get('rasa_label'),payload.get('free_text','')[:2000],json.dumps(payload.get('metadata',{})),time.time()
        ))


def register_youtube_video(video_id, phenotype_id, experiment_id='youtube-attention-v2', duration_s=None, metadata=None):
    with conn() as c:
        c.execute('''INSERT INTO youtube_videos(video_id,phenotype_id,experiment_id,duration_s,published_at,metadata_json)
        VALUES(?,?,?,?,?,?) ON CONFLICT(video_id) DO UPDATE SET phenotype_id=excluded.phenotype_id,
        experiment_id=excluded.experiment_id,duration_s=excluded.duration_s,metadata_json=excluded.metadata_json''',
        (video_id,phenotype_id,experiment_id,duration_s,time.time(),json.dumps(metadata or {})))


def upsert_retention(video_id, rows:list[dict]):
    now=time.time()
    with conn() as c:
        for r in rows:
            c.execute('''INSERT INTO youtube_retention(video_id,elapsed_ratio,audience_watch_ratio,relative_retention,
              started_watching,stopped_watching,segment_impressions,fetched_at) VALUES(?,?,?,?,?,?,?,?)
              ON CONFLICT(video_id,elapsed_ratio) DO UPDATE SET audience_watch_ratio=excluded.audience_watch_ratio,
              relative_retention=excluded.relative_retention,started_watching=excluded.started_watching,
              stopped_watching=excluded.stopped_watching,segment_impressions=excluded.segment_impressions,
              fetched_at=excluded.fetched_at''',(
              video_id,float(r['elapsedVideoTimeRatio']),_f(r.get('audienceWatchRatio')),_f(r.get('relativeRetentionPerformance')),
              _f(r.get('startedWatching')),_f(r.get('stoppedWatching')),_f(r.get('totalSegmentImpressions')),now))


def _f(x):
    try:return None if x is None else float(x)
    except:return None


def _nearest(rows, target):
    if not rows:return None
    return min(rows,key=lambda r:abs(float(r['elapsed_ratio'])-target))


def youtube_fitness(video_id:str):
    """Derive named attention horizons from one YouTube retention curve.

    These are observational fitness coordinates. They are not randomized effects and are never
    labelled as rasa or valence. Segment impressions are carried through as an exposure diagnostic.
    """
    with conn() as c:
        v=c.execute('SELECT * FROM youtube_videos WHERE video_id=?',(video_id,)).fetchone()
        rows=[dict(r) for r in c.execute('SELECT * FROM youtube_retention WHERE video_id=? ORDER BY elapsed_ratio',(video_id,))]
    if not v or not rows:return None
    dur=float(v['duration_s'] or 30.0)
    def awr(sec):
        r=_nearest(rows,max(0,min(1,sec/dur)));return None if not r else r.get('audience_watch_ratio')
    a5,a10,a20=awr(5),awr(10),awr(20)
    replay=sum(max(0,(r.get('audience_watch_ratio') or 0)-1) for r in rows)/max(1,len(rows))
    imps=[r.get('segment_impressions') for r in rows if r.get('segment_impressions') is not None]
    exposure_min=min(imps) if imps else None
    exposure_median=None
    if imps:
        z=sorted(float(x) for x in imps);n=len(z);exposure_median=z[n//2] if n%2 else (z[n//2-1]+z[n//2])/2
    return {
      'video_id':video_id,'phenotype_id':v['phenotype_id'],'duration_s':dur,
      'awr_5s':a5,'awr_10s':a10,'awr_20s':a20,
      'hold_10_given_5':None if not a5 or a10 is None else a10/a5,
      'hold_20_given_10':None if not a10 or a20 is None else a20/a10,
      'replay_area':replay,'points':len(rows),
      'segment_impressions_min':exposure_min,'segment_impressions_median':exposure_median,
      'observational':True
    }


def sync_youtube_fitness_events(video_id:str):
    """Materialize one video's latest YouTube fitness into the generic evolution event store.

    Re-syncing is idempotent for the video because its previous youtube:* session events are replaced.
    This creates an explicitly separate evolutionary sub-environment; OPEN and FOR YOU never consume
    these events unless the caller selects a youtube-* objective.
    """
    f=youtube_fitness(video_id)
    if not f:return None
    mapping={
      'youtube_5s':f.get('awr_5s'),
      'youtube_10_given_5':f.get('hold_10_given_5'),
      'youtube_20_given_10':f.get('hold_20_given_10'),
      'youtube_replay':f.get('replay_area'),
    }
    session=f'youtube:{video_id}'
    meta={'video_id':video_id,'environment':'youtube-wild','observational':True,
          'segment_impressions_min':f.get('segment_impressions_min'),
          'segment_impressions_median':f.get('segment_impressions_median')}
    with conn() as c:
        c.execute("DELETE FROM events WHERE session_id=? AND event_type LIKE 'youtube_%'",(session,))
        for typ,val in mapping.items():
            if val is None:continue
            c.execute("INSERT INTO events(phenotype_id,session_id,event_type,value,metadata_json,created_at) VALUES(?,?,?,?,?,?)",
                      (f['phenotype_id'],session,typ,float(val),json.dumps(meta),time.time()))
    return f


def _pearson(xs,ys):
    if len(xs)<3:return None
    mx=sum(xs)/len(xs);my=sum(ys)/len(ys)
    dx=[x-mx for x in xs];dy=[y-my for y in ys]
    vx=sum(x*x for x in dx);vy=sum(y*y for y in dy)
    if vx<=1e-15 or vy<=1e-15:return None
    return sum(x*y for x,y in zip(dx,dy))/math.sqrt(vx*vy)


def structural_response_report(exp_id='attention-rasa-v2'):
    """Exploratory bridge from rendered structure to reported human experience.

    This is intentionally descriptive. QRI-inspired descriptors are predictors, not definitions of
    valence; retrospective rasa labels are response categories, not measurements of classical rasa.
    """
    desc_keys=('symmetry','spectral_entropy','entropy','occupancy','contrast','edge','centroid_offset')
    seq_keys=('symmetry_gradient_abs','symmetry_recovery_fraction','temporal_change_proxy')
    rows=[]
    with conn() as c:
        responses=[dict(r) for r in c.execute('SELECT * FROM experiment_responses WHERE experiment_id=?',(exp_id,))]
        for r in responses:
            st=c.execute("SELECT metadata_json FROM events WHERE phenotype_id=? AND session_id=? AND event_type='structural' ORDER BY created_at DESC LIMIT 1",(r['phenotype_id'],r['session_id'])).fetchone()
            if not st:
                st=c.execute("SELECT metadata_json FROM events WHERE phenotype_id=? AND event_type='structural' ORDER BY created_at DESC LIMIT 1",(r['phenotype_id'],)).fetchone()
            sq=c.execute("SELECT metadata_json FROM events WHERE phenotype_id=? AND session_id=? AND event_type='structural_sequence' ORDER BY created_at DESC LIMIT 1",(r['phenotype_id'],r['session_id'])).fetchone()
            try:m=json.loads(st[0]) if st else {}
            except:m={}
            try:q=json.loads(sq[0]) if sq else {}
            except:q={}
            rec={'valence':r['valence'],'arousal':r['arousal'],'absorption':r['absorption'],'rasa_label':r['rasa_label']}
            for k in desc_keys:
                if isinstance(m.get(k),(int,float)):rec[k]=float(m[k])
            for k in seq_keys:
                if isinstance(q.get(k),(int,float)):rec[k]=float(q[k])
            rows.append(rec)
    predictors=desc_keys+seq_keys;outcomes=('valence','arousal','absorption')
    corr={}
    for p in predictors:
        corr[p]={}
        for o in outcomes:
            pairs=[(r[p],r[o]) for r in rows if isinstance(r.get(p),(int,float)) and isinstance(r.get(o),(int,float))]
            v=_pearson([x for x,_ in pairs],[y for _,y in pairs])
            corr[p][o]={'r':None if v is None else round(v,4),'n':len(pairs)}
    rasa={}
    for label in sorted({r.get('rasa_label') for r in rows if r.get('rasa_label')}):
        group=[r for r in rows if r.get('rasa_label')==label];z={'n':len(group)}
        for k in predictors+outcomes:
            vals=[r[k] for r in group if isinstance(r.get(k),(int,float))]
            if vals:z[k]=round(sum(vals)/len(vals),4)
        rasa[label]=z
    return {'experiment_id':exp_id,'n_responses':len(rows),'status':'exploratory',
            'note':'descriptive correlations only; QRI-inspired structure variables are hypotheses, and rasa labels are retrospective response categories',
            'correlations':corr,'rasa_groups':rasa}


def commonization_report(exp_id='commonization-v1'):
    """Compare particular vs commonized framing for identically generated phenotypes."""
    arms={'particular':[],'commonized':[]}
    with conn() as c:
        assigns=[dict(r) for r in c.execute('SELECT * FROM study_assignments WHERE study_id=?',(exp_id,))]
        responses=[dict(r) for r in c.execute('SELECT * FROM experiment_responses WHERE experiment_id=?',(exp_id,))]
        resp={(r['session_id'],r['phenotype_id']):r for r in responses}
        for a in assigns:
            arm='commonized' if str(a['arm']).endswith('|commonized') else 'particular'
            ev=[dict(r) for r in c.execute('SELECT event_type,value,metadata_json FROM events WHERE session_id=? AND phenotype_id=?',(a['session_id'],a['phenotype_id']))]
            # Keep only events explicitly tagged with this study when metadata exists.
            filt=[]
            for e in ev:
                try:md=json.loads(e['metadata_json'] or '{}')
                except:md={}
                if md.get('study_id') in (None,exp_id):filt.append(e)
            types={}
            for e in filt:types.setdefault(e['event_type'],[]).append(e['value'])
            r=resp.get((a['session_id'],a['phenotype_id']))
            rec={'horizon_5':1.0 if 'horizon_5' in types else 0.0,
                 'horizon_10':1.0 if 'horizon_10' in types else 0.0,
                 'horizon_20':1.0 if 'horizon_20' in types else 0.0,
                 'replay':float(len(types.get('replay',[]))),
                 'favorite':float(len(types.get('favorite',[])))}
            dwell=[x for x in types.get('dwell',[]) if isinstance(x,(int,float))]
            rec['dwell_s']=sum(dwell)/len(dwell)/1000 if dwell else None
            if r:rec.update({'valence':r['valence'],'arousal':r['arousal'],'absorption':r['absorption'],'rasa_label':r['rasa_label']})
            arms[arm].append(rec)
    metrics=('horizon_5','horizon_10','horizon_20','dwell_s','replay','favorite','valence','arousal','absorption')
    summary={}
    for arm,items in arms.items():
        z={'n':len(items)}
        for k in metrics:
            vals=[r[k] for r in items if isinstance(r.get(k),(int,float))]
            z[k]=None if not vals else round(sum(vals)/len(vals),4)
        summary[arm]=z
    delta={}
    for k in metrics:
        a=summary['commonized'].get(k);b=summary['particular'].get(k)
        delta[k]=None if a is None or b is None else round(a-b,4)
    return {'experiment_id':exp_id,'status':'exploratory','arms':summary,'commonized_minus_particular':delta,
            "note":"randomized first-party framing contrast; operational analogy to commonization/sadharanikarana, not a direct measurement of Abhinavagupta's construct"}

def experiment_report(exp_id='attention-rasa-v2'):
    with conn() as c:
        rr=[dict(r) for r in c.execute('SELECT * FROM experiment_responses WHERE experiment_id=?',(exp_id,))]
        vids=[r[0] for r in c.execute('SELECT video_id FROM youtube_videos WHERE experiment_id=?',(exp_id,))]
    vals=[r['valence'] for r in rr if r['valence'] is not None]
    absor=[r['absorption'] for r in rr if r['absorption'] is not None]
    labels={}
    for r in rr:
        if r['rasa_label']:labels[r['rasa_label']]=labels.get(r['rasa_label'],0)+1
    return {
      'experiment_id':exp_id,'n_responses':len(rr),'mean_valence':_mean(vals),'mean_absorption':_mean(absor),
      'rasa_labels':labels,'youtube':[x for x in (youtube_fitness(v) for v in vids) if x]
    }


def _mean(xs):return None if not xs else sum(xs)/len(xs)
