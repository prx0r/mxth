#!/usr/bin/env python3
from pathlib import Path
import json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
try:
    from scipy.special import jv, jn_zeros
except Exception:
    jv=jn_zeros=None
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'preview.png'
SIZE=176

def canvas(): return Image.new('L',(SIZE,SIZE),3)
def splat(im,x,y,q,size=1):
    if 0<=x<SIZE and 0<=y<SIZE:
        d=ImageDraw.Draw(im);v=int(max(0,min(255,55+200*q)));s=max(1,int(size));d.ellipse((x-s,y-s,x+s,y+s),fill=v)
def rotxy(x,y,a):
    c,s=math.cos(a),math.sin(a);return x*c-y*s,x*s+y*c

def lenia(seed):
    meta=json.loads((ROOT/'app/static/data/lenia/orbium.json').read_text());raw=np.fromfile(ROOT/'app/static/data/lenia/orbium.u8.bin',dtype=np.uint8).reshape(meta['frames'],meta['n'],meta['n'])
    A=raw[(seed*17)%meta['frames']]/255.;im=canvas();rng=random.Random(seed);a=rng.uniform(-math.pi,math.pi);zoom=rng.uniform(.85,1.45);gamma=rng.uniform(.45,1.6);ys,xs=np.nonzero(A>.035);vals=A[ys,xs];mass=vals.sum();cx=(xs*vals).sum()/mass;cy=(ys*vals).sum()/mass
    for x,y,v in zip(xs,ys,vals):
        dx,dy=rotxy(x-cx,y-cy,a);xx=SIZE/2+dx*(SIZE/meta['n'])*zoom;yy=SIZE/2+dy*(SIZE/meta['n'])*zoom;s=1+rng.random()*1.2;splat(im,xx,yy,v**gamma,s)
    return im

def proj(x,y,mode,a,zoom):
    X,Y=x-.5,y-.5
    if mode=='polar':
        th=(X+.5)*math.tau;r=.12+.82*(Y+.5);X=.5*r*math.cos(th);Y=.5*r*math.sin(th)
    elif mode=='fold':
        th=math.atan2(Y,X);r=math.hypot(X,Y);k=4;th=((th*k+math.pi)%(math.tau)-math.pi)/k;X,Y=r*math.cos(th),r*math.sin(th)
    X,Y=rotxy(X,Y,a);return SIZE/2+X*SIZE*.8*zoom,SIZE/2+Y*SIZE*.8*zoom

