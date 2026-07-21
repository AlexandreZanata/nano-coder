#!/usr/bin/env python3
"""Nano-Orchestrator Arena — local playground to inspect proposals + schedule runs.

  python arena/server.py
  python -m nano_orchestrator arena --port 8765
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
OUT = ROOT / "out"
PROPOSAL = OUT / "proposal"
RUNS = ROOT / "benchmarks" / "runs"

SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _json_response(handler: BaseHTTPRequestHandler, payload: object, status: int = 200) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(path: Path) -> object | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid_json", "path": str(path)}


def api_overview() -> dict:
    package = _read_json(PROPOSAL / "package.json")
    files: list[dict] = []
    if PROPOSAL.is_dir():
        for path in sorted(PROPOSAL.iterdir()):
            if not path.is_file() or path.name == "package.json":
                continue
            files.append(
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "mtime": path.stat().st_mtime,
                    "ext": path.suffix.lstrip(".").lower(),
                }
            )
    runs = []
    if RUNS.is_dir():
        for path in sorted(RUNS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            runs.append(
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "mtime": path.stat().st_mtime,
                }
            )
    return {
        "ok": True,
        "roots": {
            "proposal": str(PROPOSAL),
            "runs": str(RUNS),
        },
        "package": package,
        "files": files,
        "runs": runs[:40],
        "human_gate": True,
        "auto_persist": False,
    }


def api_file(name: str) -> tuple[dict, int]:
    if not SAFE_NAME.match(name):
        return {"ok": False, "error": "invalid_name"}, 400
    path = PROPOSAL / name
    if not path.is_file() or not path.resolve().is_relative_to(PROPOSAL.resolve()):
        return {"ok": False, "error": "not_found"}, 404
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "ok": True,
        "name": name,
        "bytes": len(text.encode("utf-8")),
        "ext": path.suffix.lstrip(".").lower(),
        "content": text,
    }, 200


def site_file_path(name: str) -> Path | None:
    """Resolve a safe proposal asset for /site/<name> browsing."""
    if not SAFE_NAME.match(name):
        return None
    path = PROPOSAL / name
    if not path.is_file() or not path.resolve().is_relative_to(PROPOSAL.resolve()):
        return None
    return path


def api_run(name: str) -> tuple[dict, int]:
    if not SAFE_NAME.match(name):
        return {"ok": False, "error": "invalid_name"}, 400
    path = RUNS / name
    if not path.is_file() or not path.resolve().is_relative_to(RUNS.resolve()):
        return {"ok": False, "error": "not_found"}, 404
    data = _read_json(path)
    return {"ok": True, "name": name, "data": data}, 200


class ArenaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[arena] {self.address_string()} {fmt % args}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/overview":
            _json_response(self, api_overview())
            return
        if path == "/api/file":
            qs = parse_qs(parsed.query)
            name = unquote((qs.get("name") or [""])[0])
            payload, status = api_file(name)
            _json_response(self, payload, status)
            return
        if path == "/api/run":
            qs = parse_qs(parsed.query)
            name = unquote((qs.get("name") or [""])[0])
            payload, status = api_run(name)
            _json_response(self, payload, status)
            return
        if path == "/site" or path.startswith("/site/"):
            self._serve_site(path)
            return
        self._serve_static(path)

    def _serve_site(self, path: str) -> None:
        rel = path[len("/site") :].lstrip("/")
        if not rel:
            rel = "index.html"
        if ".." in rel or "/" in rel or "\\" in rel:
            self.send_error(400)
            return
        file_path = site_file_path(rel)
        if file_path is None:
            self.send_error(404)
            return
        data = file_path.read_bytes()
        ctype, _ = mimetypes.guess_type(str(file_path))
        if file_path.suffix.lower() == ".css":
            ctype = "text/css; charset=utf-8"
        elif file_path.suffix.lower() in (".html", ".htm"):
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        if ".." in rel or rel.startswith("/"):
            self.send_error(400)
            return
        file_path = (STATIC / rel).resolve()
        if not file_path.is_file() or not file_path.is_relative_to(STATIC.resolve()):
            self.send_error(404)
            return
        data = file_path.read_bytes()
        ctype, _ = mimetypes.guess_type(str(file_path))
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nano-Orchestrator Arena playground")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not STATIC.is_dir():
        print(f"FAIL: missing static dir {STATIC}")
        return 1
    server = ThreadingHTTPServer((args.host, args.port), ArenaHandler)
    print(f"Arena → http://{args.host}:{args.port}", flush=True)
    print(f"Proposal root: {PROPOSAL}", flush=True)
    print(f"Runs root:     {RUNS}", flush=True)
    print("HUMAN GATE: review only — never auto-persist.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArena stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
