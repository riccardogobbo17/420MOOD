"""Controllo rapido del motore statistiche su un CSV esportato, senza Streamlit.

Uso:
    .venv/bin/python app/scripts/verifica_csv.py <percorso_csv>

Replica il preprocessing della pagina Admin e stampa il report che finirebbe
nel PDF, cosi' da verificare i numeri prima di caricare la partita a DB.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futsal_analysis.utils_eventi import (  # noqa: E402
    calcola_kpi_executive,
    calcola_report_completo,
    calcola_tipologia_gol,
)
from futsal_analysis.utils_time import (  # noqa: E402
    calcola_tempo_effettivo,
    calcola_tempo_reale,
    tag_primo_secondo_tempo,
)


def carica(path: Path) -> pd.DataFrame:
    header = path.read_text(encoding="utf-8-sig").splitlines()[0]
    sep = ";" if header.count(";") > header.count(",") else ","
    df = pd.read_csv(path, sep=sep, dtype=str, encoding="utf-8-sig").fillna("")
    df = df.rename(columns={
        "Position": "posizione",
        "Posizione": "posizione",
        "Data": "data",
        "Evento": "evento",
        "Portiere": "portiere",
        "Squadra": "squadra",
        "Chi": "chi",
        "Dove": "dove",
        "Lato": "lato",
        "Esito": "esito",
    })
    df = df.sort_values("posizione").reset_index(drop=True)
    df["Periodo"] = tag_primo_secondo_tempo(df)
    df["tempoEffettivo"] = calcola_tempo_effettivo(df)
    df["tempoReale"] = calcola_tempo_reale(df)
    return df


def main() -> None:
    path = Path(sys.argv[1])
    df = carica(path)
    report = calcola_report_completo(df)
    kpi = calcola_kpi_executive(df)

    print(f"Eventi letti: {len(df)}")
    print(f"Risultato: FMP {kpi['Noi']['gol']} - {kpi['Loro']['gol']}\n")

    print("--- KPI Noi vs Loro ---")
    print(pd.DataFrame({"Noi": kpi["Noi"], "Loro": kpi["Loro"]}).drop(index="tipologia_gol", errors="ignore"))

    print("\n--- Come nascono i gol ---")
    print(pd.DataFrame(calcola_tipologia_gol(df)))

    print("\n--- Squadra: attacco ---")
    print(pd.DataFrame(report["squadra"]["attacco"]))

    print("\n--- Squadra: difesa ---")
    print(pd.DataFrame(report["squadra"]["difesa"]))

    print("\n--- Portieri ---")
    print(pd.DataFrame(report["portieri_individuali"]).T)

    print("\n--- Individuali ---")
    print(pd.DataFrame(report["individuali"]).T.fillna(0).astype(int))


if __name__ == "__main__":
    main()