def bio(seed):
    rng=random.Random(seed);variants=['center-hyperpolarized','french-flag','uniform-bistable'];v=variants[seed%3];meta=json.loads((ROOT/f'app/static/data/bioelectric/{v}.json').read_text());rec=674;raw=np.fromfile(ROOT/f'app/static/data/bioelectric/{v}.f32.bin',dtype='<f4').reshape(meta['frames'],rec);f=raw[(seed*23)%meta['frames']];V=f[:121];e=f[121:265];ex=f[265:409];ey=f[409:553];I=f[553:];mode=['vmem','field','field-vector','current','contour'][seed%5];projection=['native','polar','fold'][(seed//2)%3];a=rng.uniform(-math.pi,math.pi);zoom=rng.uniform(.75,1.35);im=canvas()
    if mode in ('field','field-vector'):
        mx=max(1e-12,float(e.max()))
        for y in range(12):
            for x in range(12):
                i=y*12+x;q=max(0,min(1,float(e[i]/mx)))
                if q<.08:continue
                xx,yy=proj(x/11,y/11,projection,a,zoom)
                if mode=='field-vector':
                    ang=math.atan2(float(ey[i]),float(ex[i]))+a;ln=2+8*q;d=ImageDraw.Draw(im);lum=int(70+185*q);d.line((xx-math.cos(ang)*ln,yy-math.sin(ang)*ln,xx+math.cos(ang)*ln,yy+math.sin(ang)*ln),fill=lum,width=1)
                else:splat(im,xx,yy,q,1+q*2)
    else:
        for y in range(11):
            for x in range(11):
                i=y*11+x
                if mode=='current':q=min(1,math.log1p(abs(float(I[i]))*1e12)/math.log(40))
                else:q=max(0,min(1,(float(V[i])+.06)/.06))
                if mode=='contour':q=.5+.5*math.cos(q*math.tau*(3+seed%5))
                if q<.07:continue
                xx,yy=proj(x/10,y/10,projection,a,zoom);splat(im,xx,yy,q,1+2*q)
    return im

def chladni(seed):
    rng=random.Random(seed);im=canvas();square=seed%2==0;a=rng.uniform(-math.pi,math.pi);zoom=rng.uniform(.8,1.25);N=8500
    if square:m,n=[(2,3),(3,5),(4,7),(5,8)][seed%4]
    else:n,s=[(2,2),(3,2),(5,1),(6,2)][seed%4];alpha=float(jn_zeros(n,s)[-1]) if jn_zeros else 5
    for i in range(N):
        x=(i*.61803398875)%1;y=(i*.754877666)%1
        if square:amp=math.cos(n*math.pi*x)*math.cos(m*math.pi*y)-math.cos(m*math.pi*x)*math.cos(n*math.pi*y)
        else:
            dx=x*2-1;dy=y*2-1;r=math.hypot(dx,dy)
            if r>1:continue
            amp=float(jv(n,alpha*r))*math.cos(n*math.atan2(dy,dx)) if jv else math.sin(alpha*r)*math.cos(n*math.atan2(dy,dx))
        q=math.exp(-abs(amp)*(9+seed%14))
        if q<.25:continue
        X,Y=rotxy((x-.5)*zoom,(y-.5)*zoom,a);splat(im,SIZE/2+X*SIZE,SIZE/2+Y*SIZE,q,.65)
    return im

def ns(seed):
    rng=random.Random(seed);im=canvas()
    # Frozen source bytes (same schedule/scaffold the browser observes).
    sched=json.loads((ROOT/'app/static/data/ns26/schedule.json').read_text())
    base=np.fromfile(ROOT/'app/static/data/ns26/base.f32.bin',dtype='<f4').reshape(-1,3)
    fi=(seed*17)%sched['frames'];tau,rs,zs,vel=(sched[k][fi] for k in ('tau','rs','zs','vel'))
    phase=math.tau*fi/sched['frames']+8*vel*.025;t=8+seed*.7
    yaw=rng.uniform(-math.pi,math.pi);pitch=rng.uniform(-.8,.8);zoom=rng.uniform(.8,1.5);swirl=rng.uniform(.5,2);cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);N=min(7000,len(base))
    for i in range(N):
        u,eta,X=base[i];r=math.sqrt(2*tau*X)*rs*7;pulse=math.sin(eta*11+X*8-phase);aa=math.tau*u*31+swirl*vel*.015*t+.5*pulse;x=r*math.cos(aa);y=zs*eta*8+.16*pulse;z=r*math.sin(aa);x1=x*cy-z*sy;z1=x*sy+z*cy;y1=y*cp-z1*sp;z2=y*sp+z1*cp;per=1/(1+max(-.7,z2*.13));xx=SIZE/2+x1*SIZE*.15*zoom*per;yy=SIZE/2+y1*SIZE*.15*zoom*per;q=abs(pulse);splat(im,xx,yy,q,.55)
    return im

def main():
    funcs=[bio,lenia,chladni,ns];cols=10;rows=6;header=58;gap=1;W=cols*SIZE+(cols-1)*gap;H=header+rows*SIZE+(rows-1)*gap;sheet=Image.new('RGB',(W,H),(4,5,5));d=ImageDraw.Draw(sheet);d.text((14,14),'MATHARTIST LAB  /  IMMUTABLE SCIENCE -> EVOLVING PERCEPTION',fill=(205,210,208));d.text((14,33),'BIOELECTRIC   LENIA   CYMATICS   NS26    |    monochrome specimen field',fill=(72,78,75))
    for r in range(rows):
        for c in range(cols):
            idx=r*cols+c;fn=funcs[idx%4];im=fn(idx+11);x=c*(SIZE+gap);y=header+r*(SIZE+gap);sheet.paste(Image.merge('RGB',(im,im,im)),(x,y))
    OUT.parent.mkdir(exist_ok=True);sheet.save(OUT,quality=94);print(OUT)
if __name__=='__main__':main()
