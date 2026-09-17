from __future__ import annotations
import json, mimetypes, sys, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from archive import init_db, load_specs, create_population, list_population, add_event, lineage, export_all, get_many, correlation_report, study_sample, conn, get_phenotype
from experiment_store import (init_experiment_db, list_experiments, get_experiment, add_response,
    experiment_report, youtube_fitness, structural_response_report, commonization_report,
    sync_youtube_fitness_events)

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/"app"/"static"

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if self.path.startswith('/api/'): return
        super().log_message(fmt,*args)
    def _json(self,obj,status=200):
        b=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
    def _body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query)
        if u.path=="/api/health": return self._json({"ok":True,"name":"mathartist-suite"})
        if u.path=="/api/sources":
            specs=load_specs();return self._json([{k:v for k,v in s.items() if k not in ("interpretation_genes",)} for s in specs.values()])
        if u.path=="/api/population":
            src=q.get("source",["LENIA"])[0];mode=q.get("mode",["open"])[0];count=min(128,max(1,int(q.get("count",[72])[0])));session=q.get("session",[None])[0]
            return self._json(list_population(src,mode,count,session))
        if u.path=="/api/study":
            src=q.get("source",["LENIA"])[0];count=min(128,max(1,int(q.get("count",[36])[0])));session=q.get("session",["anon"])[0];study=q.get("study",["attention-v1"])[0]
            return self._json(study_sample(src,session,count,study))
        if u.path=="/api/lineage": return self._json(lineage(q.get("id",[""])[0]))
        if u.path=="/api/byids":
            ids=[x for raw in q.get("ids",[]) for x in raw.split(",") if x]
            return self._json(get_many(ids))
        if u.path=="/api/export": return self._json(export_all())
        if u.path=="/api/analysis": return self._json(correlation_report(q.get("source",[None])[0]))
        if u.path=="/api/spec":
            src=q.get("source",["LENIA"])[0]; return self._json(load_specs().get(src,{}))
        if u.path=="/api/experiments": return self._json(list_experiments())
        if u.path=="/api/experiment": return self._json(get_experiment(q.get("id",["attention-rasa-v2"])[0]) or {})
        if u.path=="/api/experiment/report": return self._json(experiment_report(q.get("id",["attention-rasa-v2"])[0]))
        if u.path=="/api/experiment/structural-response": return self._json(structural_response_report(q.get("id",["attention-rasa-v2"])[0]))
        if u.path=="/api/experiment/commonization": return self._json(commonization_report(q.get("id",["commonization-v1"])[0]))
        if u.path=="/api/youtube/fitness": return self._json(youtube_fitness(q.get("video_id",[""])[0]) or {})
        return self._serve_static(u.path)
    def do_POST(self):
        u=urllib.parse.urlparse(self.path); body=self._body()
        if u.path=="/api/evolve":
            try:
                out=create_population(body["source_id"],body.get("mode","open"),min(128,int(body.get("count",72))),body.get("selected_ids") or [],body.get("session_id"),body.get("seed"))
                return self._json(out)
            except Exception as e:return self._json({"error":str(e)},400)
        if u.path=="/api/event":
            add_event(body);return self._json({"ok":True})
        if u.path=="/api/experiment/response":
            try:add_response(body);return self._json({"ok":True})
            except Exception as e:return self._json({"error":str(e)},400)
        if u.path=="/api/youtube/sync-fitness":
            try:return self._json(sync_youtube_fitness_events(body.get("video_id","")) or {})
            except Exception as e:return self._json({"error":str(e)},400)
        if u.path=="/api/expand":
            try:
                pid=body.get("phenotype_id",""); count=min(128,max(1,int(body.get("count",64))))
                with conn() as c:
                    p=get_phenotype(c,pid)
                    if not p: return self._json({"error":"phenotype not found"},404)
                out=create_population(p["source_id"],"frontier",count,selected_ids=[pid],
                                      session_id=body.get("session_id"),seed=body.get("seed"))
                return self._json(out)
            except Exception as e:return self._json({"error":str(e)},400)
        return self._json({"error":"not found"},404)
    def _serve_static(self,path):
        if path=="/": path="/index.html"
        p=(STATIC/path.lstrip('/')).resolve()
        if not str(p).startswith(str(STATIC.resolve())) or not p.is_file():
            p=STATIC/"index.html"
        b=p.read_bytes();ctype=mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        self.send_response(200);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(b)));self.send_header("Cache-Control","no-cache");self.end_headers();self.wfile.write(b)

def main():
    init_db();init_experiment_db();port=8765
    if len(sys.argv)>1:
        try:port=int(sys.argv[1])
        except:pass
    print(f"MathArtist Lab: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1",port),Handler).serve_forever()

if __name__=="__main__":main()
