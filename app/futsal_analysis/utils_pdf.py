"""Utility per generare report in PDF a partire da DataFrame e figure."""

from __future__ import annotations

import numbers
from dataclasses import dataclass
from io import BytesIO
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
from matplotlib.figure import Figure
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


Section = Tuple[str, pd.DataFrame]


@dataclass
class PdfTableSection:
    title: str
    dataframe: pd.DataFrame


@dataclass
class PdfImageSection:
    title: str
    image_bytes: bytes
    max_width: int = 380


@dataclass
class PdfMatchMeta:
    """Metadati copertina report partita."""

    home_name: str = "FMP"
    away_name: str = "Avversario"
    home_goals: int = 0
    away_goals: int = 0
    competition: str = ""
    match_date: str = ""
    category: str = ""


def _format_kpi_value(value: object, is_pct: bool = False) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if is_pct:
        return f"{value:.0f}%" if float(value).is_integer() else f"{value:.1f}%"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _build_cover_elements(
    meta: PdfMatchMeta,
    timeline_df: Optional[pd.DataFrame],
    styles,
    page_width: float,
) -> List:
    """Copertina: score, meta, timeline gol."""
    elements: List = []

    brand = ParagraphStyle(
        "CoverBrand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#1565c0"),
        alignment=1,
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=2,
    )
    score_style = ParagraphStyle(
        "CoverScore",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        leading=32,
    )
    team_style = ParagraphStyle(
        "CoverTeam",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
    )
    section_style = ParagraphStyle(
        "CoverSection",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#1565c0"),
        spaceBefore=10,
        spaceAfter=4,
    )
    goal_style = ParagraphStyle(
        "CoverGoal",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#334155"),
        leading=11,
    )

    elements.append(Paragraph("FMP MATCH REPORT", brand))
    meta_bits = [b for b in [meta.competition, meta.match_date, meta.category] if b]
    if meta_bits:
        elements.append(Paragraph(" · ".join(meta_bits), meta_style))
    elements.append(Spacer(1, 10))

    score_table = Table(
        [
            [
                Paragraph(meta.home_name, team_style),
                Paragraph(f"{meta.home_goals}  –  {meta.away_goals}", score_style),
                Paragraph(meta.away_name, team_style),
            ]
        ],
        colWidths=[page_width * 0.35, page_width * 0.30, page_width * 0.35],
    )
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(score_table)

    if timeline_df is not None and not timeline_df.empty:
        elements.append(Paragraph("TIMELINE GOL", section_style))
        rows = [["Minuto", "Squadra", "Marcatore", "Tipo azione"]]
        for _, row in timeline_df.iterrows():
            rows.append(
                [
                    str(row.get("Minuto", "")),
                    str(row.get("Squadra", "")),
                    str(row.get("Marcatore", "")),
                    str(row.get("Tipo Azione", "")),
                ]
            )
        tl = Table(rows, colWidths=[page_width * 0.15, page_width * 0.18, page_width * 0.34, page_width * 0.33])
        tl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        elements.append(tl)

    elements.append(PageBreak())
    return elements


