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

    # --- GRAFICI DI SQUADRA (Attacco & Difesa) ---
    st.subheader("Statistiche di squadra per zona")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Attacco")
        zone_attacco = report_zona['squadra']['attacco']
        if zone_attacco:
            first_zone = next(iter(zone_attacco.values()))
            metriche_attacco = list(first_zone.keys())
            stat_keys_att_sel = st.multiselect(
                "Statistiche attacco (squadra)",
                metriche_attacco,
                default=metriche_attacco[:3],
                key="zona_stats_attacco_squadra"
            )
            if stat_keys_att_sel:
                fig, ax = draw_team_metric_per_zone(
                    report_zona, campo, stat_keys_att_sel,
                    team_key="attacco",
                    title="Attacco per zona (squadra)",
                    cmap=cm.Reds
                )
                st.pyplot(fig)
        else:
            st.info("Nessun dato di attacco disponibile.")

    with col2:
        st.markdown("#### Difesa")
        zone_difesa = report_zona['squadra']['difesa']
        if zone_difesa:
            first_zone = next(iter(zone_difesa.values()))
            metriche_difesa = list(first_zone.keys())
            stat_keys_dif_sel = st.multiselect(
                "Statistiche difesa (squadra)",
                metriche_difesa,
                default=metriche_difesa[:3],
                key="zona_stats_difesa_squadra"
            )
            if stat_keys_dif_sel:
                fig, ax = draw_team_metric_per_zone(
                    report_zona, campo, stat_keys_dif_sel,
                    team_key="difesa",
                    title="Difesa per zona (squadra)",
                    cmap=cm.Blues
                )
                st.pyplot(fig)
        else:
            st.info("Nessun dato di difesa disponibile.")

    st.markdown("---")

    # --- GRAFICI INDIVIDUALI (Attacco & Difesa) ---
    st.subheader("Statistiche individuali per zona")
    giocatori = sorted({
        g for zona in report_zona['individuali'].values()
        for g in zona.keys() if g.strip()
    })
    giocatore_scelto = st.selectbox("Scegli giocatore", giocatori, key="zona_giocatore")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### Attacco – {giocatore_scelto}")
        # Trovo metriche attacco per quel giocatore
        metriche_attacco_gioc = []
        for zona in report_zona['individuali'].values():
            if giocatore_scelto in zona:
                metriche_attacco_gioc = [k for k in zona[giocatore_scelto].keys() if "tiro" in k or "palla_persa" in k]
                break

        stat_keys_att_gioc_sel = st.multiselect(
            "Statistiche attacco (giocatore)",
            metriche_attacco_gioc,
            default=metriche_attacco_gioc[:3],
            key="zona_stats_attacco_gioc"
        )

        if stat_keys_att_gioc_sel:
            fig, ax = draw_player_metric_per_zone(
                report_zona['individuali'], campo, stat_keys_att_gioc_sel,
                chi=giocatore_scelto,
                title=f"Attacco per zona – {giocatore_scelto}",
                cmap=cm.OrRd
            )
            st.pyplot(fig)

    with col2:
        st.markdown(f"#### Difesa – {giocatore_scelto}")
        # Trovo metriche difesa per quel giocatore
        metriche_difesa_gioc = []
        for zona in report_zona['individuali'].values():
            if giocatore_scelto in zona:
                metriche_difesa_gioc = [k for k in zona[giocatore_scelto].keys() if "recuperata" in k or "falli" in k or "ribattuti" in k]
                break

        stat_keys_dif_gioc_sel = st.multiselect(
            "Statistiche difesa (giocatore)",
            metriche_difesa_gioc,
            default=metriche_difesa_gioc[:3],
            key="zona_stats_difesa_gioc"
        )

        if stat_keys_dif_gioc_sel:
            fig, ax = draw_player_metric_per_zone(
                report_zona['individuali'], campo, stat_keys_dif_gioc_sel,
                chi=giocatore_scelto,
                title=f"Difesa per zona – {giocatore_scelto}",
                cmap=cm.BuPu
            )
            st.pyplot(fig)


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
