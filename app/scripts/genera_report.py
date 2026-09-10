"""Genera il report PDF della partita da un CSV, senza Streamlit ne' database.

Uso:
    .venv/bin/python app/scripts/genera_report.py <csv> [avversario] [output.pdf]

Esempio:
    .venv/bin/python app/scripts/genera_report.py ~/Downloads/montegrappa-fmp.csv Montegrappa report.pdf

E' il modo piu' rapido per iterare sul layout: modifichi
futsal_analysis/report_partita.py, rilanci, apri il PDF.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futsal_analysis.report_partita import MetaPartita, genera_report_partita  # noqa: E402
from verifica_csv import carica  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)

    percorso = Path(sys.argv[1])
    avversario = sys.argv[2] if len(sys.argv) > 2 else percorso.stem.replace("-", " ").title()
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("report_partita.pdf")

    df = carica(percorso)
    data = str(df["data"].iloc[0]) if "data" in df.columns and len(df) else ""

    pdf = genera_report_partita(df, MetaPartita(
        avversario=avversario,
        competizione="Campionato",
        data=data,
    ))
    output.write_bytes(pdf)
    print(f"PDF scritto: {output} ({len(pdf) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