def _build_kpi_dashboard_elements(
    kpi: dict,
    home_name: str,
    away_name: str,
    styles,
    page_width: float,
) -> List:
    """Pagina KPI executive Noi vs Loro."""
    elements: List = []
    title_style = ParagraphStyle(
        "KpiTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=8,
    )
    label_style = ParagraphStyle(
        "KpiLabel",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        leading=9,
    )
    value_style = ParagraphStyle(
        "KpiValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        leading=13,
    )
    head_style = ParagraphStyle(
        "KpiHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
        alignment=1,
    )

    noi = kpi.get("Noi", {})
    loro = kpi.get("Loro", {})

    elements.append(Paragraph("KPI EXECUTIVE DASHBOARD", title_style))

    rows_def = [
        ("Gol", "gol", False),
        ("Assist", "assist", False),
        ("Tiri totali", "tiri", False),
        ("Tiri in porta", "tiri_in_porta", False),
        ("Efficacia tiro", "efficacia_tiro_pct", True),
        ("Conversione", "conversione_pct", True),
        ("Recuperi", "recuperi", False),
        ("Palle perse", "perse", False),
        ("Falli", "falli", False),
        ("Parate", "parate", False),
        ("% Parate", "perc_parate", True),
        ("Angoli", "angoli", False),
        ("Laterali", "laterali", False),
        ("Punizioni", "punizioni", False),
    ]

    header = [
        Paragraph("Indicatore", head_style),
        Paragraph(home_name or "FMP", head_style),
        Paragraph(away_name or "Avversario", head_style),
    ]
    data = [header]
    for label, key, is_pct in rows_def:
        data.append(
            [
                Paragraph(label, label_style),
                Paragraph(_format_kpi_value(noi.get(key), is_pct=is_pct), value_style),
                Paragraph(_format_kpi_value(loro.get(key), is_pct=is_pct), value_style),
            ]
        )

    def stile_blocco() -> TableStyle:
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f1f5f9")),
                ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )

    # Layout a due colonne: KPI a sinistra, tipologia gol a destra, cosi' la
    # pagina resta una sola anche quando si aggiungono indicatori.
    kpi_width = page_width * 0.58
    goal_width = page_width * 0.38
    gap = page_width * 0.04

    table = Table(data, colWidths=[kpi_width * 0.40, kpi_width * 0.30, kpi_width * 0.30], hAlign="LEFT")
    table.setStyle(stile_blocco())

    # Tipologia dei gol (Esito dell'evento Gol): come li facciamo, come li prendiamo.
    tipologia = kpi.get("tipologia_gol") or {}
    fatti = tipologia.get("fatti", {})
    subiti = tipologia.get("subiti", {})
    voci = [k for k in fatti.keys() if fatti.get(k) or subiti.get(k)]

    colonna_destra: List = []
    if voci:
        rows = [[
            Paragraph("Come nascono i gol", head_style),
            Paragraph("Fatti", head_style),
            Paragraph("Subiti", head_style),
        ]]
        for voce in voci:
            rows.append(
                [
                    Paragraph(str(voce).replace("_", " ").capitalize(), label_style),
                    Paragraph(_format_kpi_value(fatti.get(voce)), value_style),
                    Paragraph(_format_kpi_value(subiti.get(voce)), value_style),
                ]
            )
        goal_table = Table(rows, colWidths=[goal_width * 0.48, goal_width * 0.26, goal_width * 0.26], hAlign="LEFT")
        goal_table.setStyle(stile_blocco())
        colonna_destra = [goal_table]

    layout = Table(
        [[table, "", colonna_destra or ""]],
        colWidths=[kpi_width, gap, goal_width],
        hAlign="CENTER",
    )
    layout.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(layout)

    note = ParagraphStyle(
        "KpiNote",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#94a3b8"),
        spaceBefore=10,
        leading=9,
    )
    elements.append(
        Paragraph(
            "Nota: recuperi e palle perse sono taggati solo per FMP. Le punizioni non "
            "entrano nel conteggio tiri, ma le punizioni parate contano come parata.",
            note,
        )
    )
    elements.append(PageBreak())
    return elements


