#!/usr/bin/env python3
"""Offline read-only frontend review. No .env, model imports or inference routes.
Run: python3 -B scripts/serve_frontend.py --port 8011
"""
import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_customs import review_data as data

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send(self, payload, mime='application/json', status=200):
        if not isinstance(payload, bytes): payload = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)
    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path in ['/health', '/api/health']: return self.send({'status': 'ok', 'offline_review': True, 'running': False})
            if path == '/api/artifacts': return self.send({'artifacts': []})
            if path == '/api/recordings': return self.send({'recordings': []})
            if path == '/api/review/catalog': return self.send(data.catalog())
            if path == '/api/review/comparison': return self.send(data.comparison())
            parts = path.strip('/').split('/')
            if len(parts) >= 4 and parts[:2] == ['api', 'review']:
                run_id, kind = parts[2:4]
                if kind == 'bundle' and len(parts) == 4: return self.send(data.bundle(run_id))
                if kind == 'files' and len(parts) == 5: return self.send(data.source_path(run_id, parts[4]).read_bytes(), 'text/plain; charset=utf-8')
                if kind == 'events' and len(parts) == 4:
                    trace = data.events(run_id)
                    self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Cache-Control', 'no-cache'); self.end_headers()
                    for event in trace:
                        self.wfile.write(('data: ' + json.dumps(event) + '\n\n').encode()); self.wfile.flush(); time.sleep(.12)
                    return
            static = data.ROOT / 'model_customs/static'
            name = 'index.html' if path == '/' else path.removeprefix('/static/') if path.startswith('/static/') else ''
            file = static / name
            if not name or not file.resolve().is_relative_to(static.resolve()) or not file.is_file(): raise ValueError()
            mime = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.txt':'text/plain'}.get(file.suffix, 'application/octet-stream')
            return self.send(file.read_bytes(), mime)
        except (ValueError, OSError, KeyError):
            try: self.send({'detail': 'Evidence or page unavailable'}, status=404)
            except OSError: pass
    def do_POST(self): self.send({'detail': 'Offline review server: model calls disabled'}, status=405)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--port', type=int, default=8011); args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Read-only frontend: http://127.0.0.1:{args.port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
