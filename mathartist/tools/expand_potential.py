#!/usr/bin/env python3
"""Expand around POTENTIAL phenotypes: spawn a local cloud of descendants.

Usage:
  python tools/expand_potential.py ns26-063a403fa2 --count 256 --sigma 0.7 --seed 1
  python tools/expand_potential.py --list-potential --source NS26 --count 10

For each marked POTENTIAL phenotype, creates a configurable local mutation cloud
(default 256 descendants, sigma 0.7). Preserves parent-child lineage and exact
seed/control provenance. Writes population JSON and optionally renders contact sheet.

This is the CLI equivalent of what the dashboard POTENTIAL→BRANCH button does.
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
from aesthetics.viability import gate


def list_potential(source_id, count=10):
    """List the most recently marked POTENTIAL phenotypes for a source."""
    with archive.conn() as c:
        rows = c.execute(
            "SELECT phenotype_id, MAX(created_at) t FROM events "
            "WHERE event_type='potential' AND value>0 "
            "GROUP BY phenotype_id ORDER BY t DESC LIMIT ?",
            (count * 4,),
        ).fetchall()
        out = [archive.get_phenotype(c, r[0]) for r in rows]
        return [x for x in out if x and x["source_id"] == source_id][:count]


def expand_phenotype(pid, count=256, seed=1):
    """Create a local cloud around one phenotype."""
    with archive.conn() as c:
        p = archive.get_phenotype(c, pid)
        if not p:
            raise SystemExit(f"phenotype {pid} not found")
    rng_base = seed
    pop = archive.create_population(
        p["source_id"], "frontier", count,
        selected_ids=[pid], seed=rng_base,
    )
    # classify by novelty distance from parent
    parent_genome = p["genome"]
    for ph in pop:
        dist = 0.0
        surface = {}
        try:
            from controlsurface.engine import surface_for_spec
            specs = archive.load_specs()
            surface = surface_for_spec(specs[ph["source_id"]], ph["source_variant"])
        except Exception:
            pass
        for k in surface:
            d = surface[k]
            pv = parent_genome.get(k, 0)
            cv = ph["genome"].get(k, 0)
            if d.get("type") in ("float", "int"):
                span = max(1e-12, float(d.get("max", 1)) - float(d.get("min", 0)))
                dist += ((float(pv) - float(cv)) / span) ** 2
            elif d.get("type") == "enum":
                dist += 0 if pv == cv else 1
        ph["parent_distance"] = round(math.sqrt(dist / max(1, len(surface))), 4)
    return pop, p


def render_contact_sheet(pop, out_dir, parent_id=None, width=128, times="9"):
    """Render population and produce a contact sheet PNG."""
    frames = out_dir / "frames"
    frames.mkdir(exist_ok=True)
    pop_file = out_dir / "pop.json"
    pop_file.write_text(json.dumps(pop))
    subprocess.run(
        ["node", str(ROOT / "tools/render_population.cjs"),
         str(ROOT), str(pop_file), str(frames), str(width), times],
        check=True, cwd=ROOT, stdout=subprocess.DEVNULL,
    )
    # contact sheet
    from PIL import Image, ImageDraw
    T = width
    cols = min(12, len(pop))
    rows = math.ceil(len(pop) / cols)
    header = 42
    sheet = Image.new("RGB", (cols * T, header + rows * T), (3, 3, 3))
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), f"EXPAND POTENTIAL  |  {len(pop)} descendants of {parent_id or '?'}",
           fill=(218, 218, 218))
    d.text((10, 25), "blind expansion · human decides POTENTIAL",
           fill=(110, 110, 110))
    for i, ph in enumerate(pop):
        p = frames / ph["id"] / "t0.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB").resize((T, T))
        x = (i % cols) * T
        y = header + (i // cols) * T
        sheet.paste(im, (x, y))
        d.text((x + 4, y + 4), f"{ph['source_variant'][:8]} n={ph.get('parent_distance', 0):.2f}",
               fill=(170, 190, 170))
    out_png = out_dir / "contact-sheet.png"
    sheet.save(out_png)
    shutil.rmtree(frames, ignore_errors=True)
    return out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phenotype_id", nargs="?", help="phenotype ID to expand around")
    ap.add_argument("--list-potential", action="store_true")
    ap.add_argument("--source", default="NS26")
    ap.add_argument("--count", type=int, default=256)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()

    archive.init_db()

    if a.list_potential:
        potentials = list_potential(a.source, a.count)
        for p in potentials:
            print(json.dumps({"id": p["id"], "variant": p["source_variant"],
                              "gen": p["generation"], "parents": p["parent_ids"]}))
        print(f"total: {len(potentials)}")
        return

    if not a.phenotype_id:
        ap.error("provide a phenotype_id or use --list-potential")

    pop, parent = expand_phenotype(a.phenotype_id, a.count, a.seed)
    out_dir = Path(a.out or (ROOT / "docs" / "benchmarks" / "v3.3-corpus" / f"expand-{a.phenotype_id[:20]}"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "population.json").write_text(json.dumps(pop, indent=2))
    (out_dir / "parent.json").write_text(json.dumps(parent, indent=2))

    if a.render:
        png = render_contact_sheet(pop, out_dir, a.phenotype_id)
        print(f"contact sheet: {png}")
    else:
        print(f"wrote {len(pop)} phenotypes to {out_dir}")

    # fertility report
    by_variant = {}
    for ph in pop:
        by_variant.setdefault(ph["source_variant"], []).append(ph)
    report = {"parent": a.phenotype_id, "source": parent["source_id"],
              "count": len(pop), "by_variant": {}}
    for v, ps in by_variant.items():
        dists = [ph.get("parent_distance", 0) for ph in ps]
        report["by_variant"][v] = {
            "n": len(ps),
            "mean_distance": round(float(np.mean(dists)), 4),
            "max_distance": round(float(np.max(dists)), 4),
        }
    (out_dir / "fertility.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
