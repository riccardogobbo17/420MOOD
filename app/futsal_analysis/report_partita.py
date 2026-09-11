"""Report PDF della singola partita, con layout dedicato.

Modulo volutamente indipendente da Streamlit: dipende solo da pandas,
matplotlib e reportlab. Puo' essere richiamato dalla pagina 1_partite oppure
da riga di comando (vedi app/scripts/genera_report.py), cosi' il report resta
lavorabile anche senza far partire l'app.

Struttura del PDF (A4 verticale, 2 pagine):
    1. Copertina + andamento partita + barre KPI + tipologie gol (torta)
    2. Scheda giocatori + portieri

Il DataFrame in ingresso e' quello degli eventi con le colonne minuscole
(evento, squadra, chi, esito, portiere, posizione). Se mancano 'Periodo' e
'tempoEffettivo' vengono calcolati qui.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .utils_eventi import (
    calcola_kpi_executive,
    calcola_stats_individuali,
    calcola_stats_portieri_individuali,
    calcola_tipologia_gol,
    mask_gol,
    mask_tiro,
)
from .utils_time import calcola_tempo_effettivo, tag_primo_secondo_tempo

# --- Palette sociali FMP: fucsia / nero / bianco (tono soft, non fluo) ---
FUCSIA = "#c45b8c"
FUCSIA_SCURO = "#8f3a62"
FUCSIA_CHIARO = "#e0a0c0"
FUCSIA_MEDIO = "#d478a8"
FUCSIA_CHIARISSIMO = "#efc8dc"
NERO = "#111111"
BIANCO = "#ffffff"
# Alias usati nei grafici (noi = fucsia, loro = nero/grigio)
BLU = FUCSIA
BLU_SCURO = FUCSIA_SCURO
GRIGIO = "#a3a3a3"
GRIGIO_SCURO = "#4a4a4a"
ROSSO = NERO  # gol avversari in nero
INCHIOSTRO = NERO
TENUE = "#6b6b6b"
BORDO = "#e5e5e5"
RIGA_ALT = "#f7f7f7"

DURATA_TEMPO_MIN = 20  # minuti effettivi per tempo
AMPIEZZA_FASCIA_MIN = 5

# Font: Georgia per titoli/punteggio (piu' elegante di Helvetica).
FONT_CORPO = "Helvetica"
FONT_CORPO_BOLD = "Helvetica-Bold"
FONT_TITOLO = FONT_CORPO_BOLD
FONT_PUNTEGGIO = FONT_CORPO_BOLD
_FONT_OK = False


def _assicura_font() -> None:
    """Registra Georgia se disponibile sul sistema (macOS)."""
    global FONT_TITOLO, FONT_PUNTEGGIO, _FONT_OK
    if _FONT_OK:
        return
    percorsi = [
        ("/System/Library/Fonts/Supplemental/Georgia.ttf",
         "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
        ("/Library/Fonts/Georgia.ttf", "/Library/Fonts/Georgia Bold.ttf"),
    ]
    for regular, bold in percorsi:
        try:
            pdfmetrics.registerFont(TTFont("FMPGeorgia", regular))
            pdfmetrics.registerFont(TTFont("FMPGeorgia-Bold", bold))
            FONT_TITOLO = "FMPGeorgia-Bold"
            FONT_PUNTEGGIO = "FMPGeorgia-Bold"
            _FONT_OK = True
            return
        except Exception:
            continue
    _FONT_OK = True  # fallback Helvetica gia' impostato


# Torta tipologie: rosa/fucsia ben contrastati (leggibili anche in legenda).
COLORI_TIPOLOGIA = {
    "Costruzione": "#5a1838",
    "Transizione": "#c2185b",
    "Palla inattiva": "#f48fb1",
    "Errore": "#880e4f",
    "non_taggato": "#fce4ec",
}


@dataclass
class MetaPartita:
    """Intestazione del report."""

    avversario: str = "Avversario"
    competizione: str = ""
    data: str = ""
    casa: str = "FMP"
    categoria: str = "Prima Squadra"


# =========================================================================
# Preparazione dati
# =========================================================================

# Colonne calcolate da utils_time: hanno un nome in camelCase da preservare.
COLONNE_TEMPO = ("Periodo", "tempoEffettivo", "tempoReale")


def prepara_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizza i nomi delle colonne e aggiunge Periodo/tempoEffettivo se mancanti."""
    df = df.copy()
    df = df.rename(columns={
        c: str(c).strip().lower().replace(" ", "_")
        for c in df.columns if c not in COLONNE_TEMPO
    })
    if "Periodo" not in df.columns:
        df["Periodo"] = tag_primo_secondo_tempo(df)
    if "tempoEffettivo" not in df.columns:
        df["tempoEffettivo"] = calcola_tempo_effettivo(df)
    return df


