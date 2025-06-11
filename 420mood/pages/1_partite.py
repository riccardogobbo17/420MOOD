import streamlit as st
import pandas as pd
import numpy as np
import os

DATA_DIR = "FMP"

# === FUNZIONI ===

def lista_partite(data_dir=DATA_DIR):
    partite = []
    for subdir, dirs, files in os.walk(data_dir):
        for file in files:
            if file == "events.csv":
                rel_path = os.path.relpath(os.path.join(subdir, file), data_dir)
                path_parts = rel_path.split(os.sep)
                if len(path_parts) >= 2:
                    tipo = path_parts[0]
                    avversario = path_parts[1]
                    try:
                        df = pd.read_csv(os.path.join(subdir, file))
                        data = df["Data"].iloc[0] if "Data" in df.columns else ""
                    except:
                        data = ""
                    partite.append({
                        "tipo": tipo,
                        "avversario": avversario,
                        "data": data,
                        "file_path": os.path.join(subdir, file)
                    })
    return sorted(partite, key=lambda x: x['data'], reverse=True)

def to_seconds(time_str):
    if pd.isna(time_str):
        return np.nan
    t = time_str.split(':')
    if len(t) == 3:
        h, m, s = t
        return int(h)*3600 + int(m)*60 + float(s)
    return np.nan

