#!/usr/bin/env python3
"""Pre-render P5.js sketches as GIFs using Playwright + ffmpeg."""
import json, os, sys, tempfile, shutil, subprocess, urllib.request
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "corpus" / "tsubuyaki" / "local_registry.jsonl"
OUT_DIR = Path(__file__).resolve().parents[1] / "static" / "gifs"
P5_CDN = "https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"
SIZE = 320
FPS = 12
SECONDS = 3
FRAMES = FPS * SECONDS


def fetch_sketch(sketch_id):
    url = f"https://tsubuyaki.art/sketches/{sketch_id}.js"
    req = urllib.request.Request(url, headers={"User-Agent": "MathArtist/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.read().decode("utf-8")


def make_html(sketch_code):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="{P5_CDN}"></script>
<style>body{{margin:0;overflow:hidden;background:#111}}</style>
</head><body><script>
{sketch_code}
</script></body></html>"""


def render_gif(sketch_id, sketch_code, out_path):
    from playwright.sync_api import sync_playwright

    html = make_html(sketch_code)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": SIZE, "height": SIZE})

        # Load sketch via srcdoc
        page.set_content(html, wait_until="networkidle")

        # Wait for P5 to initialize
        page.wait_for_timeout(2000)

        # Capture frames
        frames_dir = tempfile.mkdtemp(prefix="frames-")
        for i in range(FRAMES):
            page.screenshot(path=os.path.join(frames_dir, f"frame-{i:04d}.png"))
            page.wait_for_timeout(int(1000 / FPS))

        browser.close()

        # Create GIF with ffmpeg (2-pass for quality)
        palette = os.path.join(frames_dir, "palette.png")
        pattern = os.path.join(frames_dir, "frame-%04d.png")

        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS),
            "-i", pattern,
            "-vf", f"palettegen=max_colors=128:stats_mode=diff",
            palette
        ], check=True)

        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS),
            "-i", pattern,
            "-i", palette,
            "-lavfi", "paletteuse=dither=bayer:bayer_scale=3",
            "-loop", "0",
            "-fs", "500K",  # max 500KB per GIF
            str(out_path)
        ], check=True)

        shutil.rmtree(frames_dir, ignore_errors=True)

    return out_path.stat().st_size


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load registry
    ids = []
    with open(REGISTRY) as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                ids.append(d["id"])

    # Process first N sketches
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    ids = ids[:limit]

    print(f"Rendering {len(ids)} sketches as {SIZE}x{SIZE} GIFs ({FPS}fps, {SECONDS}s)")

    for i, sketch_id in enumerate(ids):
        out_path = OUT_DIR / f"{sketch_id}.gif"
        if out_path.exists():
            print(f"  [{i+1}/{len(ids)}] {sketch_id} — exists, skipping")
            continue

        try:
            print(f"  [{i+1}/{len(ids)}] {sketch_id} — fetching...", end=" ", flush=True)
            code = fetch_sketch(sketch_id)
            print("rendering...", end=" ", flush=True)
            size = render_gif(sketch_id, code, out_path)
            print(f"done ({size/1024:.0f}KB)")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nDone. GIFs in {OUT_DIR}")


if __name__ == "__main__":
    main()
