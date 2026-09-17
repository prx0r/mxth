"""NS26 end-to-end source fixture: frozen bytes -> control surface -> render hash.

This is the reproducible adapter fixture: a recorded source bundle (schedule +
scaffold bytes + frozen core) plus an expected render hash for a fixed seed, so a
future change to any frozen byte fails loudly instead of drifting silently.
"""
import hashlib
import json
import math
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import archive
from controlsurface.engine import validate_control_surface
from source_bundles import bundle_manifest

SPEC = None


def spec():
    global SPEC
    if SPEC is None:
        SPEC = archive.load_specs()["NS26"]
    return SPEC


def test_ns26_control_surface_is_evidence_backed():
    s = spec()
    assert s["provenance_level"] == "DERIVED"
    assert validate_control_surface(s) == []
    surf = s["control_surface"]
    assert set(surf) == {
        "rotation", "pitch", "zoom", "threshold", "gamma", "exposure",
        "trail", "sample", "point_size", "time_rate", "swirl",
    }
    for name, d in surf.items():
        assert d.get("provenance"), name
        assert d["claim_scope"] == "observation-only", name


def test_ns26_frozen_bytes_match_schedule_record():
    sched = json.loads((ROOT / "app/static/data/ns26/schedule.json").read_text())
    raw = (ROOT / "app/static/data/ns26/base.f32.bin").read_bytes()
    rec = sched["base"]
    assert rec["count"] == 8192 and rec["bytes"] == len(raw)
    assert hashlib.sha256(raw).hexdigest() == rec["sha256"]
    assert sched["frames"] == 120 and len(sched["tau"]) == 120
    assert sched["h"] == 0.006 == spec()["immutable_core"]["h_demo"]


def test_ns26_schedule_math_is_frozen():
    """Independent recomputation of the similarity scales must match the bytes."""
    sched = json.loads((ROOT / "app/static/data/ns26/schedule.json").read_text())
    h = 0.006
    for j in (0, 1, 17, 119):
        tau = 0.018 + 0.22 * (0.5 + 0.5 * math.sin(math.tau * j / 120 + 0.4))
        assert sched["tau"][j] == pytest.approx(tau, rel=1e-12)
        assert sched["rs"][j] == pytest.approx(math.sqrt(tau), rel=1e-12)
        assert sched["zs"][j] == pytest.approx(tau ** (0.5 - h), rel=1e-12)
        assert sched["vel"][j] == pytest.approx(tau ** (-0.5 - h), rel=1e-12)


def test_ns26_scaffold_base_is_frozen():
    raw = (ROOT / "app/static/data/ns26/base.f32.bin").read_bytes()
    base = struct.unpack("<" + "f" * 8192 * 3, raw)
    for i in (0, 1, 100, 8191):
        assert base[3 * i] == pytest.approx(i / 8192, rel=1e-6)
        assert base[3 * i + 1] == pytest.approx(2 * ((i * 0.61803398875) % 1) - 1, rel=1e-6)
        assert base[3 * i + 2] == pytest.approx(0.03 + 5 * ((i * 0.754877666) % 1), rel=1e-6)


def test_ns26_bundle_covers_source_bytes():
    paths = {x["path"] for x in bundle_manifest(spec(), "similarity-core")["files"]}
    assert {
        "app/static/data/ns26/schedule.json",
        "app/static/data/ns26/base.f32.bin",
        "app/static/js/sources/ns26_core.js",
        "app/static/js/sources/ns26.js",
        "tools/generate_trajectories.py",
    } <= paths


def test_ns26_genomes_are_observation_only():
    import random
    old = archive.DB
    with tempfile.TemporaryDirectory() as td:
        archive.DB = pathlib.Path(td) / "x.sqlite3"
        archive.init_db()
        rng = random.Random(3301)
        g = archive.random_genome(spec(), rng, variant="pulse-view")
        for _ in range(100):
            g = archive.mutate_genome(spec(), g, rng, variant="pulse-view")
        assert set(g) == set(spec()["control_surface"])
        assert not (set(g) & set(spec()["immutable_core"]))
        roots = archive.create_population("NS26", "frontier", 4, seed=3301)
        by_variant = {}
        for r in roots:
            by_variant.setdefault(r["source_variant"], []).append(r["id"])
        for variant, ids in by_variant.items():
            kk = archive.create_population("NS26", "frontier", 4, ids[:1], seed=3303)
            assert all(k["source_variant"] == variant for k in kk)
            assert all(k["spec_hash"] == archive.core_hash(spec(), variant) for k in kk)
    archive.DB = old


