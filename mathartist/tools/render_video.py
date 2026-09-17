#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from archive import init_db,conn,get_phenotype

def main():
    ap=argparse.ArgumentParser(description='Render a MathArtist phenotype with the exact browser source renderer and encode MP4.')
    ap.add_argument('phenotype',help='phenotype id or JSON file');ap.add_argument('--out');ap.add_argument('--seconds',type=float,default=30);ap.add_argument('--fps',type=int,default=10);ap.add_argument('--size',type=int,default=512);args=ap.parse_args()
    if not shutil.which('node'):raise SystemExit('node is required')
    if not shutil.which('ffmpeg'):raise SystemExit('ffmpeg is required')
    pth=Path(args.phenotype)
    if pth.exists():ph=json.loads(pth.read_text())
    else:
        init_db()
        with conn() as c:ph=get_phenotype(c,args.phenotype)
        if not ph:raise SystemExit(f'unknown phenotype: {args.phenotype}')
    out=Path(args.out or f"{ph['id']}.mp4").resolve();frames=max(1,round(args.seconds*args.fps))
    with tempfile.TemporaryDirectory(prefix='mathartist-frames-') as td:
        td=Path(td);pf=td/'phenotype.json';pf.write_text(json.dumps(ph))
        subprocess.run(['node',str(ROOT/'tools/render_frames.cjs'),str(ROOT),str(pf),str(td/'frames'),str(args.size),str(args.fps),str(frames)],check=True)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(args.fps),'-i',str(td/'frames/frame-%05d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
    print(out)
if __name__=='__main__':main()
