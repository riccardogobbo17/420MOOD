"""Lettura/scrittura della cartella app/tagger/config/."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent / "config"
COLORS = {"orange", "green", "red", "teal", "yellow", "purple", "blue", "gray"}
FILES = ("rosa.json", "eventi.json", "attributi.json", "opzioni.json")


def _read(name: str) -> dict:
    path = CONFIG_DIR / name
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} non valido: {exc}") from exc
    return data if isinstance(data, dict) else {}


def _write(name: str, payload: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "rosa": _read("rosa.json"),
        "eventi": _read("eventi.json"),
        "attributi": _read("attributi.json"),
        "opzioni": _read("opzioni.json"),
        "path": str(CONFIG_DIR),
    }


def _clean_list(values) -> list[str]:
    if not isinstance(values, list):
        return []
    out = []
    seen = set()
    for raw in values:
        item = str(raw or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _clean_event(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    ident = str(raw.get("id") or "").strip()
    if not ident:
        return None
    color = str(raw.get("color") or "gray").strip().lower()
    if color not in COLORS:
        color = "gray"
    shortcut = str(raw.get("shortcut") or "").strip().lower()[:1]
    group = str(raw.get("group") or "Altro").strip() or "Altro"
    try:
        preroll = max(0.0, float(raw.get("preroll") or 0))
    except (TypeError, ValueError):
        preroll = 0.0
    try:
        duration = float(raw.get("duration") or 5)
    except (TypeError, ValueError):
        duration = 5.0
    if duration <= 0:
        duration = 5.0
    return {
        "id": ident,
        "shortcut": shortcut,
        "color": color,
        "group": group,
        "preroll": preroll,
        "duration": duration,
    }


def save_config(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("JSON non valido")

    rosa_in = payload.get("rosa") if isinstance(payload.get("rosa"), dict) else {}
    giocatori = _clean_list(rosa_in.get("giocatori"))
    portieri = _clean_list(rosa_in.get("portieri"))
    sticky = str(rosa_in.get("portiere_sticky") or "").strip()
    if sticky and sticky not in portieri:
        sticky = portieri[0] if portieri else ""
    rosa = {
        "giocatori": giocatori,
        "portieri": portieri,
        "portiere_sticky": sticky,
    }

    eventi_in = payload.get("eventi") if isinstance(payload.get("eventi"), dict) else payload
    raw_list = eventi_in.get("eventi") if isinstance(eventi_in, dict) else None
    if not isinstance(raw_list, list):
        raw_list = payload.get("eventi") if isinstance(payload.get("eventi"), list) else []
    eventi = []
    seen = set()
    for item in raw_list:
        cleaned = _clean_event(item)
        if not cleaned or cleaned["id"] in seen:
            continue
        seen.add(cleaned["id"])
        eventi.append(cleaned)
    if not eventi:
        raise ValueError("Serve almeno un evento")

    attr_in = payload.get("attributi") if isinstance(payload.get("attributi"), dict) else {}
    esiti_in = attr_in.get("esiti") if isinstance(attr_in.get("esiti"), dict) else {}
    esiti = {
        str(key).strip(): _clean_list(vals)
        for key, vals in esiti_in.items()
        if str(key).strip()
    }
    zone = []
    for item in attr_in.get("zone") or []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()[:1]
        label = str(item.get("label") or "").strip()
        if key and label:
            zone.append({"key": key, "label": label})
    if not zone:
        zone = [
            {"key": "1", "label": "Zona 1"},
            {"key": "2", "label": "Zona 2"},
            {"key": "3", "label": "Zona 3"},
        ]

    opt_in = payload.get("opzioni") if isinstance(payload.get("opzioni"), dict) else {}
    try:
        durata = float(opt_in.get("durata_fallback") or 5)
    except (TypeError, ValueError):
        durata = 5.0
    try:
        ritardo = float(opt_in.get("ritardo_tagging") or 0)
    except (TypeError, ValueError):
        ritardo = 0.0
    opzioni = {
        "durata_fallback": durata if durata > 0 else 5.0,
        "ritardo_tagging": ritardo,
    }

    _write("rosa.json", rosa)
    _write("eventi.json", {"eventi": eventi})
    _write("attributi.json", {"esiti": esiti, "zone": zone})
    _write("opzioni.json", opzioni)
    return load_config()