def _mmss_in_minuti(valore) -> Optional[float]:
    """Converte 'MM:SS' in minuti decimali; None se non interpretabile."""
    testo = str(valore).strip()
    if not testo or ":" not in testo:
        return None
    try:
        parti = [int(p) for p in testo.split(":")]
    except ValueError:
        return None
    if len(parti) != 2:
        return None
    return parti[0] + parti[1] / 60


def _minuti_evento(df: pd.DataFrame, mask) -> List[float]:
    """Minuti effettivi degli eventi selezionati, scartando quelli non datati."""
    if "tempoEffettivo" not in df.columns:
        return []
    minuti = [_mmss_in_minuti(v) for v in df.loc[mask, "tempoEffettivo"]]
    return [m for m in minuti if m is not None]


def _fmt(valore, percentuale: bool = False) -> str:
    if valore is None or (isinstance(valore, float) and pd.isna(valore)):
        return "—"
    if percentuale:
        numero = float(valore)
        return f"{numero:.0f}%" if numero.is_integer() else f"{numero:.1f}%"
    if isinstance(valore, float):
        return str(int(valore)) if valore.is_integer() else f"{valore:.1f}"
    return str(valore)


# =========================================================================
# Grafici
# =========================================================================

# (etichetta, chiave in kpi_executive, e' una percentuale)
VOCI_CONFRONTO = [
    ("Gol", "gol", False),
    ("Tiri totali", "tiri", False),
    ("Tiri in porta", "tiri_in_porta", False),
    ("Efficacia tiro", "efficacia_tiro_pct", True),
    ("Conv. Tiri", "conversione_pct", True),
    ("Parate", "parate", False),
    ("% Parate", "perc_parate", True),
    ("Angoli", "angoli", False),
    ("Palle recuperate", "recuperi", False),
    ("Palle perse", "perse", False),
]


def _kpi_per_barre(kpi: dict) -> dict:
    """Copia i KPI con palle recuperate/perse specchiate sull'avversario.

    Nel tagging 2026/27 perse e recuperi sono marcati solo per noi: la palla
    recuperata nostra e' una persa avversaria e viceversa.
    """
    noi = dict(kpi.get("Noi") or {})
    loro = dict(kpi.get("Loro") or {})
    recuperi = int(noi.get("recuperi") or 0)
    perse = int(noi.get("perse") or 0)
    noi["recuperi"] = recuperi
    noi["perse"] = perse
    loro["recuperi"] = perse
    loro["perse"] = recuperi
    return {"Noi": noi, "Loro": loro, "tipologia_gol": kpi.get("tipologia_gol")}


# Larghezza della pista delle barre (unita' asse x) e colonna etichette.
LARGHEZZA_PISTA = 1.0
LARGHEZZA_ETICHETTA = 0.28
PISTA_CHIARA = "#dedede"  # fondo grigio chiaro sotto i valori