def _format_value(value: object) -> str:
    """Formatta un valore qualsiasi in stringa per il PDF."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    if isinstance(value, numbers.Number):
        if isinstance(value, float):
            if value.is_integer():
                return f"{int(value)}"
            return f"{value:.2f}"
        return str(value)

    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y %H:%M")

    return str(value)


def _dataframe_to_table_data(df: pd.DataFrame, index_column: Optional[str] = None) -> list[list[str]]:
    """Converte un DataFrame in una lista di liste per l'uso con ReportLab.
    
    Args:
        df: DataFrame da convertire
        index_column: Nome della colonna da usare come indice (se None, usa il comportamento standard)
    """

    df_reset = df.copy()
    
    # Se è specificata una colonna indice, usala come indice
    if index_column and index_column in df_reset.columns:
        df_reset = df_reset.set_index(index_column)
        df_reset = df_reset.reset_index()
    else:
        df_reset = df_reset.reset_index()

    # Rinomina la colonna dell'indice per renderla più leggibile
    first_col = df_reset.columns[0]
    if first_col == "index":
        df_reset = df_reset.rename(columns={first_col: ""})

    df_reset = df_reset.fillna("")
    
    # Rinomina colonne specifiche per uniformità
    column_rename_map = {
        "Tiri Ribattuti Noi": "Tiri Subiti Ribattuti",
        "Tiri Loro Ribattuti Da Noi": "Tiri Subiti Ribattuti",
        "Tiri Ribattuti Da Noi": "Tiri Subiti Ribattuti",
    }
    df_reset = df_reset.rename(columns=column_rename_map)

    header = [str(col) for col in df_reset.columns]
    rows = [[_format_value(value) for value in row] for row in df_reset.itertuples(index=False)]

    if header:
        first_header = header[0].strip().lower()
        if first_header in ("", "index"):
            sequential = True
            for expected, row in enumerate(rows):
                value = row[0]
                if value == "":
                    sequential = False
                    break
                try:
                    idx_val = int(value)
                except (TypeError, ValueError):
                    sequential = False
                    break
                if idx_val != expected:
                    sequential = False
                    break
            if sequential:
                header = header[1:]
                rows = [row[1:] for row in rows]

    return [header] + rows


def generate_pdf_from_tables(title: str, sections: Iterable[Section]) -> bytes:
    """Genera un PDF con un titolo e una lista di sezioni tabellari.

    Args:
        title: Titolo principale del report.
        sections: Iterable di tuple (nome_sezione, dataframe).

    Returns:
        bytes: Contenuto del PDF.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=25,
        rightMargin=25,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f2f6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5f5")),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]
    )

    for section_title, df in sections:
        if df.empty:
            continue

        elements.append(Paragraph(section_title, styles["Heading2"]))

        table_data = _dataframe_to_table_data(df)
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(table_style)

        elements.append(table)
        elements.append(Spacer(1, 18))

    doc.build(elements)

    buffer.seek(0)
    return buffer.read()


def figure_to_png_bytes(fig: Figure, dpi: int = 150) -> bytes:
    """Converte una figura Matplotlib in bytes PNG."""

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    png_bytes = buffer.read()
    buffer.close()
    return png_bytes


