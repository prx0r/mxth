#!/usr/bin/env python3
"""Fetch an attribution-forward #つぶやきProcessing JSON feed into a local seed registry.

Network access is intentionally runtime-only; third-party code is not vendored into MathArtist releases.
Fetched code (license unknown) lives under corpus/tsubuyaki/code/ which tools/package.py excludes
from release zips. The registry itself carries attribution + hashes only, never code bytes.

Feeds:
  --url https://tsubuyaki.art/data/latest.json     (small "latest" window, metadata only)
  --url https://tsubuyaki.art/data/sketches.json   (full archive; items carry code_file pointers)

Code fetch:
  --fetch-code pulls each item's code_file (site-relative, e.g. sketches/<id>.js) into
  --code-dir (default corpus/tsubuyaki/code/) and records code_sha256 + local path.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, pathlib, urllib.request

SITE = "https://tsubuyaki.art/"

def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def _author(item):
    a = item.get("author") or item.get("artist") or item.get("username") or "unknown"
    if isinstance(a, dict):
        return {"name": a.get("name"), "username": a.get("username"), "url": a.get("url")}
    return {"name": a, "username": item.get("username"), "url": None}

def normalize(item):
    tsub = item.get("tsubuyaki") or {}
    code = item.get("code") or item.get("source_code") or ""
    if not code and isinstance(item.get("source"), str) and "\n" in item["source"]:
        code = item["source"]
    return {
        "id": item.get("id"),
        "artist": _author(item),
        "original_url": item.get("tweet_url") or item.get("original_url") or item.get("url"),
        "archive_url": item.get("archive_url") or (f"{SITE}sketch.html?id={item.get('id')}" if item.get("id") else None),
        "code_url": (SITE + item["code_file"]) if item.get("code_file") else None,
        "language": item.get("language") or "p5js",
        "runtime": item.get("runtime"),
        "tsubuyaki": tsub if isinstance(tsub, dict) else {},
        "preview": {
            "still": item.get("preview_still_file"),
            "motion": item.get("preview_motion_file"),
        },
        "code": code,
        "code_sha256": sha(code) if code else None,
        "code_local": None,
        "redistribution_status": item.get("license") or "unknown — do not republish; local research cache only",
        "source": item.get("source"),
        "status": item.get("status"),
        "summary": item.get("summary"),
        "tags": item.get("tags") or [],
    }

def _get(url: str, timeout=30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "MathArtist-corpus/3.3"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_code(rec: dict, code_dir: pathlib.Path):
    url = rec.get("code_url")
    if not url:
        return rec
    try:
        raw = _get(url)
        try:
            code = raw.decode("utf-8")
        except UnicodeDecodeError:
            code = raw.decode("utf-8", "replace")
    except Exception as e:
        rec["code_fetch_error"] = str(e)
        return rec
    dest = code_dir / f"{rec.get('id') or sha(url)[:16]}.js"
    dest.write_text(code)
    rec["code"] = ""  # never persist code bytes in the registry; local file + hash only
    rec["code_sha256"] = hashlib.sha256(raw).hexdigest()
    rec["code_chars"] = len(code)
    rec["code_local"] = str(dest.relative_to(dest.parents[2])) if len(dest.parts) > 2 else dest.name
    return rec

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="https://tsubuyaki.art/data/latest.json")
    p.add_argument("--input")
    p.add_argument("--out", default="corpus/tsubuyaki/local_registry.jsonl")
    p.add_argument("--fetch-code", action="store_true")
    p.add_argument("--code-dir", default="corpus/tsubuyaki/code")
    p.add_argument("--jobs", type=int, default=8)
    a = p.parse_args()
    if a.input:
        data = json.loads(pathlib.Path(a.input).read_text())
    else:
        data = json.loads(_get(a.url, timeout=120))
    items = data if isinstance(data, list) else data.get("items") or data.get("sketches") or data.get("entries") or []
    recs = [normalize(x) for x in items]
    if a.fetch_code:
        code_dir = pathlib.Path(a.code_dir)
        code_dir.mkdir(parents=True, exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            recs = list(ex.map(lambda r: fetch_code(r, code_dir), recs))
        ok = sum(1 for r in recs if r.get("code_sha256"))
        print(json.dumps({"code_fetched": ok, "of": len(recs)}))
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"records": len(recs), "out": str(out)}))

if __name__ == "__main__":
    main()
