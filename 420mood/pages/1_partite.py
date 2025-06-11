import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client

# === CONFIGURAZIONE SUPABASE ===
SUPABASE_URL = "https://jinmmonxjovoccejgwhk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppbm1tb254am92b2NjZWpnd2hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTk3NzksImV4cCI6MjA2NTEzNTc3OX0.kapMvgvW-6fng-RhxZV_YFcLnxcXo9Bg2wpDWu_H-5g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FUNZIONI SUPPORTO ===

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
    df['posizione_sec'] = df['posizione'].apply(to_seconds)

    idx_start = 0
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]

    t_start = df.loc[idx_start, 'posizione_sec']
    t_fine_primo = df.loc[idx_fine_primo, 'posizione_sec']
    t_start_secondo = df.loc[idx_start_secondo, 'posizione_sec']
    t_fine_partita = df.loc[idx_fine_partita, 'posizione_sec']

    tempo_effettivo_sec = []

    for i, row in df.iterrows():
        t = row['posizione_sec']
        if i <= idx_fine_primo:
            perc = (t - t_start) / (t_fine_primo - t_start) if (t_fine_primo - t_start) else 0
            eff = perc * 20 * 60
        elif i >= idx_start_secondo:
            perc = (t - t_start_secondo) / (t_fine_partita - t_start_secondo) if (t_fine_partita - t_start_secondo) else 0
            eff = 20 * 60 + perc * 20 * 60
        else:
            eff = np.nan
        tempo_effettivo_sec.append(eff)

    df['tempo_effettivo_sec'] = tempo_effettivo_sec
    df['tempo_effettivo'] = df['tempo_effettivo_sec'].apply(format_mmss)

    return df

def filtra_per_tempo(df, tempo='primo'):
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]
    if tempo == 'primo':
        return df.loc[:idx_fine_primo]
    elif tempo == 'secondo':
        return df.loc[idx_fine_primo+1:idx_fine_partita]
    return df

def analizza_tiri_gol(df):
    return {
        'Gol fatti': len(df[(df['evento'] == 'Gol') & (df['squadra'] != 'Loro')]),
        'Gol subiti': len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Loro')]),
        'Tiri fatti': len(df[(df['evento'] == 'Tiro') & (df['squadra'] != 'Loro')]),
        'Tiri subiti': len(df[(df['evento'] == 'Tiro') & (df['squadra'] == 'Loro')]),
    }

def conta_eventi(df, evento):
    fatti = len(df[(df['evento'] == evento) & (df['squadra'] != 'Loro')])
    subiti = len(df[(df['evento'] == evento) & (df['squadra'] == 'Loro')])
    return fatti, subiti

# === INTERFACCIA ===

st.title("Tutte le partite disponibili")

# Carichiamo la lista delle partite da Supabase
res = supabase.table("partite").select("*").order("data", desc=True).execute()
partite = res.data

if not partite:
    st.warning("Nessuna partita trovata.")
else:
    n_cols = 4
    for i in range(0, len(partite), n_cols):
        cols = st.columns(n_cols)
        for j, partita in enumerate(partite[i:i+n_cols]):
            with cols[j]:
                st.markdown(f"### {partita['avversario'].title()}")
                st.write(f"{partita['competizione'].capitalize()} — {partita['data']}")
                if st.button("Analizza", key=f"btn_{i}_{j}"):
                    st.session_state["partita_scelta"] = partita["id"]

if "partita_scelta" in st.session_state:
    partita_id = st.session_state["partita_scelta"]
    partita_info = next((p for p in partite if p["id"] == partita_id), None)

    st.markdown("---")
    st.subheader(f"Analisi di {partita_info['competizione'].capitalize()} vs {partita_info['avversario'].title()} — {partita_info['data']}")

    eventi = supabase.table("eventi").select("*").eq("partita_id", partita_id).execute().data
    df = pd.DataFrame(eventi)

    if df.empty:
        st.warning("Nessun evento trovato per questa partita.")
    else:
        df = calcola_tempo_effettivo(df)
        df["tempo_reale_sec"] = df["posizione"].apply(to_seconds)

        gol_fatti_tot = len(df[(df['evento'] == 'Gol') & (df['squadra'] != 'Loro')])
        gol_subiti_tot = len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Loro')])

        st.markdown(f"## Risultato: **FMP {gol_fatti_tot} – {gol_subiti_tot} {partita_info['avversario'].title()}**")

        idx_inizio = 0
        idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
        idx_inizio_secondo = idx_fine_primo + 1
        idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]

        durata_primo = df.loc[idx_fine_primo, 'tempo_reale_sec'] - df.loc[idx_inizio, 'tempo_reale_sec']
        durata_secondo = df.loc[idx_fine_partita, 'tempo_reale_sec'] - df.loc[idx_inizio_secondo, 'tempo_reale_sec']
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

        st.subheader("Altri Eventi")
        st.dataframe(df_eventi)
