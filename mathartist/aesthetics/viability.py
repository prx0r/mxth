from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=json.loads((ROOT/'aesthetics/integrity_gate.v3.1.json').read_text())

def gate(m, grammar=DEFAULT):
    """Technical observation integrity only; never an aesthetic filter."""
    c=grammar['limits'];reasons=[]
    for k in ('occupancy','mean'):
        lo,hi=c[k];v=float(m.get(k,0))
        if v<lo:reasons.append(k+':low')
        elif v>hi:reasons.append(k+':high')
    if float(m.get('contrast',0))<c['contrast_min']:reasons.append('low-contrast')
    if float(m.get('saturation_fraction',1))>c['saturation_fraction_max']:reasons.append('overexposed')
    return {'grammar':grammar['id'],'pass':not reasons,'reasons':reasons}
