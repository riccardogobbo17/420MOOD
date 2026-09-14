"""Sessione partita su disco: JSON + CSV in app/tagger/sessioni/."""

from __future__ import annotations

import json
import re
from pathlib import Path

SESSION_DIR = Path(__file__).resolve().parent / "sessioni"
_LAST: dict | None = None


def _slug(avversario: str) -> str:
    raw = re.sub(r"\s+", "-", (avversario or "partita").strip().lower())
    raw = re.sub(r"[^a-z0-9._-]+", "", raw)
    return raw or "partita"


def stem(avversario: str, data: str) -> str:
    date = re.sub(r"[^0-9.-]+", "", (data or "").strip()) or "nodata"
    return f"{_slug(avversario)}_{date}"


def _safe_name(name: str) -> str:
    base = Path(str(name or "")).name
    base = re.sub(r"[^a-zA-Z0-9._-]+", "_", base)
    return base or "export.csv"


def save_session(payload: dict) -> dict:
    global _LAST
    if not isinstance(payload, dict):
        raise ValueError("Sessione non valida")
    _LAST = payload
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    name = stem(str(payload.get("matchName") or ""), str(payload.get("matchDate") or ""))
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    named = SESSION_DIR / f"{name}.json"
    ultima = SESSION_DIR / "ultima.json"
    named.write_text(body, encoding="utf-8")
    ultima.write_text(body, encoding="utf-8")
    return {
        "file": named.name,
        "path": str(named),
        "ultima": str(ultima),
        "dir": str(SESSION_DIR),
    }


def flush_last() -> dict | None:
    if not _LAST:
        return None
    return save_session(_LAST)


def load_ultima() -> dict | None:
    path = SESSION_DIR / "ultima.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_csv(filename: str, csv_text: str, avversario: str = "", data: str = "") -> dict:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    name = _safe_name(filename)
    if not name.lower().endswith(".csv"):
        name += ".csv"
    if name in ("export.csv", "eventi.csv") or not filename:
        name = f"{stem(avversario, data)}_eventi.csv"
    path = SESSION_DIR / name
    text = csv_text if csv_text.startswith("\ufeff") else "\ufeff" + csv_text
    path.write_text(text, encoding="utf-8")
    stem_name = stem(avversario, data)
    if name.startswith(stem_name) and name.endswith(".csv") and "_primo-tempo" not in name and "_selezione" not in name:
        (SESSION_DIR / "ultima.csv").write_text(text, encoding="utf-8")
    return {"file": path.name, "path": str(path), "dir": str(SESSION_DIR)}