def _node_ok():
    node = shutil.which("node")
    if not node:
        return False
    try:
        subprocess.run(
            [node, "-e", "require('skia-canvas')"], cwd=ROOT,
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def test_ns26_js_core_matches_python():
    if not shutil.which("node"):
        pytest.skip("node not available")
    sched = json.loads((ROOT / "app/static/data/ns26/schedule.json").read_text())
    raw = (ROOT / "app/static/data/ns26/base.f32.bin").read_bytes()
    base = struct.unpack("<" + "f" * 8192 * 3, raw)
    fi = 17
    S = {k: sched[k][fi] for k in ("tau", "rs", "zs", "vel")}
    phase = math.tau * fi / 120 + 3.0 * S["vel"] * 0.025
    extra = 1.0 * S["vel"] * 0.015 * 3.0
    expected = []
    for i in (0, 1, 100, 8191):
        u, eta, X = base[3 * i], base[3 * i + 1], base[3 * i + 2]
        r = math.sqrt(2 * S["tau"] * X) * S["rs"] * 7
        pulse = math.sin(eta * 11 + X * 8 - phase)
        a = math.tau * u * 31 + extra + 0.5 * pulse
        expected.append([r * math.cos(a), S["zs"] * eta * 8 + 0.16 * pulse, r * math.sin(a), abs(pulse)])
    probe = {"idx": [0, 1, 100, 8191], "S": S, "phase": phase, "extra": extra}
    with tempfile.TemporaryDirectory() as td:
        pf = pathlib.Path(td) / "probe.json"
        pf.write_text(json.dumps(probe))
        js = (
            "import{readFileSync}from'fs';"
            "import{scaffoldPoint}from'" + (ROOT / "app/static/js/sources/ns26_core.js").as_uri() + "';"
            "const q=JSON.parse(readFileSync('" + str(pf) + "','utf8'));"
            "const b=new Float32Array(readFileSync('" + str(ROOT / "app/static/data/ns26/base.f32.bin") + "').buffer);"
            "console.log(JSON.stringify(q.idx.map(i=>scaffoldPoint(b[3*i],b[3*i+1],b[3*i+2],q.S,q.phase,q.extra))));"
        )
        out = subprocess.run(
            [shutil.which("node"), "--input-type=module", "-e", js],
            check=True, capture_output=True, text=True,
        )
    for got, want in zip(json.loads(out.stdout), expected):
        assert got == pytest.approx(want, rel=1e-6, abs=1e-6)


def test_ns26_expected_render_hash():
    """Fixed seed -> fixed population -> fixed render bytes (t2 frame hashes)."""
    if not _node_ok():
        pytest.skip("node + skia-canvas not available")
    old = archive.DB
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        archive.DB = td / "x.sqlite3"
        archive.init_db()
        pop = archive.create_population("NS26", "frontier", 8, seed=424242)
        (td / "pop.json").write_text(json.dumps(pop))
        subprocess.run(
            [shutil.which("node"), str(ROOT / "tools/render_population.cjs"),
             str(ROOT), str(td / "pop.json"), str(td / "frames"), "96", "9"],
            check=True, cwd=ROOT, stdout=subprocess.DEVNULL,
        )
        hashes = []
        for p in pop:
            h = hashlib.sha256((td / "frames" / p["id"] / "t0.png").read_bytes()).hexdigest()
            hashes.append(h)
        assert len(set(hashes)) == len(hashes), "seeded NS26 renders must be distinct"
        assert all((td / "frames" / p["id"] / "t0.png").stat().st_size > 500 for p in pop)
    archive.DB = old
