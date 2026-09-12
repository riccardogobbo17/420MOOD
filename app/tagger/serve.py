#!/usr/bin/env python3
"""Avvia il tagger FMP in locale (shortcut dedicati + video locale + YouTube).

POST /api/report  JSON {csv, avversario} → PDF del report partita.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

from standalone import standalone_html

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
VENV_PYTHON = REPO / ".venv" / "bin" / "python"
REPORT_SCRIPT = ROOT.parent / "scripts" / "genera_report.py"
DEFAULT_PORT = 8765


def _python_for_report() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def build_report_pdf(csv_text: str, avversario: str) -> bytes:
    if not REPORT_SCRIPT.exists():
        raise RuntimeError(f"Script report non trovato: {REPORT_SCRIPT}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        csv_path = tmp_path / "eventi.csv"
        pdf_path = tmp_path / "report.pdf"
        csv_path.write_text(csv_text, encoding="utf-8-sig")
        env = os.environ.copy()
        env.setdefault("MPLCONFIGDIR", str(tmp_path / "mplcache"))
        result = subprocess.run(
            [
                _python_for_report(),
                str(REPORT_SCRIPT),
                str(csv_path),
                avversario or "Avversario",
                str(pdf_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            env=env,
            timeout=90,
        )
        if result.returncode != 0 or not pdf_path.exists():
            detail = (result.stderr or result.stdout or "generazione PDF fallita").strip()
            raise RuntimeError(detail[-800:] or "generazione PDF fallita")
        return pdf_path.read_bytes()


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            body = standalone_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/report":
            self.send_error(404, "Not found")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 8_000_000:
            self._send_json(400, {"error": "CSV mancante o troppo grande"})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "JSON non valido"})
            return
        csv_text = str(payload.get("csv") or "")
        avversario = str(payload.get("avversario") or "Avversario").strip() or "Avversario"
        if not csv_text.strip():
            self._send_json(400, {"error": "CSV vuoto"})
            return
        try:
            pdf = build_report_pdf(csv_text, avversario)
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(len(pdf)))
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{avversario.replace(chr(34), "")}_report.pdf"',
        )
        self.end_headers()
        self.wfile.write(pdf)
        print(f"[tagger] PDF {len(pdf)} byte per {avversario}", flush=True)

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        print(f"[tagger] {self.address_string()} {args[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Server locale del Tagger FMP")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    handler = functools.partial(Handler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        url = f"http://127.0.0.1:{args.port}/"
        print(f"Tagger FMP pronto: {url}", flush=True)
        print("Ctrl+C per chiudere.", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nChiuso.")


if __name__ == "__main__":
    main()
