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
        if path == "/player.html":
            body = (ROOT / "player.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/config":
            self._handle_get_config()
            return
        if path == "/api/session":
            self._handle_get_session()
            return
        if path == "/api/partite":
            self._handle_list_partite()
            return
        if path == "/api/eventi-count":
            self._handle_eventi_count()
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        payload = self._read_json()
        if payload is None and path != "/api/report":
            return
        if path == "/api/report":
            if payload is None:
                return
            self._handle_report(payload)
            return
        if path == "/api/partite":
            self._handle_create_partita(payload or {})
            return
        if path == "/api/push":
            self._handle_push(payload or {})
            return
        if path == "/api/config":
            self._handle_save_config(payload or {})
            return
        if path == "/api/session":
            self._handle_save_session(payload or {})
            return
        if path == "/api/session/csv":
            self._handle_save_csv(payload or {})
            return
        self.send_error(404, "Not found")

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 8_000_000:
            self._send_json(400, {"error": "Body mancante o troppo grande"})
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "JSON non valido"})
            return None

    def _handle_report(self, payload: dict) -> None:
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

    def _handle_list_partite(self) -> None:
        try:
            from push_db import TABELLA_EVENTI, TABELLA_PARTITE, list_partite
            data = list_partite()
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, {
            "partite": data,
            "tables": {"partite": TABELLA_PARTITE, "eventi": TABELLA_EVENTI},
        })

    def _handle_eventi_count(self) -> None:
        from urllib.parse import parse_qs, urlparse
        qs = parse_qs(urlparse(self.path).query)
        partita_id = (qs.get("partita_id") or [""])[0]
        if not partita_id:
            self._send_json(400, {"error": "partita_id mancante"})
            return
        try:
            from push_db import count_eventi
            n = count_eventi(partita_id)
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, {"partita_id": partita_id, "count": n})

    def _handle_create_partita(self, payload: dict) -> None:
        try:
            from push_db import create_partita
            row = create_partita(payload)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, {"partita": row})

    def _handle_push(self, payload: dict) -> None:
        try:
            from push_db import create_partita, push_eventi
            partita_id = str(payload.get("partita_id") or "").strip()
            create = payload.get("create")
            if create and not partita_id:
                row = create_partita(create)
                partita_id = row["id"]
            events = payload.get("events") or []
            if not isinstance(events, list):
                raise ValueError("events deve essere una lista")
            result = push_eventi(
                partita_id,
                events,
                replace=bool(payload.get("replace", True)),
                fallback_date=str(payload.get("data") or ""),
            )
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, result)

    def _handle_get_config(self) -> None:
        try:
            from config_store import load_config
            data = load_config()
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, data)

    def _handle_save_config(self, payload: dict) -> None:
        try:
            from config_store import save_config
            data = save_config(payload)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, data)

    def _handle_get_session(self) -> None:
        try:
            from session_store import load_ultima
            data = load_ultima()
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, data or {})

    def _handle_save_session(self, payload: dict) -> None:
        try:
            from session_store import save_session
            result = save_session(payload)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, result)

    def _handle_save_csv(self, payload: dict) -> None:
        try:
            from session_store import save_csv
            result = save_csv(
                str(payload.get("filename") or ""),
                str(payload.get("csv") or ""),
                avversario=str(payload.get("avversario") or ""),
                data=str(payload.get("data") or ""),
            )
        except ValueError as csv_exc:
            self._send_json(400, {"error": str(csv_exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, result)

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        print(f"[tagger] {self.address_string()} {args[0]}")


def open_app_window(url: str) -> None:
    """Apre Chrome/Edge in modalità app, senza barra dell'indirizzo."""
    if sys.platform == "darwin":
        for name in ("Google Chrome", "Microsoft Edge", "Brave Browser", "Chromium"):
            if Path(f"/Applications/{name}.app").exists():
                subprocess.Popen(
                    ["open", "-na", name, "--args", f"--app={url}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"Aperto in {name} senza barra indirizzi.", flush=True)
                return
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        pf = os.environ.get("PROGRAMFILES", r"C:\\Program Files")
        pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\\Program Files (x86)")
        candidates = [
            Path(pf) / "Google/Chrome/Application/chrome.exe",
            Path(pf86) / "Google/Chrome/Application/chrome.exe",
            Path(local) / "Google/Chrome/Application/chrome.exe",
            Path(pf) / "Microsoft/Edge/Application/msedge.exe",
        ]
        for exe in candidates:
            if exe.exists():
                subprocess.Popen([str(exe), f"--app={url}"])
                print(f"Aperto in {exe.name} senza barra indirizzi.", flush=True)
                return
    webbrowser.open(url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Server locale del Tagger FMP")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Apri il browser normale invece della finestra app (senza barra indirizzi)",
    )
    args = parser.parse_args()

    handler = functools.partial(Handler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        url = f"http://127.0.0.1:{args.port}/"
        print(f"Tagger FMP pronto: {url}", flush=True)
        print(f"Config:  {ROOT / 'config'}", flush=True)
        print(f"Sessioni:{ROOT / 'sessioni'}", flush=True)
        print("Ctrl+C per chiudere (salva l'ultima sessione su disco).", flush=True)
        if not args.no_browser:
            if args.browser:
                webbrowser.open(url)
            else:
                open_app_window(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            try:
                from session_store import SESSION_DIR, flush_last
                info = flush_last()
                if info:
                    print(f"\nSessione salvata: {info['path']}", flush=True)
                else:
                    print(f"\nNessuna sessione da salvare ({SESSION_DIR}).", flush=True)
            except Exception as exc:
                print(f"\nChiusura: {exc}", flush=True)
            print("Chiuso.")


if __name__ == "__main__":
    main()
