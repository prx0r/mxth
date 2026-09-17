#!/usr/bin/env python3
"""Generate deterministic source trajectories used by the browser.

These are SOURCE states, not evolved images. Evolution only changes interpretation.

Lenia source:
- Equations and Orbium bicaudatus seed/parameters from Bert Chan's MIT Lenia reference,
  R/Lenia.Rmd. This generator uses the scale-equivalent 64x64 / R=13 form of the
  reference 256x256 / R=52 run.

Bioelectric source:
- Independent equation-level port of the cellular-field-network equations documented in
  Manicka & Levin's ElectricMorphogenesis repository (2025). No upstream Python code is
  copied. We fix the repository's documented default physical parameters and use its
  explicitly demonstrated initial conditions. The pretrained/learned clamp pickle is not
  bundled, so these variants are labeled EXACT-EQUATIONS rather than exact reproduction
  of a trained-paper figure.

NS26 source (DERIVED):
- Frozen similarity-scale scaffold from the selected relations of the 2026 forced
  Navier-Stokes blow-up construction (radial tau^1/2, axial tau^(1/2-h),
  velocity tau^(-1/2-h), h=0.006). This is NOT the full proof object: it freezes the
  quasi-random particle scaffold (u, eta, X) and the per-frame similarity scales
  (tau/rs/zs/vel schedule) so the browser observes identical source bytes every run.
  All genome controls are observation-only (camera, tone mapping, sampling, playback).
"""
from __future__ import annotations
from pathlib import Path
import json, math
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'app'/'static'/'data'

# Exact 20x20 Orbium bicaudatus seed from Chakazul/Lenia R/Lenia.Rmd (column-major R matrix).
ORB_SEED = [
0,0,0,0,0,0,.1,.14,.1,0,0,.03,.03,0,0,.3,0,0,0,0,
0,0,0,0,0,.08,.24,.3,.3,.18,.14,.15,.16,.15,.09,.2,0,0,0,0,
0,0,0,0,0,.15,.34,.44,.46,.38,.18,.14,.11,.13,.19,.18,.45,0,0,0,
0,0,0,0,.06,.13,.39,.5,.5,.37,.06,0,0,0,.02,.16,.68,0,0,0,
0,0,0,.11,.17,.17,.33,.4,.38,.28,.14,0,0,0,0,0,.18,.42,0,0,
0,0,.09,.18,.13,.06,.08,.26,.32,.32,.27,0,0,0,0,0,0,.82,0,0,
.27,0,.16,.12,0,0,0,.25,.38,.44,.45,.34,0,0,0,0,0,.22,.17,0,
0,.07,.2,.02,0,0,0,.31,.48,.57,.6,.57,0,0,0,0,0,0,.49,0,
0,.59,.19,0,0,0,0,.2,.57,.69,.76,.76,.49,0,0,0,0,0,.36,0,
0,.58,.19,0,0,0,0,0,.67,.83,.9,.92,.87,.12,0,0,0,0,.22,.07,
0,0,.46,0,0,0,0,0,.7,.93,1,1,1,.61,0,0,0,0,.18,.11,
0,0,.82,0,0,0,0,0,.47,1,1,.98,1,.96,.27,0,0,0,.19,.1,
0,0,.46,0,0,0,0,0,.25,1,1,.84,.92,.97,.54,.14,.04,.1,.21,.05,
0,0,0,.4,0,0,0,0,.09,.8,1,.82,.8,.85,.63,.31,.18,.19,.2,.01,
0,0,0,.36,.1,0,0,0,.05,.54,.86,.79,.74,.72,.6,.39,.28,.24,.13,0,
0,0,0,.01,.3,.07,0,0,.08,.36,.64,.7,.64,.6,.51,.39,.29,.19,.04,0,
0,0,0,0,.1,.24,.14,.1,.15,.29,.45,.53,.52,.46,.4,.31,.21,.08,0,0,
0,0,0,0,0,.08,.21,.21,.22,.29,.36,.39,.37,.33,.26,.18,.09,0,0,0,
0,0,0,0,0,0,.03,.13,.19,.22,.24,.24,.23,.18,.13,.05,0,0,0,0,
0,0,0,0,0,0,0,0,.02,.06,.08,.09,.07,.05,.01,0,0,0,0,0]
assert len(ORB_SEED)==400