def format_mmss(s):
    if pd.isna(s):
        return ''
    m = int(s // 60)
    s2 = int(round(s % 60))
    return f"{m:02}:{s2:02}"

def calcola_tempo_effettivo(df):
    df = df.copy()
    df['Posizione_sec'] = df['Posizione'].apply(to_seconds)

    idx_start = 0
    idx_fine_primo = df[df['Evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df[df['Evento'] == 'Fine partita'].index[0]

    t_start = df.loc[idx_start, 'Posizione_sec']
    t_fine_primo = df.loc[idx_fine_primo, 'Posizione_sec']
    t_start_secondo = df.loc[idx_start_secondo, 'Posizione_sec']
    t_fine_partita = df.loc[idx_fine_partita, 'Posizione_sec']

    tempo_effettivo_sec = []

    for i, row in df.iterrows():
        t = row['Posizione_sec']
        if i <= idx_fine_primo:
            perc = (t - t_start) / (t_fine_primo - t_start) if (t_fine_primo - t_start) else 0
            eff = perc * 20 * 60
        elif i >= idx_start_secondo:
            perc = (t - t_start_secondo) / (t_fine_partita - t_start_secondo) if (t_fine_partita - t_start_secondo) else 0
            eff = 20 * 60 + perc * 20 * 60
        else:
            eff = np.nan
        tempo_effettivo_sec.append(eff)

    df['tempoEffettivo_sec'] = tempo_effettivo_sec
    df['tempoEffettivo'] = df['tempoEffettivo_sec'].apply(format_mmss)

    return df

def filtra_per_tempo(df, tempo='primo'):
    idx_fine_primo = df[df['Evento'] == 'Fine primo tempo'].index[0]
    idx_fine_partita = df[df['Evento'] == 'Fine partita'].index[0]
    if tempo == 'primo':
        return df.loc[:idx_fine_primo]
    elif tempo == 'secondo':
        return df.loc[idx_fine_primo+1:idx_fine_partita]
    return df

def analizza_tiri_gol(df):
    return {
        'Gol fatti': len(df[(df['Evento'] == 'Gol') & (df['Squadra'] != 'Loro')]),
        'Gol subiti': len(df[(df['Evento'] == 'Gol') & (df['Squadra'] == 'Loro')]),
        'Tiri fatti': len(df[(df['Evento'] == 'Tiro') & (df['Squadra'] != 'Loro')]),
        'Tiri subiti': len(df[(df['Evento'] == 'Tiro') & (df['Squadra'] == 'Loro')]),
    }

def conta_eventi(df, evento):
    fatti = len(df[(df['Evento'] == evento) & (df['Squadra'] != 'Loro')])
    subiti = len(df[(df['Evento'] == evento) & (df['Squadra'] == 'Loro')])
    return fatti, subiti

# === INTERFACCIA STREAMLIT ===

st.title("Tutte le partite disponibili")

partite = lista_partite()
if not partite:
    st.warning("Nessuna partita trovata.")
else:
    n_cols = 4
    for i in range(0, len(partite), n_cols):
        cols = st.columns(n_cols)
        for j, partita in enumerate(partite[i:i+n_cols]):
            with cols[j]:
                st.markdown(f"### {partita['avversario'].title()}")
                st.write(f"{partita['tipo'].capitalize()} — {partita['data']}")
                if st.button("Analizza", key=f"btn_{i}_{j}"):
                    st.session_state["partita_scelta"] = partita

    partita_scelta = st.session_state.get("partita_scelta", None)
    if "partita_scelta" in st.session_state:
        partita_scelta = st.session_state["partita_scelta"]
        st.markdown("---")
        st.subheader(f"Analisi di {partita_scelta['tipo'].capitalize()} vs {partita_scelta['avversario'].title()} — {partita_scelta['data']}")

        df = pd.read_csv(partita_scelta["file_path"])
        df = calcola_tempo_effettivo(df)
        df['tempoReale_sec'] = df['Posizione'].apply(to_seconds)

        # -> Qui aggiungi il blocco per il risultato
        gol_fatti_tot = len(df[(df['Evento'] == 'Gol') & (df['Squadra'] != 'Loro')])
        gol_subiti_tot = len(df[(df['Evento'] == 'Gol') & (df['Squadra'] == 'Loro')])
        nome_nostra = partita_scelta["tipo"]   # se hai un altro campo per la tua squadra, usalo
        nome_avv = partita_scelta["avversario"]
        st.markdown(f"## Risultato: **FMP {gol_fatti_tot} – {gol_subiti_tot} {nome_avv.title()}**")

        idx_inizio = 0
        idx_fine_primo = df[df['Evento'] == 'Fine primo tempo'].index[0]
        idx_inizio_secondo = idx_fine_primo + 1
        idx_fine_partita = df[df['Evento'] == 'Fine partita'].index[0]

        durata_primo = df.loc[idx_fine_primo, 'tempoReale_sec'] - df.loc[idx_inizio, 'tempoReale_sec']
        durata_secondo = df.loc[idx_fine_partita, 'tempoReale_sec'] - df.loc[idx_inizio_secondo, 'tempoReale_sec']
        durata_totale = durata_primo + durata_secondo

        df_primo = filtra_per_tempo(df, 'primo')
        df_secondo = filtra_per_tempo(df, 'secondo')

        df_stats_tempi = pd.DataFrame([analizza_tiri_gol(df_primo), analizza_tiri_gol(df_secondo)],
                                    index=['Primo tempo', 'Secondo tempo'])

        eventi_da_contare = ['Gol', 'Tiri', 'Parate', 'Angolo', 'Laterale', 'Fallo', 'Ammonizione', 'Espulsione', 'Timeout', '3v2', '2v1']

        dati_eventi = {
            "Evento": [],
            "Fatti primo tempo": [],
            "Subiti primo tempo": [],
            "Fatti secondo tempo": [],
            "Subiti secondo tempo": [],
            "Fatti totali": [],
            "Subiti totali": []
        }

        for evento in eventi_da_contare:
            fatti_primo, subiti_primo = conta_eventi(df_primo, evento)
            fatti_secondo, subiti_secondo = conta_eventi(df_secondo, evento)
            dati_eventi["Evento"].append(evento)
            dati_eventi["Fatti primo tempo"].append(fatti_primo)
            dati_eventi["Subiti primo tempo"].append(subiti_primo)
            dati_eventi["Fatti secondo tempo"].append(fatti_secondo)
            dati_eventi["Subiti secondo tempo"].append(subiti_secondo)
            dati_eventi["Fatti totali"].append(fatti_primo + fatti_secondo)
            dati_eventi["Subiti totali"].append(subiti_primo + subiti_secondo)

        df_eventi = pd.DataFrame(dati_eventi)

        st.subheader("Durata dei tempi")
        st.dataframe(pd.DataFrame({
            "Periodo": ["Primo tempo", "Secondo tempo", "Totale partita"],
            "Durata_minuti": [round(durata_primo/60), round(durata_secondo/60), round(durata_totale/60)]
        }))

        st.subheader("Gol e Tiri per Tempo")
        st.dataframe(df_stats_tempi)

        st.subheader("Altri Eventi (Angoli, Laterali, Palle perse/recuperate)")
        st.dataframe(df_eventi)