def _figura_confronto(kpi: dict, casa: str, ospite: str) -> plt.Figure:
    """Pista piena in grigio chiaro; sopra, fucsia/grigio fino al valore.

    Conte: normalizzate sul max della coppia. Percentuali: ogni lato usa la
    propria scala 0-100% (pista piena = 100%).
    """
    noi, loro = kpi.get("Noi", {}), kpi.get("Loro", {})
    voci = [
        (etichetta, noi.get(chiave), loro.get(chiave), pct)
        for etichetta, chiave, pct in VOCI_CONFRONTO
        if noi.get(chiave) is not None or loro.get(chiave) is not None
    ]

    meta_barra = 0.42
    altezza = max(2.4, 0.36 * len(voci) + 0.75)
    fig, ax = plt.subplots(figsize=(7.0, altezza))
    meta = LARGHEZZA_PISTA / 2
    label_x = -meta - 0.04

    for y, (etichetta, v_noi, v_loro, pct) in enumerate(voci):
        a = float(v_noi or 0)
        b = float(v_loro or 0)
        if pct:
            len_noi = min(max(a, 0.0), 100.0) / 100.0 * meta
            len_loro = min(max(b, 0.0), 100.0) / 100.0 * meta
        else:
            scala = max(a, b, 1.0)
            len_noi = (a / scala) * meta
            len_loro = (b / scala) * meta

        ax.barh(y, -meta, left=0, height=meta_barra, color=PISTA_CHIARA,
                edgecolor="none", zorder=2)
        ax.barh(y, meta, left=0, height=meta_barra, color=PISTA_CHIARA,
                edgecolor="none", zorder=2)
        if len_noi > 0:
            ax.barh(y, -len_noi, left=0, height=meta_barra, color=BLU,
                    edgecolor="none", zorder=3)
        if len_loro > 0:
            ax.barh(y, len_loro, left=0, height=meta_barra, color=GRIGIO,
                    edgecolor="none", zorder=3)

        ax.text(-meta + 0.03, y, _fmt(v_noi, pct),
                ha="left", va="center", fontsize=7.5, fontweight="bold",
                color=BLU_SCURO, zorder=5)
        ax.text(meta - 0.03, y, _fmt(v_loro, pct),
                ha="right", va="center", fontsize=7.5, fontweight="bold",
                color=GRIGIO_SCURO, zorder=5)
        ax.text(label_x, y, etichetta, ha="right", va="center",
                fontsize=7.2, color=GRIGIO_SCURO, zorder=4)

    ax.axvline(0, color="#d4d4d4", linewidth=0.8, zorder=4)
    ax.set_xlim(label_x - LARGHEZZA_ETICHETTA, meta + 0.06)
    ax.set_ylim(len(voci) - 0.4, -1.05)
    ax.set_yticks([])
    ax.set_xticks([])
    for lato in ("top", "right", "bottom", "left"):
        ax.spines[lato].set_visible(False)

    ax.text(-meta / 2, -0.88, casa.upper(), ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=BLU)
    ax.text(meta / 2, -0.88, ospite.upper(), ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=GRIGIO_SCURO)

    fig.tight_layout(pad=0.25)
    return fig


