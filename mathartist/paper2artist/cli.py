from __future__ import annotations
import argparse,json
from pathlib import Path
from .inspect_paper2agent import inspect
from .register import register_manifest

def main():
    ap=argparse.ArgumentParser(prog='paper2artist',description='Bridge verified Paper2Agent outputs into immutable MathArtist source bundles.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('inspect');a.add_argument('paper2agent_output');a.add_argument('--out',default='paper2artist-inspection.json')
    b=sub.add_parser('register');b.add_argument('manifest')
    args=ap.parse_args()
    if args.cmd=='inspect':
        x=inspect(Path(args.paper2agent_output));Path(args.out).write_text(json.dumps(x,indent=2)+'\n');print(args.out)
    else:
        print(json.dumps(register_manifest(Path(args.manifest)),indent=2))
if __name__=='__main__':main()
