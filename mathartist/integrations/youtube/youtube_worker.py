#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys
from datetime import date,timedelta,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from archive import init_db
from experiment_store import init_experiment_db,register_youtube_video,upsert_retention,youtube_fitness,sync_youtube_fitness_events

SCOPES=[
 'https://www.googleapis.com/auth/youtube.upload',
 'https://www.googleapis.com/auth/youtube.readonly',
 'https://www.googleapis.com/auth/yt-analytics.readonly',
]
PRIVATE=ROOT/'.private';TOKEN=PRIVATE/'youtube-token.json'

def clients():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as e:
        raise SystemExit('Install research extras first: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2') from e
    secret=os.getenv('MATHARTIST_YOUTUBE_CLIENT_SECRET')
    if not secret:raise SystemExit('Set MATHARTIST_YOUTUBE_CLIENT_SECRET=/path/to/client_secret.json')
    creds=None
    if TOKEN.exists():creds=Credentials.from_authorized_user_file(str(TOKEN),SCOPES)
    if creds and creds.expired and creds.refresh_token:creds.refresh(Request())
    if not creds or not creds.valid:
        flow=InstalledAppFlow.from_client_secrets_file(secret,SCOPES);creds=flow.run_local_server(port=0)
    PRIVATE.mkdir(exist_ok=True);TOKEN.write_text(creds.to_json())
    return build('youtube','v3',credentials=creds),build('youtubeAnalytics','v2',credentials=creds)

def rows_to_dict(result):
    names=[x['name'] for x in result.get('columnHeaders',[])]
    return [dict(zip(names,row)) for row in result.get('rows',[]) or []]

def fetch_retention(analytics,video_id,start_date,end_date):
    metrics='audienceWatchRatio,relativeRetentionPerformance,startedWatching,stoppedWatching,totalSegmentImpressions'
    result=analytics.reports().query(ids='channel==MINE',startDate=start_date,endDate=end_date,
      metrics=metrics,dimensions='elapsedVideoTimeRatio',filters=f'video=={video_id}',sort='elapsedVideoTimeRatio').execute()
    return rows_to_dict(result)

def main():
    ap=argparse.ArgumentParser(description='MathArtist YouTube wild-feedback worker')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('auth')
    u=sub.add_parser('upload');u.add_argument('mp4');u.add_argument('--phenotype',required=True);u.add_argument('--experiment',default='youtube-attention-v2');u.add_argument('--title');u.add_argument('--description',default='MathArtist experimental organism.');u.add_argument('--privacy',choices=['private','unlisted','public'],default='unlisted');u.add_argument('--duration',type=float,default=30)
    r=sub.add_parser('retention');r.add_argument('video_id');r.add_argument('--start');r.add_argument('--end')
    s=sub.add_parser('sync');s.add_argument('video_id');s.add_argument('--start');s.add_argument('--end')
    j=sub.add_parser('import-json');j.add_argument('video_id');j.add_argument('json_file')
    f=sub.add_parser('fitness');f.add_argument('video_id')
    args=ap.parse_args();init_db();init_experiment_db()
    if args.cmd=='fitness':print(json.dumps(youtube_fitness(args.video_id) or {},indent=2));return
    if args.cmd=='import-json':
        x=json.loads(Path(args.json_file).read_text());rows=x.get('rows',x) if isinstance(x,dict) else x;upsert_retention(args.video_id,rows);print(json.dumps(sync_youtube_fitness_events(args.video_id) or {},indent=2));return
    yt,ya=clients()
    if args.cmd=='auth':print(f'Authorized; token stored at {TOKEN} (gitignored).');return
    if args.cmd=='upload':
        from googleapiclient.http import MediaFileUpload
        body={'snippet':{'title':args.title or f'MathArtist {args.phenotype}','description':args.description,'categoryId':'28'},'status':{'privacyStatus':args.privacy}}
        res=yt.videos().insert(part='snippet,status',body=body,media_body=MediaFileUpload(args.mp4,chunksize=-1,resumable=True)).execute();vid=res['id']
        register_youtube_video(vid,args.phenotype,args.experiment,args.duration,{'privacy':args.privacy,'file':str(Path(args.mp4).name)})
        print(json.dumps({'video_id':vid,'phenotype_id':args.phenotype},indent=2));return
    end=args.end or str(date.today());start=args.start or str(date.today()-timedelta(days=28));rows=fetch_retention(ya,args.video_id,start,end)
    if args.cmd=='sync':upsert_retention(args.video_id,rows);print(json.dumps(sync_youtube_fitness_events(args.video_id) or {},indent=2))
    else:print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
