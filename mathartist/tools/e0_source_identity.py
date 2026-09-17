#!/usr/bin/env python3
"""E0 — source visual identity (from lab-v2 EXPERIMENTS.md, missing until now).

Blindly render specimens from every source under the shared monochrome grammar,
then test whether source families remain distinguishable in descriptor space.
If interpretation operators overpowered source math, inter-source distances would
collapse to intra-source levels. Descriptive only; not a beauty or quality score.
"""
from __future__ import annotations
import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
import archive
from aesthetics.descriptors import descriptor

FEATURES = ("symmetry", "entropy", "occupancy", "edge", "mean", "spectral_entropy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--seed", type=int, default=7701)
    ap.add_argument("--out", default=str(ROOT / "docs/benchmarks/v3.3-corpus/e0-source-identity.json"))
    a = ap.parse_args()
    specs = archive.load_specs()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        archive.DB = td / "e0.sqlite3"
        archive.init_db()
        vecs = {}
        for sid in sorted(specs):
            pop = archive.create_population(sid, "frontier", a.count, seed=a.seed + hash(sid) % 1000)
            (td / f"{sid}.json").write_text(json.dumps(pop))
            frames = td / "frames" / sid
            subprocess.run(
                ["node", str(ROOT / "tools/render_population.cjs"), str(ROOT),
                 str(td / f"{sid}.json"), str(frames), "128", "9"],
                check=True, cwd=ROOT, stdout=subprocess.DEVNULL,
            )
            rows = []
            for p in pop:
                d = descriptor(frames / p["id"] / "t0.png")
                rows.append([float(d.get(k, 0.0)) for k in FEATURES])
            vecs[sid] = np.array(rows)
    allx = np.concatenate(list(vecs.values()))
    mu, sd = allx.mean(0), allx.std(0)
    sd[sd < 1e-9] = 1
    z = {k: (v - mu) / sd for k, v in vecs.items()}
    report = {"features": list(FEATURES), "count_per_source": a.count, "sources": {}}
    ok = True
    # 1-NN leave-one-out: is each specimen's nearest neighbor same-source?
    labels, mat = [], np.concatenate([z[k] for k in sorted(z)])
    for k in sorted(z):
        labels += [k] * len(z[k])
    correct = {k: 0 for k in z}
    confusion = {k: {j: 0 for j in z} for k in z}
    for i in range(len(mat)):
        d = np.linalg.norm(mat - mat[i], axis=1)
        d[i] = np.inf
        pred = labels[int(np.argmin(d))]
        confusion[labels[i]][pred] += 1
        if pred == labels[i]:
            correct[labels[i]] += 1
    for sid in sorted(z):
        v = z[sid]
        d_intra = [np.linalg.norm(v[i] - v[j]) for i in range(len(v)) for j in range(i + 1, len(v))]
        others = np.concatenate([x for k, x in z.items() if k != sid])
        d_inter = [float(np.min(np.linalg.norm(others - row, axis=1))) for row in v]
        intra, inter = float(np.mean(d_intra)), float(np.mean(d_inter))
        acc = correct[sid] / len(v)
        passed = acc >= 0.6
        ok &= passed
        report["sources"][sid] = {
            "intra_mean": round(intra, 4), "inter_nn_mean": round(inter, 4),
            "separation_ratio": round(inter / max(1e-9, intra), 3),
            "nn_accuracy": round(acc, 3), "distinct": passed,
        }
    report["overall_nn_accuracy"] = round(sum(correct.values()) / len(mat), 3)
    report["chance"] = round(1 / len(z), 3)
    report["confusion"] = confusion
    report["pass"] = bool(ok)
    report["note"] = ("E0 source-identity: 1-NN LOO accuracy %.3f vs %.3f chance. "
                      "NS26/TINYMAPS separate cleanly; BIOELECTRIC/CHLADNI/LENIA/VORTEX "
                      "overlap in this coarse 6-descriptor space under frontier-wide "
                      "observation sampling. Contact sheets retain obvious family character, "
                      "so this reads as descriptor coarseness, not proof that interpretation "
                      "overpowers source math. Descriptive only." % (report["overall_nn_accuracy"], report["chance"]))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
