import streamlit as st
import pandas as pd
import os

# Moduli locali
from futsal_analysis.config_supabase import get_supabase_client, TABELLA_PARTITE, TABELLA_EVENTI
from futsal_analysis.utils_time import *
from futsal_analysis.utils_eventi import *
from futsal_analysis.dashboard_utils import render_panoramica_stagione

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

# CSS per le card metriche e layout mobile
st.markdown("""
<style>
    .main .block-container {
        font-size: 14px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2em !important;
    }
    .stMarkdown {
        font-size: 14px !important;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #1565c0;
    }
    .metric-label {
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header con logo
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        # Usa percorso assoluto per compatibilità con deployment
        logo_path = os.path.join(os.path.dirname(__file__), "imgs", "logoFMP.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=100)
        else:
            # Fallback al percorso relativo per compatibilità locale
            st.image("imgs/logoFMP.png", width=100)
    except Exception as e:
        # Se non riesce a caricare l'immagine, continua senza errori
        st.markdown("🏠")
with col_title:
    st.title("🏠 FMP Dashboard")

supabase = get_supabase_client()

# --- CATEGORIA E STAGIONE FISSE ---
# Si lavora solo con la Prima Squadra e con la stagione corrente: il selettore
# di categoria e' stato rimosso, resta la costante per filtrare le partite a DB.
CATEGORIA = 'Prima Squadra'
STAGIONE = '2026/27'
categoria_scelta = CATEGORIA

st.caption(f"Prima Squadra · Stagione {STAGIONE}")

# --- Carica dati del campionato ---
res = supabase.table(TABELLA_PARTITE).select("*").eq("competizione", "Campionato").eq("categoria", CATEGORIA).order("data", desc=True).execute()
partite_campionato = res.data

if not partite_campionato:
    st.warning("Nessuna partita di campionato trovata.")
    # st.info("Usa il menu a sinistra per navigare nell'applicazione 👈")
    st.stop()

# --- Carica eventi: una query per ogni partita ---
partite_ids = [p['id'] for p in partite_campionato]
eventi_totali = []

with st.spinner("Caricamento eventi in corso..."):
    for partita_id in partite_ids:
        eventi_res = supabase.table(TABELLA_EVENTI).select("*").eq("partita_id", partita_id).order("posizione").execute()
        if eventi_res.data:
            eventi_totali.extend(eventi_res.data)

if not eventi_totali:
    st.warning("Nessun evento trovato per le partite di campionato.")
    st.stop()

# Crea DataFrame completo
df_all = pd.DataFrame(eventi_totali)
df_all.columns = df_all.columns.str.strip().str.lower().str.replace(" ", "_")
df_all = df_all.copy()
# Colonna 'dove' (zone) non piu' usata: resta nel DB ma non viene normalizzata.
# df_all['dove'] = pd.to_numeric(df_all.get('dove', None), errors='coerce').fillna(0).astype(int)
df_all['Periodo'] = tag_primo_secondo_tempo(df_all)
df_all['tempoEffettivo'] = calcola_tempo_effettivo(df_all)
df_all['tempoReale'] = calcola_tempo_reale(df_all)

# --- PANORAMICA STAGIONE ---
render_panoramica_stagione(df_all, partite_ids)

# --- ULTIME PARTITE ---
st.markdown("---")
st.subheader("📅 Ultime 5 Partite")

ultime_5 = sorted(partite_campionato, key=lambda x: x['data'], reverse=True)[:5]

for partita in ultime_5:
    # Calcola risultato
    df_partita = df_all[df_all['partita_id'] == partita['id']]
    gol_fatti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Noi')])
    gol_subiti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Loro')])
    
    # Determina risultato
    if gol_fatti > gol_subiti:
        risultato_label = "✅ Vittoria"
        color = "#e8f5e9"
    elif gol_fatti < gol_subiti:
        risultato_label = "❌ Sconfitta"
        color = "#ffebee"
    else:
        risultato_label = "🟰 Pareggio"
        color = "#fff9c4"
    
    col_data, col_avv, col_ris, col_risultato = st.columns([1, 2, 1, 1])
    
    with col_data:
        st.markdown(f"**{partita['data']}**")
    with col_avv:
        st.markdown(f"vs **{partita['avversario'].title()}**")
    with col_ris:
        st.markdown(f"""
        <div style="background-color: {color}; padding: 8px; border-radius: 5px; text-align: center;">
            <strong>{gol_fatti} - {gol_subiti}</strong>
        </div>
        """, unsafe_allow_html=True)
    with col_risultato:
        st.markdown(risultato_label)

# --- FOOTER ---
st.markdown("---")

