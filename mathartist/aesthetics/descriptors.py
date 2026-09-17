from __future__ import annotations
import io, math, zlib
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from PIL import Image


def _gray(image):
    if isinstance(image, (str, Path)):
        image=Image.open(image)
    if isinstance(image, Image.Image):
        a=np.asarray(image.convert('L'),dtype=np.float32)/255.0
    else:
        a=np.asarray(image,dtype=np.float32)
        if a.ndim==3:a=a[...,:3].mean(-1)
        if a.max()>1:a=a/255.0
    return np.clip(a,0,1)


def _corr(a,b):
    a=a.ravel().astype(float);b=b.ravel().astype(float)
    a-=a.mean();b-=b.mean();d=np.linalg.norm(a)*np.linalg.norm(b)
    return 0.0 if d<1e-12 else float(np.dot(a,b)/d)


def symmetry_group(a):
    """Approximate stabilizer similarities for simple D4 image actions."""
    return {
      'sym_lr': _corr(a,np.fliplr(a)),
      'sym_ud': _corr(a,np.flipud(a)),
      'sym_rot180': _corr(a,np.rot90(a,2)),
      'sym_rot90': _corr(a,np.rot90(a,1)),
    }


def spectral_entropy(a):
    a=a-a.mean();p=np.abs(np.fft.rfft2(a))**2
    p[0,0]=0;s=p.sum()
    if s<=1e-16:return 0.0
    p=p.ravel()/s;p=p[p>0]
    return float(-(p*np.log2(p)).sum()/max(1e-12,math.log2(len(p))))


def compressibility(a):
    u=np.clip(np.rint(a*255),0,255).astype(np.uint8).tobytes()
    if not u:return 0.0
    return float(1-len(zlib.compress(u,9))/len(u))


def descriptor(image, threshold=None):
    a=_gray(image)
    if max(a.shape)>128:
        a=np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((96,96),Image.Resampling.BILINEAR),dtype=np.float32)/255
    mean=float(a.mean());std=float(a.std());threshold=max(.014,mean+.65*std) if threshold is None else float(threshold)
    mask=a>threshold;occ=float(mask.mean())
    sat=float((a>.96).mean())
    if mask.any():
        ys,xs=np.nonzero(mask);h,w=a.shape
        bbox=((xs.max()-xs.min()+1)*(ys.max()-ys.min()+1))/(h*w)
        weights=a[mask]+1e-6
        cx=float((xs*weights).sum()/weights.sum());cy=float((ys*weights).sum()/weights.sum())
        centroid=float(math.hypot((cx-(w-1)/2)/(w/2),(cy-(h-1)/2)/(h/2)))
    else:bbox=0.0;centroid=1.0
    gx=np.abs(np.diff(a,axis=1)).mean() if a.shape[1]>1 else 0
    gy=np.abs(np.diff(a,axis=0)).mean() if a.shape[0]>1 else 0
    s=symmetry_group(a)
    return {
      **{k:round(float(v),5) for k,v in s.items()},
      'symmetry_best':round(max(s.values()),5),
      'foreground_threshold':round(float(threshold),5),'occupancy':round(occ,5),'bbox_area_ratio':round(float(bbox),5),'centroid_offset':round(centroid,5),
      'mean':round(mean,5),'contrast':round(std,5),'saturation_fraction':round(sat,5),'edge_density':round(float((gx+gy)/2),5),
      'spectral_entropy':round(spectral_entropy(a),5),'compressibility':round(compressibility(a),5)
    }


def recurrence(images):
    frames=[_gray(x) for x in images]
    if len(frames)<2:return {'recurrence_mean':None,'change_mean':None}
    vals=[];chg=[]
    for a,b in zip(frames,frames[1:]):
        if a.shape!=b.shape:b=np.asarray(Image.fromarray((b*255).astype(np.uint8)).resize((a.shape[1],a.shape[0])),dtype=np.float32)/255
        vals.append(_corr(a,b));chg.append(float(np.mean(np.abs(a-b))))
    return {'recurrence_mean':round(float(np.mean(vals)),5),'change_mean':round(float(np.mean(chg)),5)}


def sequence_descriptor(images):
    ds=[descriptor(x) for x in images]
    out={}
    for k in ds[0]:
        vals=[d[k] for d in ds if isinstance(d[k],(int,float))]
        out[k+'_mean']=round(float(np.mean(vals)),5)
        out[k+'_std']=round(float(np.std(vals)),5)
    out.update(recurrence(images))
    if len(ds)>1:
        sym=[d['symmetry_best'] for d in ds]
        grad=np.diff(sym)
        out['symmetry_gradient_abs']=round(float(np.mean(np.abs(grad))),5)
        out['symmetry_recovery_fraction']=round(float(np.mean(grad[1:]*grad[:-1]<0)) if len(grad)>1 else 0.0,5)
    return out