def _densita_gaussiana(minuti: Sequence[float], x: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    """Somma di gaussiane centrate su ogni evento → curva tipo violino."""
    if not minuti:
        return np.zeros_like(x, dtype=float)
    y = np.zeros_like(x, dtype=float)
    for m in minuti:
        y += np.exp(-0.5 * ((x - m) / sigma) ** 2)
    return y


def _gol_con_marcatori(df: pd.DataFrame, squadra: str) -> List[tuple]:
    """Lista (minuto, etichetta) dei gol di `squadra`.

    L'etichetta e' il marcatore, oppure 'Autogol' se l'evento e' un autogol
    a favore di quella squadra.
    """
    mask = mask_gol(df, squadra)
    if not mask.any():
        return []
    out = []
    for _, riga in df.loc[mask].iterrows():
        minuto = _mmss_in_minuti(riga.get("tempoEffettivo"))
        if minuto is None:
            continue
        evento = str(riga.get("evento") or "").strip()
        if evento == "Autogol":
            etichetta = "Autogol"
        else:
            etichetta = str(riga.get("chi") or "").strip().title()
        out.append((minuto, etichetta))
    return out


def _figura_andamento(df: pd.DataFrame, casa: str, ospite: str) -> Optional[plt.Figure]:
    """Tiri per fasce di 5' (barre, noi sopra / loro sotto) con gol + marcatore."""
    tiri_noi = _minuti_evento(df, mask_tiro(df, "Noi"))
    tiri_loro = _minuti_evento(df, mask_tiro(df, "Loro"))
    gol_noi = _gol_con_marcatori(df, "Noi")
    gol_loro = _gol_con_marcatori(df, "Loro")

    if not (tiri_noi or tiri_loro or gol_noi or gol_loro):
        return None

    durata = 2 * DURATA_TEMPO_MIN
    bordi = list(range(0, durata + AMPIEZZA_FASCIA_MIN, AMPIEZZA_FASCIA_MIN))
    centri = [(bordi[i] + bordi[i + 1]) / 2 for i in range(len(bordi) - 1)]

    def per_fascia(minuti: Sequence[float]) -> List[int]:
        conteggi = [0] * (len(bordi) - 1)
        for m in minuti:
            indice = min(int(m // AMPIEZZA_FASCIA_MIN), len(conteggi) - 1)
            conteggi[max(indice, 0)] += 1
        return conteggi

    conteggi_noi = per_fascia(tiri_noi)
    conteggi_loro = per_fascia(tiri_loro)

    fig, ax = plt.subplots(figsize=(6.6, 2.35))
    larghezza_barra = AMPIEZZA_FASCIA_MIN * 0.78
    ax.bar(centri, conteggi_noi, width=larghezza_barra,
           color=BLU, edgecolor="white", linewidth=0.6, zorder=3,
           label=f"Tiri {casa}")
    ax.bar(centri, [-c for c in conteggi_loro], width=larghezza_barra,
           color=GRIGIO, edgecolor="white", linewidth=0.6, zorder=3,
           label=f"Tiri {ospite}")

    limite = max([1] + conteggi_noi + conteggi_loro)
    corsia = limite + 1.25
    for m, nome in gol_noi:
        ax.plot([m], [corsia], marker="o", markersize=5.5, color=BLU_SCURO, zorder=5)
        if nome:
            ax.annotate(
                nome, (m, corsia), textcoords="offset points", xytext=(0, -7),
                ha="center", va="top", fontsize=5.8, color=BLU_SCURO,
                fontweight="bold", zorder=6,
            )
    for m, nome in gol_loro:
        ax.plot([m], [-corsia], marker="o", markersize=5.5, color=ROSSO, zorder=5)
        if nome:
            ax.annotate(
                nome, (m, -corsia), textcoords="offset points", xytext=(0, 7),
                ha="center", va="bottom", fontsize=5.8, color=ROSSO,
                fontweight="bold", zorder=6,
            )

    ax.axvline(DURATA_TEMPO_MIN, color=BORDO, linewidth=1.0, linestyle="--", zorder=2)
    ax.text(DURATA_TEMPO_MIN, corsia + 0.45, "intervallo", ha="center", va="bottom",
            fontsize=6.5, color=TENUE)

    ax.axhline(0, color=BORDO, linewidth=0.8, zorder=2)
    ax.set_xlim(0, durata)
    ax.set_ylim(-corsia - 1.1, corsia + 0.9)
    ax.set_xticks(bordi)
    ax.set_xticklabels([f"{b}'" for b in bordi], fontsize=7, color=TENUE)
    passi = range(-limite, limite + 1, max(1, limite // 3))
    ax.set_yticks(list(passi))
    ax.set_yticklabels([str(abs(v)) for v in passi], fontsize=7, color=TENUE)
    ax.set_ylabel("tiri", fontsize=7, color=TENUE)
    ax.grid(axis="y", color="#f0f0f0", linewidth=0.6, zorder=1)
    ax.set_axisbelow(True)
    for lato in ("top", "right", "left"):
        ax.spines[lato].set_visible(False)
    ax.spines["bottom"].set_color(BORDO)

    ax.legend(
        handles=[
            Patch(facecolor=BLU, label=f"Tiri {casa}"),
            Patch(facecolor=GRIGIO, label=f"Tiri {ospite}"),
            Line2D([], [], marker="o", linestyle="none", color=BLU_SCURO,
                   label=f"Gol {casa}"),
            Line2D([], [], marker="o", linestyle="none", color=ROSSO,
                   label=f"Gol {ospite}"),
        ],
        loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4,
        fontsize=6.5, frameon=False, handlelength=1.1, columnspacing=1.3,
    )

    fig.tight_layout(pad=0.25)
    return fig


def _colori_fette(etichette: Sequence[str]) -> List[str]:
    """Rosa/fucsia a contrasto marcato fra una fetta e l'altra."""
    scala = [
        "#5a1838",  # bordeaux
        "#c2185b",  # fucsia vivo
        "#f48fb1",  # rosa chiaro
        "#880e4f",  # magenta scuro
        "#ec407a",  # rosa medio
        "#f8bbd0",  # rosa pastel
        "#ad1457",
    ]
    out = []
    for i, e in enumerate(etichette):
        out.append(COLORI_TIPOLOGIA.get(e) or scala[i % len(scala)])
    return out


def _figura_tipologie_gol(kpi: dict) -> Optional[plt.Figure]:
    """Due torte affiancate; % in bianco, senza legenda sotto."""
    tipologia = kpi.get("tipologia_gol") or {}
    fatti = {k: v for k, v in (tipologia.get("fatti") or {}).items() if v}
    subiti = {k: v for k, v in (tipologia.get("subiti") or {}).items() if v}
    if not fatti and not subiti:
        return None

    fig, assi = plt.subplots(1, 2, figsize=(5.8, 2.05))
    for ax, dati, titolo in (
        (assi[0], fatti, "Gol fatti"),
        (assi[1], subiti, "Gol subiti"),
    ):
        if not dati:
            ax.text(0.5, 0.5, "nessun gol", ha="center", va="center",
                    fontsize=8, color=TENUE)
            ax.set_axis_off()
            ax.set_title(titolo, fontsize=8.5, color=GRIGIO_SCURO, pad=3)
            continue

        etichette = list(dati.keys())
        valori = list(dati.values())
        colori = _colori_fette(etichette)
        labels = [f"{e.replace('_', ' ').capitalize()} ({v})" for e, v in zip(etichette, valori)]
        cunei, testi, autotexts = ax.pie(
            valori,
            colors=colori,
            labels=labels,
            startangle=90,
            wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 1.1},
            autopct=lambda p: f"{p:.0f}%" if p >= 8 else "",
            pctdistance=0.70,
            labeldistance=1.12,
            textprops={"fontsize": 6.2, "color": GRIGIO_SCURO},
        )
        for t in autotexts:
            t.set_fontsize(7.5)
            t.set_color("white")
            t.set_fontweight("bold")
        for t in testi:
            t.set_fontsize(6.0)
            t.set_color(GRIGIO_SCURO)
        ax.set_title(titolo, fontsize=8.5, color=GRIGIO_SCURO, pad=3)

    fig.tight_layout(pad=0.25)
    return fig


def _immagine(fig: plt.Figure, larghezza: float, dpi: int = 200) -> Image:
    """Converte una figura matplotlib in un flowable Image della larghezza data."""
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    buffer.seek(0)
    # Usa le dimensioni reali del PNG (bbox_inches=tight cambia l'aspect ratio).
    from PIL import Image as PILImage
    with PILImage.open(buffer) as pil:
        px_w, px_h = pil.size
    buffer.seek(0)
    return Image(buffer, width=larghezza, height=larghezza * px_h / px_w)


# =========================================================================
# Stili e blocchi tabellari
# =========================================================================

def _stili() -> dict:
    _assicura_font()
    base = getSampleStyleSheet()["Normal"]
    return {
        "brand": ParagraphStyle(
            "Brand", parent=base, fontName=FONT_TITOLO, fontSize=13,
            textColor=colors.HexColor(FUCSIA), alignment=TA_CENTER, spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "Meta", parent=base, fontName=FONT_CORPO, fontSize=8.5,
            textColor=colors.HexColor(TENUE), alignment=TA_CENTER, spaceAfter=2,
        ),
        "squadra": ParagraphStyle(
            "Squadra", parent=base, fontName=FONT_TITOLO, fontSize=11,
            textColor=colors.HexColor(NERO), alignment=TA_CENTER,
        ),
        "punteggio": ParagraphStyle(
            "Punteggio", parent=base, fontName=FONT_PUNTEGGIO, fontSize=16,
            textColor=colors.HexColor(NERO), alignment=TA_CENTER, leading=20,
            spaceBefore=4, spaceAfter=4,
        ),
        "sezione": ParagraphStyle(
            "Sezione", parent=base, fontName=FONT_TITOLO, fontSize=10,
            textColor=colors.HexColor(FUCSIA), alignment=TA_CENTER,
            spaceBefore=4, spaceAfter=8,
        ),
        "cella": ParagraphStyle(
            "Cella", parent=base, fontName=FONT_CORPO, fontSize=7.5,
            textColor=colors.HexColor(GRIGIO_SCURO), alignment=TA_CENTER,
        ),
        "nota": ParagraphStyle(
            "Nota", parent=base, fontName=FONT_CORPO, fontSize=6.8,
            textColor=colors.HexColor(TENUE), alignment=TA_CENTER,
            spaceBefore=6, leading=9,
        ),
    }


def _stile_tabella(prima_colonna_a_sinistra: bool = True) -> TableStyle:
    comandi = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NERO)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_CORPO_BOLD),
        ("FONTNAME", (0, 1), (0, -1), FONT_CORPO_BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(INCHIOSTRO)),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(RIGA_ALT)]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDO)),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor(BORDO)),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if prima_colonna_a_sinistra:
        comandi.append(("ALIGN", (0, 0), (0, -1), "LEFT"))
    return TableStyle(comandi)


