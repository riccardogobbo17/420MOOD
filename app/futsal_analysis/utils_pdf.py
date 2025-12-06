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
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            # Font delle celle di dati (righe > 0).
            ("FONTSIZE", (0, 1), (-1, -1), 6),
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
            ("FONTSIZE", (0, 0), (-1, 0), 5),
            # Font delle celle di dati (righe > 0).
            ("FONTSIZE", (0, 1), (-1, -1), 6),
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
        else:
            other_sections.append(section)

    groups: List[Tuple[str, List[PdfTableSection], Callable]] = [
        ("Stats Squadra", team_sections, lambda s: render_sections_columns(s, use_index_column=False)),
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