def generate_lenia():
    out=STATIC/'lenia'; out.mkdir(parents=True,exist_ok=True)
    N,R,MU,SIGMA,DT=64,13,.15,.014,.1
    seed=np.asarray(ORB_SEED,dtype=np.float64).reshape((20,20),order='F')
    A=np.zeros((N,N),dtype=np.float64)
    A[N//2-10:N//2+10,N//2-10:N//2+10]=seed
    q=np.arange(N); q=np.where(q<N/2,q,q-N)
    yy,xx=np.meshgrid(q,q,indexing='ij'); r=np.hypot(xx,yy)/R
    # R/Lenia.Rmd kernel.type=0: (4 r (1-r))^4, shell peak [1]
    kernel=np.where(r<1,(4*r*(1-r))**4,0.0); kernel/=kernel.sum()
    K=np.fft.fft2(kernel)
    frames=[]; total_steps=720; stride=6
    for gen in range(total_steps):
        if gen%stride==0: frames.append(np.rint(np.clip(A,0,1)*255).astype(np.uint8))
        potential=np.fft.ifft2(K*np.fft.fft2(A)).real
        # R/Lenia.Rmd delta.type=0: compact quartic growth
        growth=np.maximum(0.0,1.0-(potential-MU)**2/(SIGMA**2*9.0))**4*2.0-1.0
        A=np.clip(A+growth*DT,0.0,1.0)
    arr=np.stack(frames)
    (out/'orbium.u8.bin').write_bytes(arr.tobytes(order='C'))
    meta={"id":"orbium","n":N,"frames":len(frames),"dtype":"uint8","stride_steps":stride,"source_dt":DT,
          "source":"Chakazul/Lenia R/Lenia.Rmd","R":R,"mu":MU,"sigma":SIGMA,"dt":DT,
          "kernel":"(4r(1-r))^4 for r<1","growth":"2*max(0,1-(u-mu)^2/(9 sigma^2))^4-1"}
    (out/'orbium.json').write_text(json.dumps(meta,indent=2))
    return meta

class Bioelectric:
    """Independent numpy port of the documented cellular-field equations."""
    def __init__(self, variant):
        self.rows=self.cols=11; self.N=121; self.fr=5e-6; self.dt=.01
        self.Z=3; self.Vth=-27e-3; self.VT=27e-3; self.V0=12e-3; self.C=.1e-9
        self.Epol=-55e-3; self.Edep=-5e-3; self.Gref=1e-9; self.G0=.05*self.Gref
        self.ke=8.987e9; self.epsr=1e7; self.field_const=self.ke/self.epsr
        self.Gdep=np.full(self.N,1.5*self.Gref); self.Gpol=np.full(self.N,self.Gref)
        self.ft_bias=.0005; self.ft_weight=1000.; self.ft_gain=-1.; self.ft_tc=10.
        self.coords=np.asarray([((r*2+1)*self.fr,(c*2+1)*self.fr) for r in range(11) for c in range(11)])
        self.fcoords=np.asarray([(r*2*self.fr,c*2*self.fr) for r in range(12) for c in range(12)])
        self.dx=self.fcoords[:,None,0]-self.coords[None,:,0]; self.dy=self.fcoords[:,None,1]-self.coords[None,:,1]
        dist=np.hypot(self.dx,self.dy)
        self.out=(dist <= self.fr*math.sqrt(2)*(4+.001))
        self.rinv2=np.where(self.out,1/np.maximum(dist,1e-30)**2,0.)
        self.ins=(dist <= self.fr*math.sqrt(2)*(1+.001)); self.incount=self.ins.sum(axis=0)
        self.adj=np.zeros((self.N,self.N),dtype=np.float64)
        for r in range(11):
            for c in range(11):
                i=r*11+c
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    rr,cc=r+dr,c+dc
                    if 0<=rr<11 and 0<=cc<11:self.adj[i,rr*11+cc]=1
        if variant=='center-hyperpolarized':
            self.V=np.zeros(self.N); self.V[60]=-.06
        elif variant=='french-flag':
            self.V=np.zeros(self.N);self.V[:44]=-.005;self.V[44:77]=-.03;self.V[77:]=-.06
        elif variant=='uniform-bistable':
            self.V=np.full(self.N,-9.2e-3)
        else: raise ValueError(variant)
    def sigmoid(self,x):
        return 1/(1+np.exp(-np.clip(x,-60,60)))
    def step(self):
        Q=self.C*self.V
        ex=self.field_const*((self.rinv2*self.dx)@Q)
        ey=self.field_const*((self.rinv2*self.dy)@Q)
        eV=np.sqrt(ex*ex+ey*ey+1e-15)
        eVmean=(eV[:,None]*self.ins).sum(axis=0)/self.incount
        dgp=10*(-self.Gpol+(2*self.sigmoid(self.ft_gain*eVmean+self.ft_bias)-1)*self.ft_weight)/self.ft_tc
        self.Gpol=np.clip(self.Gpol+self.dt*dgp*self.Gref,0,2*self.Gref)
        pin=1/(1+np.exp(np.clip(self.Z*(self.V-self.Vth)/self.VT,-60,60)))
        pout=1/(1+np.exp(np.clip(-self.Z*(self.V-self.Vth)/self.VT,-60,60)))
        ich=-self.Gpol*(self.V-self.Epol)*pin-self.Gdep*(self.V-self.Edep)*pout
        dv=self.V[:,None]-self.V[None,:]
        gij=(2*self.G0/(1+np.cosh(np.clip(dv/self.V0,-60,60))))*self.adj
        gap=gij@self.V-gij.sum(axis=1)*self.V
        current=ich+gap
        self.V=self.V+(current/self.C)*self.dt
        return self.V.copy(),eV.astype(np.float64),ex.astype(np.float64),ey.astype(np.float64),current.copy()

def generate_bioelectric():
    out=STATIC/'bioelectric'; out.mkdir(parents=True,exist_ok=True)
    metas=[]
    for variant in ('center-hyperpolarized','french-flag','uniform-bistable'):
        sim=Bioelectric(variant); frames=[]; total_steps=2400; stride=12
        for i in range(total_steps):
            V,eV,ex,ey,current=sim.step()
            if i%stride==0:
                # Fixed record layout per frame: Vmem[121], eV[144], Ex[144], Ey[144], current[121]
                frames.append(np.concatenate([V,eV,ex,ey,current]).astype('<f4'))
        arr=np.stack(frames)
        path=out/f'{variant}.f32.bin';path.write_bytes(arr.tobytes(order='C'))
        meta={"id":variant,"cells":121,"cell_side":11,"field_points":144,"field_side":12,"frames":len(frames),
              "dtype":"float32-le","stride_steps":stride,"source_dt":sim.dt,"record":["Vmem:121","eV:144","Ex:144","Ey:144","current:121"],
              "source":"Manicka & Levin 2025 ElectricMorphogenesis equation-level reimplementation",
              "parameters":{"Z":3,"V_th":-0.027,"V_T":0.027,"V_0":0.012,"C":1e-10,"E_pol":-0.055,"E_dep":-0.005,
                            "G_ref":1e-9,"GJStrength":0.05,"fieldStrength":1.0,"fieldScreenSize":4,"fieldTransductionBias":0.0005,
                            "fieldTransductionWeight":1000.0,"fieldTransductionGain":-1.0,"fieldTransductionTimeConstant":10.0}}
        (out/f'{variant}.json').write_text(json.dumps(meta,indent=2));metas.append(meta)
    return metas

def generate_ns26():
    """Freeze the DERIVED Navier-Stokes similarity scaffold.

    Frozen source bytes:
      base.f32.bin  — N particles x [u, eta, X] float32-LE quasi-random scaffold.
      schedule.json — F-frame similarity schedule (tau/rs/zs/vel) + base sha256.
    The browser observer (ns26.js + frozen ns26_core.js) may only read these bytes
    plus observation-only genome controls. h, exponents and scaffold are immutable.
    """
    import hashlib
    out = STATIC / 'ns26'
    out.mkdir(parents=True, exist_ok=True)
    H = 0.006
    N, F = 8192, 120
    PHI1, PHI2 = 0.61803398875, 0.754877666
    base = np.zeros((N, 3), dtype=np.float64)
    for i in range(N):
        base[i, 0] = i / N
        base[i, 1] = 2 * ((i * PHI1) % 1) - 1
        base[i, 2] = 0.03 + 5 * ((i * PHI2) % 1)
    raw = base.astype('<f4').tobytes(order='C')
    (out / 'base.f32.bin').write_bytes(raw)
    tau, rs, zs, vel = [], [], [], []
    for j in range(F):
        t = 0.018 + 0.22 * (0.5 + 0.5 * math.sin(math.tau * j / F + 0.4))
        tau.append(t)
        rs.append(math.sqrt(t))
        zs.append(t ** (0.5 - H))
        vel.append(t ** (-0.5 - H))
    meta = {
        "id": "ns26-similarity-scaffold",
        "provenance_level": "DERIVED",
        "frames": F, "fps": 8,
        "h": H,
        "scales": {"radial": "tau^(1/2)", "axial": "tau^(1/2-h)", "velocity": "tau^(-1/2-h)"},
        "tau": tau, "rs": rs, "zs": zs, "vel": vel,
        "base": {
            "file": "app/static/data/ns26/base.f32.bin",
            "count": N, "record": "[u, eta, X] float32-LE",
            "u": "i/N", "eta": "2*frac(i*0.61803398875)-1", "X": "0.03+5*frac(i*0.754877666)",
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "source": "selected similarity-scale relations of the 2026 forced Navier-Stokes blow-up construction; not the full proof object",
        "generator": "tools/generate_trajectories.py::generate_ns26",
    }
    (out / 'schedule.json').write_text(json.dumps(meta))
    return {"frames": F, "particles": N, "bytes": len(raw)}


if __name__=='__main__':
    print('Lenia',generate_lenia())
    print('Bioelectric', [m['id'] for m in generate_bioelectric()])
    print('NS26',generate_ns26())