def _tabella(intestazioni: Sequence[str], righe: Sequence[Sequence[str]],
             larghezze: Sequence[float]) -> Table:
    tabella = Table([list(intestazioni)] + [list(r) for r in righe],
                    colWidths=list(larghezze), hAlign="LEFT", repeatRows=1)
    tabella.setStyle(_stile_tabella())
    return tabella


# =========================================================================
# Pagine
# =========================================================================

def _pagina_executive(df, meta, kpi, stili, larghezza) -> List:
    elementi: List = []
    gol_casa = int(mask_gol(df, "Noi").sum())
    gol_ospite = int(mask_gol(df, "Loro").sum())
    avversario = meta.avversario.title()

    elementi.append(Paragraph(f"{meta.casa} MATCH REPORT", stili["brand"]))
    dettagli = [d for d in (meta.competizione, meta.data, meta.categoria) if d]
    if dettagli:
        elementi.append(Paragraph(" · ".join(dettagli), stili["meta"]))
    elementi.append(Spacer(1, 6))

    # Risultato leggero, senza riquadro: "FMP  4 – 3  Avversario"
    elementi.append(Paragraph(
        f'{meta.casa}&nbsp;&nbsp;'
        f'<font color="{FUCSIA}" size="18"><b>{gol_casa} – {gol_ospite}</b></font>'
        f'&nbsp;&nbsp;{avversario}',
        stili["punteggio"],
    ))
    elementi.append(Spacer(1, 4))

    # 1) Andamento (grandezza precedente)
    elementi.append(Paragraph("ANDAMENTO PARTITA", stili["sezione"]))
    figura_and = _figura_andamento(df, meta.casa, avversario)
    if figura_and is None:
        elementi.append(Paragraph("Dati insufficienti per il grafico.", stili["meta"]))
    else:
        img_and = _immagine(figura_and, larghezza * 0.90)
        img_and.hAlign = "CENTER"
        elementi.append(img_and)
    elementi.append(Spacer(1, 3))

    # 2) Barre KPI (spessore ripristinato + sfondo pista)
    elementi.append(Paragraph("CONFRONTO", stili["sezione"]))
    kpi_barre = _kpi_per_barre(kpi)
    elementi.append(_immagine(
        _figura_confronto(kpi_barre, meta.casa, avversario), larghezza * 0.96,
    ))
    elementi.append(Paragraph(
        "Efficacia tiro = tiri in porta / tiri totali. "
        "Conv. Tiri = gol / tiri in porta.",
        stili["nota"],
    ))
    elementi.append(Spacer(1, 2))

    # 3) Tipologie (senza titolo sezione, per risparmiare spazio in pagina 1)
    figura_tipo = _figura_tipologie_gol(kpi)
    if figura_tipo is not None:
        img_tipo = _immagine(figura_tipo, larghezza * 0.68)
        img_tipo.hAlign = "CENTER"
        elementi.append(img_tipo)

    return elementi


