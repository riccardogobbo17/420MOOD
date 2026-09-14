"""Operazioni Supabase per il tagger: stesse tabelle e mapping dell'Admin 2026/27."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

APP = Path(__file__).resolve().parents[1]
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from futsal_analysis.config_supabase import (  # noqa: E402
    TABELLA_EVENTI,
    TABELLA_PARTITE,
    get_supabase_client,
)

CATEGORIA = "Prima Squadra"
COLONNE_EVENTO = [
    "posizione", "data", "evento", "chi", "esito", "dove", "lato", "piede",
    "portiere", "quartetto", "quartetto_1", "quartetto_2", "quartetto_3",
    "quartetto_4", "squadra", "partita_id",
]


def to_id_partita(data: str, avversario: str) -> str:
    return f"{data}_{avversario}".replace(" ", "_").replace("/", "-")


def _iso_date(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def map_event_row(raw: dict, partita_id: str, fallback_date: str) -> dict:
    data = _iso_date(str(raw.get("Data") or raw.get("data") or fallback_date))
    row = {
        "posizione": str(raw.get("Position") or raw.get("posizione") or "").strip(),
        "data": data,
        "evento": str(raw.get("Evento") or raw.get("evento") or raw.get("Name") or "").strip(),
        "chi": str(raw.get("Chi") or raw.get("chi") or "").strip(),
        "esito": str(raw.get("Esito") or raw.get("esito") or "").strip(),
        "dove": str(raw.get("Dove") or raw.get("dove") or "").strip(),
        "lato": str(raw.get("Lato") or raw.get("lato") or "").strip(),
        "piede": "",
        "portiere": str(raw.get("Portiere") or raw.get("portiere") or "").strip(),
        "quartetto": "",
        "quartetto_1": "",
        "quartetto_2": "",
        "quartetto_3": "",
        "quartetto_4": "",
        "squadra": str(raw.get("Squadra") or raw.get("squadra") or "").strip(),
        "partita_id": partita_id,
    }
    for key, val in list(row.items()):
        if val == "nan":
            row[key] = ""
    return {k: row.get(k, "") for k in COLONNE_EVENTO}


def list_partite() -> list[dict]:
    sb = get_supabase_client()
    res = (
        sb.table(TABELLA_PARTITE)
        .select("id, avversario, data, categoria, competizione, yt_link")
        .order("data", desc=True)
        .execute()
    )
    return res.data or []


def count_eventi(partita_id: str) -> int:
    sb = get_supabase_client()
    res = (
        sb.table(TABELLA_EVENTI)
        .select("id", count="exact")
        .eq("partita_id", partita_id)
        .execute()
    )
    return int(res.count or 0)


def create_partita(payload: dict) -> dict:
    data = _iso_date(str(payload.get("data") or ""))
    avversario = str(payload.get("avversario") or "").strip()
    if not data or not avversario:
        raise ValueError("Servono data e avversario")
    partita_id = to_id_partita(data, avversario)
    yt = str(payload.get("yt_link") or "").strip()
    row = {
        "id": partita_id,
        "data": data,
        "avversario": avversario,
        "competizione": str(payload.get("competizione") or "").strip(),
        "categoria": str(payload.get("categoria") or CATEGORIA).strip() or CATEGORIA,
        "yt_link": yt or None,
    }
    sb = get_supabase_client()
    sb.table(TABELLA_PARTITE).insert(row).execute()
    return row


def push_eventi(partita_id: str, events: list[dict], replace: bool, fallback_date: str) -> dict:
    if not partita_id:
        raise ValueError("partita_id mancante")
    rows = [map_event_row(e, partita_id, fallback_date) for e in events]
    rows = [r for r in rows if r["evento"] or r["posizione"]]
    rows.sort(key=lambda r: r["posizione"])
    sb = get_supabase_client()
    deleted = 0
    if replace:
        existing = count_eventi(partita_id)
        sb.table(TABELLA_EVENTI).delete().eq("partita_id", partita_id).execute()
        deleted = existing
    inserted = 0
    errors: list[dict[str, Any]] = []
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            sb.table(TABELLA_EVENTI).insert(batch).execute()
            inserted += len(batch)
        except Exception as exc:
            for row in batch:
                try:
                    sb.table(TABELLA_EVENTI).insert(row).execute()
                    inserted += 1
                except Exception as exc2:
                    errors.append({
                        "posizione": row.get("posizione"),
                        "evento": row.get("evento"),
                        "error": str(exc2) or str(exc),
                    })
    return {
        "partita_id": partita_id,
        "inserted": inserted,
        "deleted": deleted,
        "failed": len(errors),
        "errors": errors[:40],
        "tables": {"partite": TABELLA_PARTITE, "eventi": TABELLA_EVENTI},
    }
