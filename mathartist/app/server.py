from __future__ import annotations
import json, mimetypes, sys, urllib.parse, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
REGISTRY = ROOT / "corpus" / "tsubuyaki" / "local_registry.jsonl"

def load_sketch_ids():
    ids = []
    if REGISTRY.exists():
        for line in REGISTRY.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                ids.append(d["id"])
    return ids

SKETCH_IDS = load_sketch_ids()

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if self.path.startswith("/api/"):
            return
        super().log_message(fmt, *args)

    def _json(self, obj, status=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _text(self, text, status=200, content_type="text/plain"):
        b = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public,max-age=3600")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)

        # List available sketches
        if u.path == "/api/sketches":
            return self._json({"ids": SKETCH_IDS[:50], "total": len(SKETCH_IDS)})

        # Proxy thumbnail from Twitter CDN
        if u.path.startswith("/api/thumb/"):
            sketch_id = u.path.split("/api/thumb/", 1)[1].split("?")[0]
            # Look up preview URL from registry
            thumb_url = None
            for line in REGISTRY.read_text().splitlines():
                if line.strip():
                    d = json.loads(line)
                    if d["id"] == sketch_id:
                        thumb_url = d.get("preview", {}).get("still")
                        break
            if not thumb_url:
                # 1x1 transparent GIF
                import base64
                gif = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")
                self.send_response(200)
                self.send_header("Content-Type", "image/gif")
                self.send_header("Content-Length", str(len(gif)))
                self.end_headers()
                self.wfile.write(gif)
                return
            try:
                req = urllib.request.Request(thumb_url, headers={"User-Agent": "MathArtist/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public,max-age=86400")
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                import base64
                gif = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")
                self.send_response(200)
                self.send_header("Content-Type", "image/gif")
                self.send_header("Content-Length", str(len(gif)))
                self.end_headers()
                self.wfile.write(gif)
            return

        # Proxy sketch code from tsubuyaki.art
        if u.path.startswith("/api/sketch/"):
            sketch_id = u.path.split("/api/sketch/", 1)[1].split("?")[0]
            url = f"https://tsubuyaki.art/sketches/{sketch_id}.js"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "MathArtist/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                code = resp.read().decode("utf-8")
                return self._text(code, content_type="application/javascript")
            except Exception as e:
                return self._json({"error": str(e)}, 502)

        # Proxy sketch code as srcdoc-safe HTML
        if u.path.startswith("/api/srcdoc/"):
            sketch_id = u.path.split("/api/srcdoc/", 1)[1].split("?")[0]
            url = f"https://tsubuyaki.art/sketches/{sketch_id}.js"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "MathArtist/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                code = resp.read().decode("utf-8")
                html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
<style>body{{margin:0;overflow:hidden;background:#111}}</style>
</head><body><script>
{code}
</script></body></html>"""
                return self._text(html, content_type="text/html")
            except Exception as e:
                return self._json({"error": str(e)}, 502)

        # Proxy preview image
        if u.path.startswith("/api/preview/"):
            sketch_id = u.path.split("/api/preview/", 1)[1].split("?")[0]
            url = f"https://tsubuyaki.art/preview/{sketch_id}.jpg"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "MathArtist/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public,max-age=86400")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                # Return 1x1 transparent GIF on failure
                import base64
                gif = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")
                self.send_response(200)
                self.send_header("Content-Type", "image/gif")
                self.send_header("Content-Length", str(len(gif)))
                self.end_headers()
                self.wfile.write(gif)
            return

        # Serve static files
        return self._serve_static(u.path)

    def _serve_static(self, path):
        if path == "/":
            path = "/index.html"
        p = (STATIC / path.lstrip("/")).resolve()
        if not str(p).startswith(str(STATIC.resolve())) or not p.is_file():
            p = STATIC / "index.html"
        b = p.read_bytes()
        ctype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(b)


def main():
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    print(f"MathArtist: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