def _blocco_tipologia_gol(kpi, meta, stili, larghezza) -> Optional[Table]:
    """LEGACY: tabella tipologie, sostituita dalla torta in _figura_tipologie_gol."""
    tipologia = kpi.get("tipologia_gol") or {}
    fatti = tipologia.get("fatti", {})
    subiti = tipologia.get("subiti", {})
    voci = [k for k in fatti if fatti.get(k) or subiti.get(k)]
    if not voci:
        return None
    righe = [[str(v).replace("_", " ").capitalize(), _fmt(fatti.get(v)), _fmt(subiti.get(v))]
             for v in voci]
    return _tabella(
        ["Come nascono i gol", "Fatti", "Subiti"],
        righe,
        [larghezza * 0.52, larghezza * 0.24, larghezza * 0.24],
    )


def _pagina_andamento(df, meta, stili, larghezza) -> List:
    """LEGACY: andamento + timeline erano pagina 2; ora l'andamento e' in copertina."""
    elementi: List = [Paragraph("ANDAMENTO PARTITA", stili["sezione"])]
    avversario = meta.avversario.title()
    figura = _figura_andamento(df, meta.casa, avversario)
    if figura is None:
        elementi.append(Paragraph("Dati insufficienti per il grafico.", stili["meta"]))
    else:
        elementi.append(_immagine(figura, larghezza))
    # Timeline gol rimossa dal report (tenuta come funzione sotto per riuso).
    return elementi


