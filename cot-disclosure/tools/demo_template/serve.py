"""Serve the local demo folder on this machine only (Nov 23; development and the presentation, not a deployment).

  python3 tools/demo_template/serve.py [--port 8765] [--no-open]

Serves cot-disclosure/results/demo/ (demo.html and pad/..., gitignored: the page's recorded runs) at
http://127.0.0.1:<port>/demo.html#pad and opens it in the browser. GET and HEAD only, no directory listings, nothing
outside that folder, quiet. If the port is busy it tries the next ones. Ctrl-C stops it.
Why localhost only: the folder holds model text (recorded runs) that must never leave this Mac, so the server binds
127.0.0.1, never 0.0.0.0. Standard library only. POST /live (the pad's live mode, live.py) runs one question on the
base model through Ollama on this Mac; it needs the repo's .venv python (the analysis's modules).
"""
import argparse
import http.server
import json
import mimetypes
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "demo"
sys.path.insert(0, str(Path(__file__).resolve().parent))
TYPES = {".html": "text/html; charset=utf-8", ".json": "application/json", ".png": "image/png", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):
        pass

    def guess_type(self, path):
        ext = Path(path).suffix.lower()
        return TYPES.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"

    def _ok(self):
        """The request's path must be a file inside ROOT (no listings, no escapes)."""
        try:
            p = Path(self.translate_path(self.path.split("?", 1)[0].split("#", 1)[0])).resolve()
            return p.is_file() and p.is_relative_to(ROOT.resolve())
        except (OSError, ValueError):
            return False

    def do_GET(self):
        if self._ok():
            super().do_GET()
        else:
            self.send_error(404)

    def do_HEAD(self):
        if self._ok():
            super().do_HEAD()
        else:
            self.send_error(404)

    def do_POST(self):
        """POST /live only: the pad's "your own question", one run on the base model through Ollama (live.py). Same
        origin only; nothing is saved."""
        if self.path != "/live" or self.headers.get("Origin") not in (None, f"http://127.0.0.1:{self.server.server_port}"):
            return self.send_error(405)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 < n <= 20000:
                return self.send_error(413)
            q = json.loads(self.rfile.read(n))
            import live
            out = live.run(str(q["question"])[:4000], [str(o)[:500] for o in q["options"]][:10], q.get("hint", "user"),
                           q.get("letter"), bool(q.get("thinking", True)))
            body, code = json.dumps(out, ensure_ascii=False).encode(), 200
        except Exception as e:                       # a bad request or Ollama down: say so, never a stack trace
            body, code = json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}"}).encode(), 200
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _no(self):
        self.send_error(405)
    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _no


def make_server(port, tries=20):
    for p in range(port, port + tries):
        try:
            return http.server.ThreadingHTTPServer(("127.0.0.1", p), Handler), p
        except OSError:
            continue
    raise SystemExit(f"no free port from {port} to {port + tries - 1}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args(argv)
    if not (ROOT / "demo.html").exists():
        print(f"{ROOT / 'demo.html'} is missing: run tools/demo_template/build.py first", file=sys.stderr)
        return 1
    srv, port = make_server(a.port)
    url = f"http://127.0.0.1:{port}/demo.html#pad"
    print(url)
    if not a.no_open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
