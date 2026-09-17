#!/usr/bin/env python3
"""Conservative numeric-literal candidate extractor for tiny p5/Processing programs.
It does NOT claim every literal is a valid mathematical control."""
import argparse,json,re,pathlib
NUM=re.compile(r'(?<![\w.])(-?(?:\d+\.\d*|\.\d+|\d+)(?:e[+-]?\d+)?)',re.I)
LOCK_CONTEXT=('createCanvas','background','stroke','frameRate','pixelDensity')
def extract(code):
 out=[]
 for i,m in enumerate(NUM.finditer(code)):
  s=max(0,m.start()-28);e=min(len(code),m.end()+28);ctx=code[s:e]
  role='observer_or_runtime' if any(k in ctx for k in LOCK_CONTEXT) else 'math_candidate'
  out.append({'id':i,'literal':m.group(1),'offset':m.start(),'role':role,'context':ctx})
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('file');a=p.parse_args();code=pathlib.Path(a.file).read_text();print(json.dumps(extract(code),indent=2))