def _blocco_timeline(df, meta, larghezza) -> Optional[Table]:
    """LEGACY: timeline gol tabellare, non piu' inclusa nel PDF."""
    gol = df[mask_gol(df, "Noi") | mask_gol(df, "Loro")].copy()
    if gol.empty:
        return None

    gol["_minuto"] = [_mmss_in_minuti(v) for v in gol["tempoEffettivo"]]
    gol = gol.sort_values("_minuto", na_position="last")

    avversario = meta.avversario.title()
    casa_gol = 0
    ospite_gol = 0
    righe = []
    for _, riga in gol.iterrows():
        nostro = str(riga.get("squadra", "")).strip() == "Noi"
        if nostro:
            casa_gol += 1
        else:
            ospite_gol += 1
        minuto = str(riga.get("tempoEffettivo") or "").strip()
        marcatore = str(riga.get("chi") or "").strip().title() or "—"
        righe.append([
            f"{minuto}'" if minuto else "—",
            meta.casa if nostro else avversario,
            marcatore,
            str(riga.get("esito") or "").strip() or "—",
            f"{casa_gol}-{ospite_gol}",
        ])

    return _tabella(
        ["Minuto", "Squadra", "Marcatore", "Tipo azione", "Punteggio"],
        righe,
        [larghezza * 0.13, larghezza * 0.20, larghezza * 0.24, larghezza * 0.28, larghezza * 0.15],
    )


PRECISIONE_TIRO = "__precisione__"

# (etichetta colonna, chiave nelle stats individuali) nell'ordine di stampa
COLONNE_GIOCATORE = [
    ("Gol", "gol_fatti"),
    ("Assist", "assist"),
    ("Tiri", "tiri_totali"),
    ("In porta", "tiri_in_porta_totali"),
    ("Prec. %", PRECISIONE_TIRO),
    ("Fuori", "tiri_fuori"),
    ("Pali", "palo_traversa"),
    ("Ribatt.", "tiri_ribattuti_noi"),
    ("Perse", "palle_perse"),
    ("Recup.", "palle_recuperate"),
    ("Falli F", "falli_fatti"),
    ("Falli S", "falli_subiti"),
    ("Gialli", "ammonizioni"),
]


def _precisione_tiro(stats: dict) -> Optional[float]:
    tiri = stats.get("tiri_totali", 0)
    if not tiri:
        return None
    return round(stats.get("tiri_in_porta_totali", 0) / tiri * 100, 1)


def _colonne_attive(individuali: dict):
    """Colonne con almeno un valore, piu' l'elenco di quelle scartate.

    Molti eventi del tagging 2026/27 non hanno il campo 'Chi' compilato
    (recuperi, falli): mostrarne la colonna vorrebbe dire stampare una fila di
    zeri. Il filtro e' dinamico, cosi' se il tagging si arricchisce le colonne
    ricompaiono da sole.
    """
    def accessore(campo):
        return lambda stats: stats.get(campo, 0)

    attive, scartate = [], []
    for etichetta, campo in COLONNE_GIOCATORE:
        chiave_test = "tiri_totali" if campo == PRECISIONE_TIRO else campo
        if any(stats.get(chiave_test, 0) for stats in individuali.values()):
            if campo == PRECISIONE_TIRO:
                attive.append((etichetta, _precisione_tiro, True))
            else:
                attive.append((etichetta, accessore(campo), False))
        elif campo != PRECISIONE_TIRO:
            scartate.append(etichetta)
    return attive, scartate


