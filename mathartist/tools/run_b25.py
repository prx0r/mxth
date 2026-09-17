#!/usr/bin/env python3
"""Run 1,000 descendants per B25 seed: mutate literals, execute, record results.

For each seed:
1. Load code + classified literals
2. For each mutation candidate, define a range (min/max from code context)
3. Generate 1,000 parameter variations (600 Sobol global + 300 local + 100 boundary)
4. For each variation: substitute literals, execute via reproduce_seed.cjs, record hash
5. Write results to descendants/<seed_id>.jsonl

Usage:
  python tools/run_b25.py [--seed-set B25_REFERENCE] [--descendants 1000] [--out seeds/descendants]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from classify_literals import extract_literals

MUTABLE_ROLES = {"MATHEMATICAL_COEFFICIENT", "FREQUENCY", "PHASE", "EXPONENT", "INITIAL_CONDITION", "SAMPLING_BUDGET", "BRANCH_SELECTOR"}


def infer_range(value: float, role: str) -> tuple[float, float]:
    """Infer a plausible mutation range for a literal."""
    if role == "FREQUENCY":
        return (max(0.1, value * 0.3), value * 3.0)
    if role == "PHASE":
        return (0, max(6.28, value * 2))
    if role == "EXPONENT":
        return (max(0.1, value * 0.5), value * 2.0)
    if role == "INITIAL_CONDITION":
        if abs(value) < 0.01:
            return (-1.0, 1.0)
        return (value * 0.2, value * 5.0)
    # MATHEMATICAL_COEFFICIENT
    if abs(value) < 0.01:
        return (-10.0, 10.0)
    return (value * 0.1, value * 10.0)


def sobol_sample(n: int, dims: int, seed: int = 0) -> list[list[float]]:
    """Simple Sobol sequence via XOR mapping. Not a true Sobol but adequate for coverage."""
    rng = random.Random(seed)
    result = []
    for i in range(n):
        row = []
        for d in range(dims):
            # Van der Corput-like mapping
            m = 1.0
            x = 0.0
            v = i + 1
            base = 2 + d * 3
            while v > 0:
                m /= base
                x += (v % base) * m
                v //= base
            row.append(x + rng.random() * 0.01)  # tiny jitter to break regularity
        result.append(row)
    return result


def generate_variations(candidates: list[dict], count: int, seed: int) -> list[dict]:
    """Generate parameter variations for mutation candidates."""
    rng = random.Random(seed)
    n_cands = len(candidates)
    if n_cands == 0:
        return [{}] * count

    # Build ranges
    ranges = []
    for c in candidates:
        v = float(c["literal"])
        lo, hi = infer_range(v, c["role"])
        ranges.append((lo, hi))

    variations = []

    # 60% Sobol/global
    n_global = int(count * 0.6)
    sobol = sobol_sample(n_global, n_cands, seed)
    for row in sobol:
        g = {}
        for i, c in enumerate(candidates):
            lo, hi = ranges[i]
            g[c["offset"]] = lo + row[i % len(row)] * (hi - lo)
        variations.append(g)

    # 30% local perturbations around default
    n_local = int(count * 0.3)
    for _ in range(n_local):
        g = {}
        for i, c in enumerate(candidates):
            v = float(c["literal"])
            lo, hi = ranges[i]
            sigma = (hi - lo) * 0.15
            g[c["offset"]] = max(lo, min(hi, v + rng.gauss(0, sigma)))
        variations.append(g)

    # 10% boundary stress
    n_boundary = count - len(variations)
    for _ in range(n_boundary):
        g = {}
        for i, c in enumerate(candidates):
            lo, hi = ranges[i]
            g[c["offset"]] = rng.choice([lo, hi, (lo + hi) / 2])
        variations.append(g)

    return variations[:count]


def apply_variation(code: str, candidates: list[dict], variation: dict) -> str:
    """Substitute numeric literals into code at their offsets."""
    # Sort by offset descending so substitutions don't shift later offsets
    subs = sorted(
        [(off, val) for off, val in variation.items()],
        key=lambda x: x[0], reverse=True
    )
    result = code
    for offset, new_val in subs:
        # Find the literal at this offset
        for c in candidates:
            if c["offset"] == offset:
                old = c["literal"]
                # Format: use int if it was int-like, else float
                if "." not in old and "e" not in old:
                    new_str = str(int(round(new_val)))
                else:
                    new_str = f"{new_val:.6g}"
                result = result[:offset] + new_str + result[offset + len(old):]
                break
    return result


def run_one(code: str, code_file: Path, seed_id: str, var_idx: int, timeout_s: int = 10) -> dict:
    """Execute one variation and return the result."""
    tmp = Path(tempfile.mktemp(suffix=".js"))
    tmp.write_text(code)
    try:
        r = subprocess.run(
            ["node", str(ROOT / "tools" / "reproduce_seed.cjs"), str(tmp),
             "--frame", "20", "--timeout", str(timeout_s * 1000)],
            capture_output=True, text=True, timeout=timeout_s + 5
        )
        out = json.loads(r.stdout)
        return {
            "ok": out.get("ok", False),
            "render_hash": out.get("render_hash"),
            "frame": out.get("frame_captured", 0),
            "error": out.get("error"),
            "execution_ms": out.get("execution_time_ms", 0),
        }
    except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e)}
    finally:
        tmp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-set", default="B25_REFERENCE")
    ap.add_argument("--descendants", type=int, default=1000)
    ap.add_argument("--out", default=str(ROOT / "seeds" / "descendants"))
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    manifest = json.load(open(ROOT / "seeds" / f"{a.seed_set}.json"))
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_ok = 0
    total_fail = 0
    t0 = time.time()

    for seed in manifest["seeds"]:
        seed_id = seed["seed_id"]
        code_file = Path(seed.get("code_file", ""))
        if not code_file.exists():
            print(f"SKIP {seed_id}: code_file not found")
            continue

        code = code_file.read_text(errors="replace")
        literals = extract_literals(code)
        candidates = [lit for lit in literals if lit["role"] in MUTABLE_ROLES]

        if not candidates:
            print(f"SKIP {seed_id}: no mutation candidates")
            continue

        print(f"RUN {seed_id}: {len(candidates)} candidates × {a.descendants} descendants")
        variations = generate_variations(candidates, a.descendants, hash(seed_id))

        results = []
        for i, var in enumerate(variations):
            if a.dry_run:
                results.append({"ok": True, "render_hash": "dry", "var_idx": i})
                continue
            varied_code = apply_variation(code, candidates, var)
            r = run_one(varied_code, code_file, seed_id, i, a.timeout)
            r["var_idx"] = i
            r["theta"] = {str(k): v for k, v in var.items()}
            results.append(r)
            if r["ok"]:
                total_ok += 1
            else:
                total_fail += 1

            if (i + 1) % 100 == 0:
                elapsed = time.time() - t0
                rate = (total_ok + total_fail) / max(1, elapsed)
                print(f"  [{i+1}/{a.descendants}] ok={total_ok} fail={total_fail} rate={rate:.1f}/s")

        # Write results for this seed
        out_file = out_dir / f"{seed_id}.jsonl"
        with out_file.open("w") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        seed_ok = sum(1 for r in results if r.get("ok"))
        print(f"  DONE {seed_id}: {seed_ok}/{len(results)} ok")

    elapsed = time.time() - t0
    print(f"\nTOTAL: {total_ok} ok, {total_fail} fail in {elapsed:.1f}s ({(total_ok+total_fail)/max(1,elapsed):.1f}/s)")


if __name__ == "__main__":
    main()