def generate_pdf_report(
    title: str,
    table_sections: Optional[Sequence[PdfTableSection]] = None,
    image_sections: Optional[Sequence[PdfImageSection]] = None,
    compact_tables: bool = False,
    match_meta: Optional[PdfMatchMeta] = None,
    kpi_executive: Optional[dict] = None,
) -> bytes:
    """Genera un PDF con sezioni tabellari e immagini.

    Se passati match_meta / kpi_executive, antepone copertina + dashboard KPI.
    """

    buffer = BytesIO()
    
    # Verifica se ci sono solo sezioni Live per usare portrait
    table_sections_list_temp = list(table_sections or [])
    live_section_titles = (
        "Possesso - Attacco",
        "Non Possesso - Difesa",
        "Perse e Recuperate",
        "Falli",
    )
    has_cover = match_meta is not None or kpi_executive is not None
    has_only_live = (
        bool(table_sections_list_temp)
        and all(sec.title in live_section_titles or sec.title in ("Risultato", "Timeline Gol") for sec in table_sections_list_temp)
        and not image_sections
        and not has_cover
    )
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4 if has_only_live else landscape(A4),
        leftMargin=25,
        rightMargin=25,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    # Font del titolo principale del report (centrato e leggermente più grande).
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=1,
        fontSize=12,
        spaceAfter=8,
    )
    # Font dei titoli di sezione all'interno del PDF.
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading4"],
        fontSize=6,
        leading=7,
        spaceAfter=2,
    )

    # Stile delle tabelle: font ridimensionati e padding verticale contenuto.
    header_font_size = 5 if compact_tables else 6
    body_font_size = 5 if compact_tables else 6
    small_header_font_size = 3 if compact_tables else 4

    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            # Font dell'intestazione di tabella (riga 0).
            ("FONTSIZE", (0, 0), (-1, 0), header_font_size),
            # Font delle celle di dati (righe > 0).
            ("FONTSIZE", (0, 1), (-1, -1), body_font_size),
            ("TOPPADDING", (0, 0), (-1, 0), 0.8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 0.8),
            ("TOPPADDING", (0, 1), (-1, -1), 0.4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 0.4),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5f5")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]
    )
    
    # Stile delle tabelle per stats individuali e quartetti: font più piccolo per le intestazioni
    table_style_small_header = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            # Font dell'intestazione di tabella (riga 0) - ridotto per stats individuali e quartetti.
            ("FONTSIZE", (0, 0), (-1, 0), small_header_font_size),
            # Font delle celle di dati (righe > 0).
            ("FONTSIZE", (0, 1), (-1, -1), body_font_size),
            ("TOPPADDING", (0, 0), (-1, 0), 0.8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 0.8),
            ("TOPPADDING", (0, 1), (-1, -1), 0.4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 0.4),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5f5")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]
    )

    available_width = doc.width
    column_gap = 12
    column_width = (available_width - (column_gap * 2)) / 3.0

    elements: List = []

    table_sections_list: List[PdfTableSection] = list(table_sections or [])

    # Estrai timeline prima della copertina (se presente)
    timeline_for_cover = None
    for sec in table_sections_list:
        if sec.title == "Timeline Gol" and sec.dataframe is not None and not sec.dataframe.empty:
            timeline_for_cover = sec.dataframe.copy()
            break

    if match_meta is not None:
        elements.extend(
            _build_cover_elements(match_meta, timeline_for_cover, styles, available_width)
        )

    if kpi_executive is not None:
        home = match_meta.home_name if match_meta else "FMP"
        away = match_meta.away_name if match_meta else "Avversario"
        elements.extend(
            _build_kpi_dashboard_elements(kpi_executive, home, away, styles, available_width)
        )

    # Titolo sezioni dettagliate (dopo cover/KPI)
    elements.append(Paragraph(title, title_style))

    def pop_section_by_title(section_title: str) -> Optional[PdfTableSection]:
        for idx, sec in enumerate(table_sections_list):
            if sec.title == section_title:
                return table_sections_list.pop(idx)
        return None

    def build_table_flowable(section: PdfTableSection, width: float, index_column: Optional[str] = None, use_small_header: bool = False) -> Table:
        df = section.dataframe
        if df.empty:
            df = pd.DataFrame([[]])
        table_data = _dataframe_to_table_data(df, index_column=index_column)
        num_cols = len(table_data[0]) if table_data else 1
        
        # Per le stats quartetti e minutaggi quartetti, allarga la prima colonna (indice con nomi giocatori) e restringe le altre
        is_quartetti = section.title.startswith(("Stats Quartetti", "Quinto Uomo"))
        is_minutaggi_quartetti = "Minutaggi" in section.title and "Quartetti" in section.title
        if (is_quartetti or is_minutaggi_quartetti) and num_cols > 1:
            # Prima colonna (indice con nomi giocatori) prende il 50% della larghezza, le altre (numeri) si dividono il resto
            first_col_width = width * 0.14
            remaining_width = width - first_col_width
            other_cols_width = remaining_width / (num_cols - 1)
            col_widths = [first_col_width] + [other_cols_width] * (num_cols - 1)
        else:
            # Distribuzione equa per le altre tabelle
            col_widths = [width / num_cols] * num_cols
        
        data_table = Table(table_data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
        # Usa lo stile con header più piccolo se richiesto
        style_to_use = table_style_small_header if use_small_header else table_style
        data_table.setStyle(style_to_use)
        return data_table

    def build_section_table(section: PdfTableSection, width: float, index_column: Optional[str] = None, use_small_header: bool = False) -> Table:
        section_table = Table(
            [
                [Paragraph(section.title, section_title_style)],
                [build_table_flowable(section, width, index_column=index_column, use_small_header=use_small_header)],
            ],
            colWidths=[width],
            hAlign="LEFT",
        )
        section_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return section_table

    # Sezione centrale con Risultato, Timeline e Durata Partita, se disponibili
    result_section = pop_section_by_title("Risultato")
    timeline_section = pop_section_by_title("Timeline Gol")
    durata_section = pop_section_by_title("Minutaggi - Durata Partita")
    summary_rendered = False
    # Con la copertina attiva risultato e timeline sono gia' in prima pagina:
    # ripeterli qui creerebbe una pagina duplicata.
    if match_meta is not None:
        result_section = None
        timeline_section = None
    if result_section or timeline_section or durata_section:
        if result_section:
            result_table = build_section_table(result_section, column_width)
            result_table.hAlign = "CENTER"
            elements.append(result_table)
            elements.append(Spacer(1, 6))
        if timeline_section:
            timeline_table = build_section_table(timeline_section, column_width)
            timeline_table.hAlign = "CENTER"
            elements.append(timeline_table)
            elements.append(Spacer(1, 6))
        if durata_section:
            durata_table = build_section_table(durata_section, column_width)
            durata_table.hAlign = "CENTER"
            elements.append(durata_table)
            elements.append(Spacer(1, 12))
        summary_rendered = True

    def get_index_column_for_minutaggi(section: PdfTableSection) -> Optional[str]:
        """Determina quale colonna usare come indice per i minutaggi."""
        df = section.dataframe
        if df.empty:
            return None
        
        # Cerca le colonne possibili per l'indice
        # Nota: dopo format_column_names, "Giocatori_movimento" diventa "Giocatori Movimento"
        possible_index_cols = [
            "Giocatori Movimento",  # Formato dopo format_column_names
            "Giocatori_movimento",  # Formato originale
            "Giocatore",
            "Portiere"
        ]
        for col in possible_index_cols:
            if col in df.columns:
                return col
        return None

    def render_sections_columns(sections: List[PdfTableSection], use_index_column: bool = False) -> None:
        """Rende le sezioni su tre colonne con piccoli spazi tra le tabelle."""
        if not sections:
            return
        
        # Se sono minutaggi, ordina le sezioni in modo specifico
        if use_index_column:
            def sort_key_minutaggi(section: PdfTableSection) -> tuple:
                title = section.title
                # Ordina per tipo (Singoli prima, poi Quartetti)
                if "Singoli" in title:
                    tipo_order = 0
                elif "Quartetti" in title or "Quartetto" in title:
                    tipo_order = 1
                else:
                    tipo_order = 2
                
                # Ordina per periodo (Totale, Primo tempo, Secondo tempo)
                if "Totale" in title:
                    periodo_order = 0
                elif "Primo tempo" in title or "1T" in title:
                    periodo_order = 1
                elif "Secondo tempo" in title or "2T" in title:
                    periodo_order = 2
                else:
                    periodo_order = 3
                
                return (tipo_order, periodo_order)
            
            sections = sorted(sections, key=sort_key_minutaggi)
        
        row_cells: List = []
        column_sections: List[List] = []
        wide_sections: List[PdfTableSection] = []

        for section in sections:
            if section.dataframe.shape[0] > 18:
                wide_sections.append(section)
                continue
            
            # Determina la colonna indice se necessario
            index_col = None
            if use_index_column:
                index_col = get_index_column_for_minutaggi(section)
            
            row_cells.append(build_section_table(section, column_width, index_column=index_col))
            if len(row_cells) == 3:
                column_sections.append(row_cells)
                row_cells = []

        if row_cells:
            while len(row_cells) < 3:
                row_cells.append("")
            column_sections.append(row_cells)

        for row in column_sections:
            row_data = []
            col_widths = []
            for idx, cell in enumerate(row):
                row_data.append(cell)
                col_widths.append(column_width)
                if idx < len(row) - 1:
                    row_data.append("")
                    col_widths.append(column_gap)
            grid = Table(
                [row_data],
                colWidths=col_widths,
                hAlign="CENTER",
            )
            grid.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(grid)
            elements.append(Spacer(1, 6))

        for section in wide_sections:
            # Determina la colonna indice se necessario
            index_col = None
            if use_index_column:
                index_col = get_index_column_for_minutaggi(section)
            table_full = build_section_table(section, available_width, index_column=index_col)
            table_full.hAlign = "CENTER"
            elements.append(table_full)
            elements.append(Spacer(1, 8))

    def render_sections_columns_2(sections: List[PdfTableSection]) -> None:
        """Rende le sezioni su due colonne con piccoli spazi tra le tabelle."""
        if not sections:
            return
        # Calcola larghezza colonna per 2 colonne
        column_width_2 = (available_width - column_gap) / 2.0
        row_cells: List = []
        column_sections: List[List] = []
        wide_sections: List[PdfTableSection] = []

        for section in sections:
            if section.dataframe.shape[0] > 18:
                wide_sections.append(section)
                continue
            row_cells.append(build_section_table(section, column_width_2))
            if len(row_cells) == 2:
                column_sections.append(row_cells)
                row_cells = []

        if row_cells:
            while len(row_cells) < 2:
                row_cells.append("")
            column_sections.append(row_cells)

        for row in column_sections:
            row_data = []
            col_widths = []
            for idx, cell in enumerate(row):
                row_data.append(cell)
                col_widths.append(column_width_2)
                if idx < len(row) - 1:
                    row_data.append("")
                    col_widths.append(column_gap)
            grid = Table(
                [row_data],
                colWidths=col_widths,
                hAlign="CENTER",
            )
            grid.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(grid)
            elements.append(Spacer(1, 6))

        for section in wide_sections:
            table_full = build_section_table(section, available_width)
            table_full.hAlign = "CENTER"
            elements.append(table_full)
            elements.append(Spacer(1, 8))

    def render_sections_columns_4(sections: List[PdfTableSection]) -> None:
        """Rende le sezioni su quattro colonne con piccoli spazi tra le tabelle."""
        if not sections:
            return
        # Calcola larghezza colonna per 4 colonne
        column_width_4 = (available_width - (column_gap * 3)) / 4.0
        row_cells: List = []
        column_sections: List[List] = []
        wide_sections: List[PdfTableSection] = []

        for section in sections:
            if section.dataframe.shape[0] > 18:
                wide_sections.append(section)
                continue
            row_cells.append(build_section_table(section, column_width_4))
            if len(row_cells) == 4:
                column_sections.append(row_cells)
                row_cells = []

        if row_cells:
            while len(row_cells) < 4:
                row_cells.append("")
            column_sections.append(row_cells)

        for row in column_sections:
            row_data = []
            col_widths = []
            for idx, cell in enumerate(row):
                row_data.append(cell)
                col_widths.append(column_width_4)
                if idx < len(row) - 1:
                    row_data.append("")
                    col_widths.append(column_gap)
            grid = Table(
                [row_data],
                colWidths=col_widths,
                hAlign="CENTER",
            )
            grid.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(grid)
            elements.append(Spacer(1, 6))

        for section in wide_sections:
            table_full = build_section_table(section, available_width)
            table_full.hAlign = "CENTER"
            elements.append(table_full)
            elements.append(Spacer(1, 8))

    def render_sections_single(sections: List[PdfTableSection], use_small_header: bool = False) -> None:
        """Rende ogni sezione a tutta larghezza (una colonna)."""
        for section in sections:
            table_full = build_section_table(section, available_width, use_small_header=use_small_header)
            table_full.hAlign = "CENTER"
            elements.append(table_full)
            elements.append(Spacer(1, 6))

    # Suddivide le restanti sezioni per gruppo logico.
    team_sections: List[PdfTableSection] = []
    individual_sections: List[PdfTableSection] = []
    quartetti_sections: List[PdfTableSection] = []
    minutaggi_sections: List[PdfTableSection] = []
    live_sections: List[PdfTableSection] = []
    top5_sections: List[PdfTableSection] = []
    other_sections: List[PdfTableSection] = []

    # Titoli delle sezioni Live (da formattare in tre colonne)
    live_section_titles = (
        "Possesso - Attacco",
        "Non Possesso - Difesa",
        "Perse e Recuperate",
        "Falli",
    )

    for section in table_sections_list:
        title = section.title
        if title.startswith("Stats Squadra"):
            team_sections.append(section)
        elif title.startswith(("Stats Individuali", "Stats Portieri Individuali")):
            individual_sections.append(section)
        elif title.startswith(("Stats Quartetti", "Quinto Uomo")):
            quartetti_sections.append(section)
        elif title.startswith("Minutaggi") and title != "Minutaggi - Durata Partita":
            minutaggi_sections.append(section)
        elif title in live_section_titles:
            live_sections.append(section)
        elif title.startswith("Top 5"):
            top5_sections.append(section)
        else:
            other_sections.append(section)

    groups: List[Tuple[str, List[PdfTableSection], Callable]] = [
        ("Stats Squadra", team_sections, lambda s: render_sections_columns(s, use_index_column=False)),
        ("Top 5", top5_sections, render_sections_columns_4),
        ("Stats Individuali", individual_sections, lambda s: render_sections_single(s, use_small_header=True)),
        ("Stats Quartetti", quartetti_sections, lambda s: render_sections_single(s, use_small_header=True)),
        ("Minutaggi", minutaggi_sections, lambda s: render_sections_columns(s, use_index_column=True)),
        ("Live", live_sections, render_sections_columns_2),
        ("Altro", other_sections, render_sections_single),
    ]

    content_started = summary_rendered

    for _, sections, renderer in groups:
        if not sections:
            continue
        if content_started:
            elements.append(PageBreak())
        renderer(sections)
        content_started = True

    if image_sections:
        # Filtra le sezioni valide
        valid_sections = [s for s in image_sections if s.image_bytes]
        
        # Raggruppa le immagini per giocatore (per le zone individuali)
        def extract_player_name(title: str) -> Optional[str]:
            """Estrae il nome del giocatore dal titolo se è una zona individuale."""
            if title.startswith("Zone ") and (" Attacco - " in title or " Difesa - " in title):
                # Formato: "Zone {giocatore} Attacco - ..." o "Zone {giocatore} Difesa - ..."
                parts = title.split(" ")
                if len(parts) >= 2:
                    # Trova la parte dopo "Zone" e prima di "Attacco" o "Difesa"
                    player_parts = []
                    for i, part in enumerate(parts[1:], 1):
                        if part in ("Attacco", "Difesa"):
                            break
                        player_parts.append(part)
                    if player_parts:
                        return " ".join(player_parts)
            return None
        
        # Raggruppa per giocatore
        player_groups: List[List[PdfImageSection]] = []
        current_player: Optional[str] = None
        current_group: List[PdfImageSection] = []
        
        for section in valid_sections:
            player = extract_player_name(section.title)
            if player:
                # È una zona individuale
                if current_player is None:
                    # Primo giocatore
                    current_player = player
                    current_group = [section]
                elif player == current_player:
                    # Stesso giocatore, aggiungi al gruppo
                    current_group.append(section)
                else:
                    # Nuovo giocatore, salva il gruppo precedente e inizia uno nuovo
                    if current_group:
                        player_groups.append(current_group)
                    current_player = player
                    current_group = [section]
            else:
                # Non è una zona individuale (es. zone squadra), aggiungi come gruppo separato
                if current_group:
                    player_groups.append(current_group)
                    current_group = []
                player_groups.append([section])
        
        # Aggiungi l'ultimo gruppo
        if current_group:
            player_groups.append(current_group)
        
        # Organizza i gruppi in righe di 3, assicurandosi che ogni giocatore inizi su una nuova riga
        image_rows: List[List[PdfImageSection]] = []
        current_row: List[PdfImageSection] = []
        
        for group in player_groups:
            # Se aggiungere questo gruppo alla riga corrente la farebbe superare 3, inizia una nuova riga
            if len(current_row) + len(group) > 3:
                if current_row:
                    image_rows.append(current_row)
                current_row = []
            
            # Aggiungi le immagini del gruppo alla riga corrente
            for section in group:
                current_row.append(section)
                if len(current_row) == 3:
                    image_rows.append(current_row)
                    current_row = []
        
        # Aggiungi l'ultima riga se non è vuota
        if current_row:
            image_rows.append(current_row)
        
        # Organizza le righe in pagine di 2 righe (6 immagini)
        images_per_page = 6
        image_pages: List[List[List[PdfImageSection]]] = []
        
        for i in range(0, len(image_rows), 2):
            page_rows = image_rows[i:i + 2]
            # Appiattisci le righe in una lista di immagini per la pagina
            page_images = []
            for row in page_rows:
                page_images.extend(row)
            image_pages.append(page_images)
        
        def build_image_cell(section: PdfImageSection) -> Table:
            """Crea una cella con l'immagine."""
            img_buffer_reader = BytesIO(section.image_bytes)
            img_reader = ImageReader(img_buffer_reader)
            img_width, img_height = img_reader.getSize()
            # Usa la larghezza della colonna come max_width per sfruttare meglio lo spazio
            max_width = column_width - 10  # Lascia un piccolo margine
            
            if img_width > max_width:
                ratio = max_width / float(img_width)
                img_width = max_width
                img_height = img_height * ratio
            
            # Crea un nuovo buffer per l'immagine finale
            img_buffer = BytesIO(section.image_bytes)
            
            # Crea una tabella per ogni sezione (solo immagine, senza titolo)
            section_cell = Table(
                [
                    [Image(img_buffer, width=img_width, height=img_height, hAlign="CENTER")],
                ],
                colWidths=[column_width],
                hAlign="CENTER",
            )
            section_cell.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            return section_cell
        
        def build_image_row(images: List[PdfImageSection]) -> Table:
            """Crea una riga con fino a 3 immagini."""
            row_data = []
            col_widths = []
            
            for idx, section in enumerate(images):
                section_cell = build_image_cell(section)
                row_data.append(section_cell)
                col_widths.append(column_width)
                
                # Aggiungi gap tra le colonne (tranne l'ultima)
                if idx < len(images) - 1:
                    row_data.append("")
                    col_widths.append(column_gap)
            
            # Riempi le colonne mancanti se la riga non è completa
            while len(row_data) < 5:  # 3 colonne + 2 gap = 5 elementi
                if len(row_data) % 2 == 0:  # Posizione pari = colonna
                    row_data.append("")
                    col_widths.append(column_width)
                else:  # Posizione dispari = gap
                    row_data.append("")
                    col_widths.append(column_gap)
            
            # Crea la tabella della riga
            row_table = Table(
                [row_data],
                colWidths=col_widths,
                hAlign="CENTER",
            )
            row_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            return row_table
        
        # Renderizza le righe di immagini
        for row_idx, row_images in enumerate(image_rows):
            # Se è la prima riga e c'è già contenuto, o se è una nuova pagina (ogni 2 righe)
            if (content_started and row_idx == 0) or (row_idx > 0 and row_idx % 2 == 0):
                elements.append(PageBreak())
            
            if row_images:
                row_table = build_image_row(row_images)
                elements.append(row_table)
                elements.append(Spacer(1, 6))
            
            content_started = True

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