def _pagina_giocatori(df, meta, stili, larghezza) -> List:
    elementi: List = [Paragraph("SCHEDA GIOCATORI", stili["sezione"])]

    individuali = calcola_stats_individuali(df, by_zona=False)
    if individuali:
        colonne, scartate = _colonne_attive(individuali)

        # Ordina per contributo offensivo, poi per volume di gioco.
        def chiave(voce):
            nome, stats = voce
            return (
                -(stats.get("gol_fatti", 0) + stats.get("assist", 0)),
                -stats.get("tiri_totali", 0),
                -stats.get("palle_recuperate", 0),
                nome,
            )

        righe = [
            [nome.title()] + [_fmt(leggi(stats), pct) for _, leggi, pct in colonne]
            for nome, stats in sorted(individuali.items(), key=chiave)
        ]

        campi = {c for _, c in COLONNE_GIOCATORE if c != PRECISIONE_TIRO}
        totali = {campo: sum(s.get(campo, 0) for s in individuali.values())
                  for campo in campi}
        righe.append(["TOTALE"] + [_fmt(leggi(totali), pct) for _, leggi, pct in colonne])

        prima = larghezza * 0.16
        resto = (larghezza - prima) / len(colonne)
        tabella = _tabella(
            ["Giocatore"] + [e for e, _, _ in colonne],
            righe,
            [prima] + [resto] * len(colonne),
        )
        tabella.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f3f3f3")),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor(GRIGIO)),
        ]))
        elementi.append(tabella)

        nota = ("Ordinamento per gol + assist. Prec. % = tiri in porta sul totale "
                "dei tiri. Ribatt. = tiri avversari ribattuti dal giocatore.")
        if scartate:
            nota += (" Colonne non mostrate perché il campo Chi non è taggato su "
                     f"questi eventi: {', '.join(scartate)}.")
        nota += (" Senza il tagging del quartetto i gol subiti non sono più "
                 "attribuibili ai giocatori di movimento.")
        elementi.append(Paragraph(nota, stili["nota"]))
    else:
        elementi.append(Paragraph("Nessun evento individuale taggato.", stili["meta"]))

    portieri = calcola_stats_portieri_individuali(df, by_zona=False)
    if portieri:
        righe = [[
            nome.title(),
            _fmt(stats.get("parate", 0)),
            _fmt(stats.get("gol_subiti", 0)),
            _fmt(stats.get("tiri_in_porta_subiti", 0)),
            _fmt(stats.get("percentuale_parate", 0), percentuale=True),
        ] for nome, stats in sorted(portieri.items())]
        elementi.append(Spacer(1, 16))
        elementi.append(KeepTogether([
            Paragraph("PORTIERI", stili["sezione"]),
            _tabella(
                ["Portiere", "Parate", "Gol subiti", "Tiri in porta subiti", "% Parate"],
                righe,
                [larghezza * 0.22, larghezza * 0.14, larghezza * 0.16,
                 larghezza * 0.28, larghezza * 0.20],
            ),
        ]))
    return elementi


# =========================================================================
# Ingresso pubblico
# =========================================================================

def genera_report_partita(df: pd.DataFrame, meta: MetaPartita) -> bytes:
    """Costruisce il PDF del report partita e ne restituisce i byte."""
    df = prepara_dataframe(df)
    kpi = calcola_kpi_executive(df)
    if "tipologia_gol" not in kpi:
        kpi["tipologia_gol"] = calcola_tipologia_gol(df)

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32,
        title=f"Report {meta.casa} vs {meta.avversario.title()}",
        author=meta.casa,
    )
    stili = _stili()
    larghezza = documento.width

    elementi: List = []
    elementi += _pagina_executive(df, meta, kpi, stili, larghezza)
    # Pagina andamento/timeline rimossa: l'andamento e' in prima pagina.
    # elementi.append(PageBreak())
    # elementi += _pagina_andamento(df, meta, stili, larghezza)
    elementi.append(PageBreak())
    elementi += _pagina_giocatori(df, meta, stili, larghezza)

    documento.build(elementi, onLaterPages=_pie_pagina, onFirstPage=_pie_pagina)
    buffer.seek(0)
    return buffer.read()


def _pie_pagina(canvas, documento) -> None:
    """Numero di pagina in basso a destra."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor(GRIGIO))
    canvas.drawRightString(A4[0] - 36, 20, str(canvas.getPageNumber()))
    canvas.restoreState()
