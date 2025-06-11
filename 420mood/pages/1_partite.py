import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client

# === CONFIGURAZIONE SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FUNZIONI BASE ===
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
    df_eff = df.copy()
    df_eff['posizione_sec'] = df_eff['posizione'].apply(to_seconds)
    idx_start = 0
    idx_fine_primo = df_eff[df_eff['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df_eff[df_eff['evento'] == 'Fine partita'].index[0]
    t_start = df_eff.loc[idx_start, 'posizione_sec']
    t_fine_primo = df_eff.loc[idx_fine_primo, 'posizione_sec']
    t_start_secondo = df_eff.loc[idx_start_secondo, 'posizione_sec']
    t_fine_partita = df_eff.loc[idx_fine_partita, 'posizione_sec']
    tempo_effettivo_sec = []
    for i, row in df_eff.iterrows():
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
    df_eff['tempo_effettivo_sec'] = tempo_effettivo_sec
    df_eff['tempo_effettivo'] = df_eff['tempo_effettivo_sec'].apply(format_mmss)
    return df_eff

def filtra_per_tempo(df, tempo='primo'):
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]
    if tempo == 'primo':
        return df.loc[:idx_fine_primo]
    elif tempo == 'secondo':
        return df.loc[idx_fine_primo+1:idx_fine_partita]
    return df

def conta_eventi(df_parziale, evento):
    fatti = len(df_parziale[(df_parziale['evento'] == evento) & (df_parziale['squadra'] != 'Loro')])
    subiti = len(df_parziale[(df_parziale['evento'] == evento) & (df_parziale['squadra'] == 'Loro')])
    return fatti, subiti

def analizza_tiri_gol(df):
    return {
        'Gol fatti': len(df[(df['evento'] == 'Gol') & (df['squadra'] != 'Loro')]),
        'Gol subiti': len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Loro')]),
        'Tiri fatti': len(df[(df['evento'] == 'Tiro') & (df['squadra'] != 'Loro')]),
        'Tiri subiti': len(df[(df['evento'] == 'Tiro') & (df['squadra'] == 'Loro')]),
    }

# === INTERFACCIA ===
st.title("Tutte le partite disponibili")
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
        df['tempoReale_sec'] = df['posizione'].apply(to_seconds)
        df = calcola_tempo_effettivo(df)

        # Eventi per tempo
        df_primo = filtra_per_tempo(df, 'primo')
        df_secondo = filtra_per_tempo(df, 'secondo')

        # Conteggio eventi
        eventi_da_contare = ['Gol', 'Tiri', 'Parate', 'Angolo', 'Laterale', 'Fallo', 'Ammonizione', 'Espulsione', 'Timeout', '3v2', '2v1']
        dati_eventi = {"Evento": [], "Fatti primo tempo": [], "Subiti primo tempo": [], "Fatti secondo tempo": [], "Subiti secondo tempo": [], "Fatti totali": [], "Subiti totali": []}

        for evento in eventi_da_contare:
            fatti_1t, subiti_1t = conta_eventi(df_primo, evento)
            fatti_2t, subiti_2t = conta_eventi(df_secondo, evento)
            dati_eventi["Evento"].append(evento)
            dati_eventi["Fatti primo tempo"].append(fatti_1t)
            dati_eventi["Subiti primo tempo"].append(subiti_1t)
            dati_eventi["Fatti secondo tempo"].append(fatti_2t)
            dati_eventi["Subiti secondo tempo"].append(subiti_2t)
            dati_eventi["Fatti totali"].append(fatti_1t + fatti_2t)
            dati_eventi["Subiti totali"].append(subiti_1t + subiti_2t)

        df_eventi = pd.DataFrame(dati_eventi)

        # Risultato
        gol_fatti_tot = dati_eventi["Fatti totali"][0]
        gol_subiti_tot = dati_eventi["Subiti totali"][0]
        st.markdown(f"## Risultato: **FMP {gol_fatti_tot} – {gol_subiti_tot} {partita_info['avversario'].title()}**")

        # Durate dei tempi
        idx_inizio = 0
        idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
        idx_inizio_secondo = idx_fine_primo + 1
        idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]
        durata_primo = df.loc[idx_fine_primo, 'tempoReale_sec'] - df.loc[idx_inizio, 'tempoReale_sec']
        durata_secondo = df.loc[idx_fine_partita, 'tempoReale_sec'] - df.loc[idx_inizio_secondo, 'tempoReale_sec']
        durata_totale = durata_primo + durata_secondo

        df_stats_tempi = pd.DataFrame([analizza_tiri_gol(df_primo), analizza_tiri_gol(df_secondo)], index=['Primo tempo', 'Secondo tempo'])

        st.subheader("Durata dei tempi")
        st.dataframe(pd.DataFrame({"Periodo": ["Primo tempo", "Secondo tempo", "Totale partita"], "Durata_minuti": [round(durata_primo/60), round(durata_secondo/60), round(durata_totale/60)]}))

        st.subheader("Gol e Tiri per Tempo")
        st.dataframe(df_stats_tempi)

        st.subheader("Altri Eventi (Angoli, Laterali, Falli, etc.)")
        st.dataframe(df_eventi)
