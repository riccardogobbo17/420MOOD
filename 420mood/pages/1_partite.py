import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
from itertools import combinations
from collections import defaultdict

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
    else:
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
    idx_fine_primo = df_eff[df_eff['evento'].str.lower() == 'fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df_eff[df_eff['evento'].str.lower() == 'fine partita'].index[0]
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

def get_quartetto(row):
    giocatori = []
    for col in ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4']:
        if pd.notna(row.get(col)):
            giocatori.append(row[col])
    giocatori = [g for g in giocatori if pd.notna(g) and str(g).strip() != '']
    return tuple(sorted(set(giocatori)))

def filtra_per_tempo(df, tempo='primo'):
    idx_fine_primo = df[df['evento'].str.lower() == 'fine primo tempo'].index[0]
    idx_fine_partita = df[df['evento'].str.lower() == 'fine partita'].index[0]
    if tempo == 'primo':
        return df.loc[:idx_fine_primo]
    elif tempo == 'secondo':
        return df.loc[idx_fine_primo+1:idx_fine_partita]
    return df

def conta_eventi(df_parziale, evento):
    evento = evento.lower()
    fatti = len(df_parziale[(df_parziale['evento'].str.lower() == evento) & (df_parziale['squadra'].str.lower() != 'loro')])
    subiti = len(df_parziale[(df_parziale['evento'].str.lower() == evento) & (df_parziale['squadra'].str.lower() == 'loro')])
    return fatti, subiti

def riepilogo_eventi_divisi(df_primo, df_secondo, eventi_da_contare):
    dati_eventi = {
        "Evento": [], "Fatti primo tempo": [], "Subiti primo tempo": [],
        "Fatti secondo tempo": [], "Subiti secondo tempo": [],
        "Fatti totali": [], "Subiti totali": []
    }
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
    return pd.DataFrame(dati_eventi)

from collections import defaultdict
from itertools import combinations

def tabella_minuti_percentuali(df_sub, tipo='quartetto', durata_rif=None):
    if 'delta_reale' not in df_sub.columns:
        raise ValueError("La colonna 'delta_reale' è necessaria. Calcolala prima di usare questa funzione.")
    if durata_rif is None:
        durata_rif = df_sub['delta_reale'].sum()
        if durata_rif == 0:
            raise ValueError("Durata di riferimento nulla: impossibile calcolare le percentuali.")

    acc = defaultdict(float)
    for idx, row in df_sub.iterrows():
        giocatori = list(row['quartetto'])
        delta = row['delta_reale']
        if tipo == 'quartetto' and len(giocatori) >= 4:
            key = tuple(sorted(set(giocatori)))
            acc[key] += delta
        if tipo == 'coppia':
            for c in combinations(sorted(set(giocatori)), 2):
                acc[c] += delta
        if tipo == 'singolo':
            for g in set(giocatori):
                acc[g] += delta

    if tipo == 'quartetto':
        df_out = pd.DataFrame([{ "Quartetto": k, "Minuti giocati": v / 60, "Percentuale": 100 * v / durata_rif } for k, v in acc.items()])
        col_sort = "Minuti giocati"
    elif tipo == 'coppia':
        df_out = pd.DataFrame([{ "Coppia": k, "Minuti giocati": v / 60, "Percentuale": 100 * v / durata_rif } for k, v in acc.items()])
        col_sort = "Minuti giocati"
    elif tipo == 'singolo':
        df_out = pd.DataFrame([{ "Giocatore": k, "Minuti giocati": v / 60, "Percentuale": 100 * v / durata_rif } for k, v in acc.items()])
        col_sort = "Minuti giocati"
    else:
        df_out = pd.DataFrame()
        col_sort = None


    # Aggiungi colonna MM:SS
    if "Minuti giocati" in df_out.columns:
        df_out["Tempo MM:SS"] = df_out["Minuti giocati"].apply(format_mmss)

    if col_sort:
        return df_out.sort_values(by=col_sort, ascending=False).reset_index(drop=True)
    return df_out


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
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df['tempoReale_sec'] = df['posizione'].apply(to_seconds)
        df = calcola_tempo_effettivo(df)
        df['delta_reale'] = df['tempoReale_sec'].shift(-1) - df['tempoReale_sec']
        df['delta_reale'] = df['delta_reale'].fillna(0)
        df['quartetto'] = df.apply(get_quartetto, axis=1)

        # Indici temporali
        idx_inizio = 0
        idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
        idx_inizio_secondo = idx_fine_primo + 1
        idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]
        durata_primo = df.loc[idx_fine_primo, 'tempoReale_sec'] - df.loc[idx_inizio, 'tempoReale_sec']
        durata_secondo = df.loc[idx_fine_partita, 'tempoReale_sec'] - df.loc[idx_inizio_secondo, 'tempoReale_sec']
        durata_totale = durata_primo + durata_secondo

        df_primo = df.loc[df.index <= idx_fine_primo].copy()
        df_secondo = df.loc[df.index >= idx_inizio_secondo].copy()

        eventi_da_contare = ['Gol', 'Tiri', 'Parate', 'Angolo', 'Laterale', 'Fallo', 'Ammonizione', 'Espulsione', 'Timeout', '3v2', '2v1']
        df_eventi = riepilogo_eventi_divisi(df_primo, df_secondo, eventi_da_contare)

        gol_fatti_1t, gol_subiti_1t = conta_eventi(df_primo, 'Gol')
        gol_fatti_2t, gol_subiti_2t = conta_eventi(df_secondo, 'Gol')
        gol_fatti_tot = gol_fatti_1t + gol_fatti_2t
        gol_subiti_tot = gol_subiti_1t + gol_subiti_2t
        st.markdown(f"## Risultato: **FMP {gol_fatti_tot} – {gol_subiti_tot} {partita_info['avversario'].title()}**")

        st.subheader("Durata dei tempi")
        st.dataframe(pd.DataFrame({"Periodo": ["Primo tempo", "Secondo tempo", "Totale partita"], "Durata_minuti": [round(durata_primo/60), round(durata_secondo/60), round(durata_totale/60)]}))

        st.subheader("Eventi per tempo")
        st.dataframe(df_eventi)

        # --- CALCOLA E MOSTRA TABELLE MINUTI/%

        # Calcola tutte le tabelle
        df_quartetti_tot = tabella_minuti_percentuali(df, tipo='quartetto', durata_rif=durata_totale)
        df_quartetti_1t = tabella_minuti_percentuali(df_primo, tipo='quartetto', durata_rif=durata_primo)
        df_quartetti_2t = tabella_minuti_percentuali(df_secondo, tipo='quartetto', durata_rif=durata_secondo)

        df_coppie_tot = tabella_minuti_percentuali(df, tipo='coppia', durata_rif=durata_totale)
        df_coppie_1t = tabella_minuti_percentuali(df_primo, tipo='coppia', durata_rif=durata_primo)
        df_coppie_2t = tabella_minuti_percentuali(df_secondo, tipo='coppia', durata_rif=durata_secondo)

        df_singoli_tot = tabella_minuti_percentuali(df, tipo='singolo', durata_rif=durata_totale)
        df_singoli_1t = tabella_minuti_percentuali(df_primo, tipo='singolo', durata_rif=durata_primo)
        df_singoli_2t = tabella_minuti_percentuali(df_secondo, tipo='singolo', durata_rif=durata_secondo)


        st.subheader("Minuti giocati per quartetto")
        # df_quartetti_tot = tabella_minuti_percentuali(df, tipo='quartetto', durata_rif=durata_totale)
        # df_quartetti_1t = tabella_minuti_percentuali(df_primo, tipo='quartetto', durata_rif=durata_primo)
        # df_quartetti_2t = tabella_minuti_percentuali(df_secondo, tipo='quartetto', durata_rif=durata_secondo)

        with st.expander("Totale partita - Quartetti"):
            st.dataframe(df_quartetti_tot)
        with st.expander("Primo tempo - Quartetti"):
            st.dataframe(df_quartetti_1t)
        with st.expander("Secondo tempo - Quartetti"):
            st.dataframe(df_quartetti_2t)

        st.subheader("Minuti giocati per coppia")
        # df_coppie_tot = tabella_minuti_percentuali(df, tipo='coppia', durata_rif=durata_totale)
        # df_coppie_1t = tabella_minuti_percentuali(df_primo, tipo='coppia', durata_rif=durata_primo)
        # df_coppie_2t = tabella_minuti_percentuali(df_secondo, tipo='coppia', durata_rif=durata_secondo)

        with st.expander("Totale partita - Coppie"):
            st.dataframe(df_coppie_tot)
        with st.expander("Primo tempo - Coppie"):
            st.dataframe(df_coppie_1t)
        with st.expander("Secondo tempo - Coppie"):
            st.dataframe(df_coppie_2t)

        st.subheader("Minuti giocati per giocatore")
        # df_singoli_tot = tabella_minuti_percentuali(df, tipo='singolo', durata_rif=durata_totale)
        # df_singoli_1t = tabella_minuti_percentuali(df_primo, tipo='singolo', durata_rif=durata_primo)
        # df_singoli_2t = tabella_minuti_percentuali(df_secondo, tipo='singolo', durata_rif=durata_secondo)

        with st.expander("Totale partita - Singoli"):
            st.dataframe(df_singoli_tot)
        with st.expander("Primo tempo - Singoli"):
            st.dataframe(df_singoli_1t)
        with st.expander("Secondo tempo - Singoli"):
            st.dataframe(df_singoli_2t)

