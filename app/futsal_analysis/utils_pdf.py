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


def _dataframe_to_table_data(df: pd.DataFrame) -> list[list[str]]:
    """Converte un DataFrame in una lista di liste per l'uso con ReportLab."""

    df_reset = df.copy()
    df_reset = df_reset.reset_index()

    # Rinomina la colonna dell'indice per renderla più leggibile
    first_col = df_reset.columns[0]
    if first_col == "index":
        df_reset = df_reset.rename(columns={first_col: ""})

    df_reset = df_reset.fillna("")

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
            ("FONTSIZE", (0, 0), (-1, 0), 10),
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
) -> bytes:
    """Genera un PDF con sezioni tabellari e immagini."""

    buffer = BytesIO()
    
    # Verifica se ci sono solo sezioni Live per usare portrait
    table_sections_list_temp = list(table_sections or [])
    live_section_titles = (
        "Possesso - Attacco",
        "Non Possesso - Difesa",
        "Perse e Recuperate",
        "Falli",
    )
    has_only_live = (
        bool(table_sections_list_temp)
        and all(sec.title in live_section_titles or sec.title in ("Risultato", "Timeline Gol") for sec in table_sections_list_temp)
        and not image_sections
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
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            # Font dell'intestazione di tabella (riga 0).
            ("FONTSIZE", (0, 0), (-1, 0), 5.5),
            # Font delle celle di dati (righe > 0).
            ("FONTSIZE", (0, 1), (-1, -1), 4.5),
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

    elements: List = [Paragraph(title, title_style)]

    table_sections_list: List[PdfTableSection] = list(table_sections or [])

    def pop_section_by_title(section_title: str) -> Optional[PdfTableSection]:
        for idx, sec in enumerate(table_sections_list):
            if sec.title == section_title:
                return table_sections_list.pop(idx)
        return None

    def build_table_flowable(section: PdfTableSection, width: float) -> Table:
        df = section.dataframe
        if df.empty:
            df = pd.DataFrame([[]])
        table_data = _dataframe_to_table_data(df)
        num_cols = len(table_data[0]) if table_data else 1
        col_widths = [width / num_cols] * num_cols
        data_table = Table(table_data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
        data_table.setStyle(table_style)
        return data_table

    def build_section_table(section: PdfTableSection, width: float) -> Table:
        section_table = Table(
            [
                [Paragraph(section.title, section_title_style)],
                [build_table_flowable(section, width)],
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

    # Sezione centrale con Risultato e Timeline, se disponibili
    result_section = pop_section_by_title("Risultato")
    timeline_section = pop_section_by_title("Timeline Gol")
    summary_rendered = False
    if result_section or timeline_section:
        if result_section:
            result_table = build_section_table(result_section, column_width)
            result_table.hAlign = "CENTER"
            elements.append(result_table)
            elements.append(Spacer(1, 6))
        if timeline_section:
            timeline_table = build_section_table(timeline_section, column_width)
            timeline_table.hAlign = "CENTER"
            elements.append(timeline_table)
            elements.append(Spacer(1, 12))
        summary_rendered = True

    def render_sections_columns(sections: List[PdfTableSection]) -> None:
        """Rende le sezioni su tre colonne con piccoli spazi tra le tabelle."""
        if not sections:
            return
        row_cells: List = []
        column_sections: List[List] = []
        wide_sections: List[PdfTableSection] = []

        for section in sections:
            if section.dataframe.shape[0] > 18:
                wide_sections.append(section)
                continue
            row_cells.append(build_section_table(section, column_width))
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
            table_full = build_section_table(section, available_width)
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

    def render_sections_single(sections: List[PdfTableSection]) -> None:
        """Rende ogni sezione a tutta larghezza (una colonna)."""
        for section in sections:
            table_full = build_section_table(section, available_width)
            table_full.hAlign = "CENTER"
            elements.append(table_full)
            elements.append(Spacer(1, 6))

    # Suddivide le restanti sezioni per gruppo logico.
    team_sections: List[PdfTableSection] = []
    individual_sections: List[PdfTableSection] = []
    quartetti_sections: List[PdfTableSection] = []
    minutaggi_sections: List[PdfTableSection] = []
    live_sections: List[PdfTableSection] = []
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
        elif title.startswith("Minutaggi"):
            minutaggi_sections.append(section)
        elif title in live_section_titles:
            live_sections.append(section)
        else:
            other_sections.append(section)

    groups: List[Tuple[str, List[PdfTableSection], Callable[[List[PdfTableSection]], None]]] = [
        ("Stats Squadra", team_sections, render_sections_columns),
        ("Stats Individuali", individual_sections, render_sections_single),
        ("Stats Quartetti", quartetti_sections, render_sections_single),
        ("Minutaggi", minutaggi_sections, render_sections_columns),
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
        for idx, section in enumerate(image_sections):
            if not section.image_bytes:
                continue

            elements.append(Paragraph(section.title, section_title_style))

            img_buffer = BytesIO(section.image_bytes)
            img_reader = ImageReader(img_buffer)
            width, height = img_reader.getSize()
            max_width = section.max_width

            if width > max_width:
                ratio = max_width / float(width)
                width = max_width
                height = height * ratio

            img_flow = Image(img_buffer, width=width, height=height, hAlign="LEFT")
            elements.append(img_flow)
            if idx != len(image_sections) - 1:
                elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

