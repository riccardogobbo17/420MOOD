"""Genera il PDF partita da un CSV, senza passare da Streamlit ne' dal database.

Uso:
    .venv/bin/python app/scripts/genera_pdf_test.py <percorso_csv> [avversario] [output.pdf]

Utile per iterare sul layout del report: ricostruisce le stesse sezioni che la
pagina 1_partite passa a generate_pdf_report.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futsal_analysis.utils_eventi import (  # noqa: E402
    calcola_kpi_executive,
    calcola_report_completo,
    mask_gol,
)
from futsal_analysis.utils_pdf import (  # noqa: E402
    PdfMatchMeta,
    PdfTableSection,
    generate_pdf_report,
)
from verifica_csv import carica  # noqa: E402


def formatta(df: pd.DataFrame) -> pd.DataFrame:
    def etichetta(v):
        return str(v).replace('_', ' ').title() if isinstance(v, str) else v

    return df.rename(columns=etichetta, index=etichetta)


def main() -> None:
    path = Path(sys.argv[1])
    avversario = sys.argv[2] if len(sys.argv) > 2 else path.stem.title()
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("report_test.pdf")

    df = carica(path)
    report = calcola_report_completo(df)
    gol_fatti = int(mask_gol(df, 'Noi').sum())
    gol_subiti = int(mask_gol(df, 'Loro').sum())

    sezioni = [
        PdfTableSection("Risultato", pd.DataFrame(
            {"FMP": [gol_fatti], avversario: [gol_subiti]}, index=["Gol"]
        )),
    ]

    gol_df = df[df['evento'] == 'Gol'].copy()
    if not gol_df.empty:
        timeline = pd.DataFrame({
            "Minuto": gol_df['tempoEffettivo'],
            "Squadra": gol_df['squadra'],
            "Marcatore": gol_df['chi'].str.title(),
            "Tipo Azione": gol_df['esito'].replace('', '—'),
        }).reset_index(drop=True)
        sezioni.append(PdfTableSection("Timeline Gol", timeline))

    for titolo, dati in [
        ("Stats Squadra - Possesso Attacco", report['squadra']['attacco']),
        ("Stats Squadra - Non Possesso Difesa", report['squadra']['difesa']),
        ("Stats Squadra - Falli", report['squadra']['falli']),
        ("Stats Squadra - Portieri Noi", report['squadra']['portieri_noi']),
        ("Stats Squadra - Portieri Loro", report['squadra']['portieri_loro']),
    ]:
        sezioni.append(PdfTableSection(titolo, formatta(pd.DataFrame(dati).fillna(0))))

    sezioni.append(PdfTableSection(
        "Stats Individuali - Totale",
        formatta(pd.DataFrame(report['individuali']).T.fillna(0).astype(int)),
    ))

    pdf = generate_pdf_report(
        f"Report Partita - FMP vs {avversario}",
        table_sections=sezioni,
        match_meta=PdfMatchMeta(
            home_name="FMP",
            away_name=avversario,
            home_goals=gol_fatti,
            away_goals=gol_subiti,
            competition="Campionato",
            match_date=str(df['data'].iloc[0]) if 'data' in df.columns else "",
            category="Prima Squadra",
        ),
        kpi_executive=calcola_kpi_executive(df),
    )
    output.write_bytes(pdf)
    print(f"PDF scritto: {output} ({len(pdf) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
