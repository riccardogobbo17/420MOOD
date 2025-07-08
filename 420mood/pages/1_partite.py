import streamlit as st
import pandas as pd
from matplotlib import cm
import matplotlib.pyplot as plt

# Moduli locali
from futsal_analysis.config_supabase import get_supabase_client
from futsal_analysis.utils_time import *
from futsal_analysis.utils_eventi import *
from futsal_analysis.utils_minutaggi import *
from futsal_analysis.pitch_drawer import FutsalPitch
from futsal_analysis.zone_analysis import *

st.set_page_config(page_title="Analisi Futsal", layout="wide")
st.title("Tutte le partite disponibili")

supabase = get_supabase_client()
res = supabase.table("partite").select("*").order("data", desc=True).execute()
partite = res.data

if not partite:
    st.warning("Nessuna partita trovata.")
    st.stop()

# --- Griglia partite con pulsante Analizza ---
n_cols = 4
for i in range(0, len(partite), n_cols):
    cols = st.columns(n_cols)
    for j, partita in enumerate(partite[i:i+n_cols]):
        with cols[j]:
            st.markdown(f"### {partita['avversario'].title()}")
            st.write(f"{partita['competizione'].capitalize()} — {partita['data']}")
            if st.button("Analizza", key=f"btn_{i}_{j}"):
                st.session_state["partita_scelta"] = partita["id"]

if "partita_scelta" not in st.session_state:
    st.stop()

partita_id = st.session_state["partita_scelta"]
partita_info = next((p for p in partite if p["id"] == partita_id), None)
st.markdown("---")
st.subheader(f"Analisi di {partita_info['competizione'].capitalize()} vs {partita_info['avversario'].title()} — {partita_info['data']}")

# --- Carica eventi della partita scelta ---
eventi = supabase.table("eventi").select("*").eq("partita_id", partita_id).execute().data
df = pd.DataFrame(eventi)
if df.empty:
    st.warning("Nessun evento trovato per questa partita.")
    st.stop()

# --- Data cleaning/normalizzazione ---
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.copy()
df['field_position'] = pd.to_numeric(df['field_position'], errors='coerce').fillna(0).astype(int)
df['Periodo'] = tag_primo_secondo_tempo(df)
df['tempoEffettivo'] = calcola_tempo_effettivo(df)
df['tempoReale'] = calcola_tempo_reale(df)

# --- RISULTATO ---
gol_fatti = len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Noi')])
gol_subiti = len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Loro')])
st.markdown(f"## Risultato: **FMP {gol_fatti} – {gol_subiti} {partita_info['avversario'].title()}**")

# --- TABS ---
tabs = st.tabs(["Stats Squadra", "Stats Individuali", "Zone", "Minutaggi"])

# === TAB 1: Stats Squadra ===
with tabs[0]:
    st.header("Statistiche di squadra")
    report_eventi = calcola_report_completo(df)
    for nome_tabella, dati in report_eventi['squadra'].items():
        st.markdown(f"**{nome_tabella.replace('_', ' ').capitalize()}**")
        if isinstance(dati, dict):
            st.dataframe(pd.DataFrame(list(dati.items()), columns=['Stat', 'Valore']).set_index('Stat'))
        else:
            st.write(dati)

    # st.subheader("Timeline Gol")
    # gol_events = df[df['evento'] == 'Gol'][['tempoReale', 'squadra', 'giocatore', 'descrizione']]
    # st.dataframe(gol_events)

# === TAB 2: Stats Individuali ===
with tabs[1]:
    st.header("Statistiche individuali giocatori")
    st.dataframe(pd.DataFrame(report_eventi['individuali']).T)
    st.header("Statistiche portieri individuali")
    st.dataframe(pd.DataFrame(report_eventi['portieri_individuali']).T)

# === TAB 3: Zone ===
with tabs[2]:
    st.header("Analisi zonale")
    campo = FutsalPitch()
    report_zona = calcola_report_zona(df)

    team_keys = list(report_zona['squadra'].keys())
    team_key_sel = st.selectbox("Categoria squadra", team_keys, format_func=lambda x: x.replace("_", " ").capitalize(), key="zona_squadra")

    zone_example = report_zona['squadra'][team_key_sel]
    if isinstance(zone_example, dict) and len(zone_example) > 0:
        first_zone = next(iter(zone_example.values()))
        metric_keys = list(first_zone.keys())
    else:
        metric_keys = []
    stat_keys_sel = st.multiselect(
        "Statistiche da visualizzare (squadra)", metric_keys, default=metric_keys[:3], key="zona_stats_squadra"
    )

    st.subheader(f"Distribuzione per zona – squadra ({team_key_sel})")
    if stat_keys_sel:
        fig, ax = draw_team_metric_per_zone(
            report_zona, campo, stat_keys_sel, team_key=team_key_sel,
            title=f"{', '.join(stat_keys_sel)} per zona ({team_key_sel})", cmap=cm.Reds
        )
        st.pyplot(fig)
    else:
        st.info("Seleziona almeno una statistica.")

    st.markdown("---")
    st.header("Report zonale – giocatore")
    giocatori = sorted({
        g for zona in report_zona['individuali'].values()
        for g in zona.keys() if g.strip()
    })
    giocatore_scelto = st.selectbox("Scegli giocatore", giocatori, key="zona_giocatore")

    for z, zona in report_zona['individuali'].items():
        if giocatore_scelto in zona:
            metriche_giocatore = list(zona[giocatore_scelto].keys())
            break
    else:
        metriche_giocatore = []

    stat_keys_giocatore_sel = st.multiselect(
        "Statistiche da visualizzare (giocatore)", metriche_giocatore, default=metriche_giocatore[:3], key="zona_stats_giocatore"
    )

    st.subheader(f"Distribuzione per zona – {giocatore_scelto.capitalize()}")
    if stat_keys_giocatore_sel:
        fig, ax = draw_player_metric_per_zone(
            report_zona['individuali'], campo, stat_keys_giocatore_sel, chi=giocatore_scelto,
            title=f"{', '.join(stat_keys_giocatore_sel)} per zona ({giocatore_scelto})", cmap=cm.Blues
        )
        st.pyplot(fig)
    else:
        st.info("Seleziona almeno una statistica.")

# === TAB 4: Minutaggi ===
with tabs[3]:
    st.header("Minutaggi")
    df_1t = filtra_per_tempo(df, 'Primo tempo')
    df_2t = filtra_per_tempo(df, 'Secondo tempo')
    minutaggi = calcola_minutaggi(df, df_1t, df_2t)

    for periodo, categorie in minutaggi.items():
        st.subheader(periodo.upper())
        for nome_tabella, df_ in categorie.items():
            st.markdown(f"**{nome_tabella.replace('_', ' ').capitalize()}**")
            st.dataframe(df_)
