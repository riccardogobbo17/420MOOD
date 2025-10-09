import streamlit as st
import pandas as pd

# Moduli locali
from futsal_analysis.config_supabase import get_supabase_client
from futsal_analysis.utils_time import *
from futsal_analysis.utils_eventi import *

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
        st.image("imgs/logoFMP.png", width=100)
    except:
        pass
with col_title:
    st.title("🏠 FMP Dashboard")

# --- SELETTORE CATEGORIA ---
supabase = get_supabase_client()

# Carica tutte le partite per ottenere le categorie disponibili
res_all = supabase.table("partite").select("categoria").execute()
categorie_disponibili = sorted(list(set([p.get('categoria', 'Prima Squadra') for p in res_all.data if p.get('categoria')])))

# Se non ci sono categorie nel DB, usa un default
if not categorie_disponibili:
    categorie_disponibili = ['Prima Squadra']

# Inizializza la categoria in session_state se non esiste
if 'categoria_selezionata' not in st.session_state:
    st.session_state['categoria_selezionata'] = categorie_disponibili[0]

# Selectbox per la categoria
categoria_scelta = st.selectbox(
    "📂 Seleziona Categoria",
    categorie_disponibili,
    index=categorie_disponibili.index(st.session_state['categoria_selezionata']) if st.session_state['categoria_selezionata'] in categorie_disponibili else 0,
    key="categoria_selectbox"
)

# Aggiorna la categoria in session_state
st.session_state['categoria_selezionata'] = categoria_scelta

st.markdown(f"### Panoramica Stagione - Campionato ({categoria_scelta})")
st.markdown("---")

# --- Carica dati del campionato FILTRATI PER CATEGORIA ---
res = supabase.table("partite").select("*").eq("competizione", "campionato").eq("categoria", categoria_scelta).order("data", desc=True).execute()
partite_campionato = res.data

if not partite_campionato:
    st.warning("Nessuna partita di campionato trovata.")
    st.info("Usa il menu a sinistra per navigare nell'applicazione 👈")
    st.stop()

# --- Carica eventi ---
partite_ids = [p['id'] for p in partite_campionato]
eventi_res = supabase.table("eventi").select("*").in_("partita_id", partite_ids).order("partita_id, posizione").execute()
eventi_totali = eventi_res.data

if not eventi_totali:
    st.warning("Nessun evento trovato per le partite di campionato.")
    st.stop()

# Crea DataFrame completo
df_all = pd.DataFrame(eventi_totali)
df_all.columns = df_all.columns.str.strip().str.lower().str.replace(" ", "_")
df_all = df_all.copy()
df_all['dove'] = pd.to_numeric(df_all.get('dove', None), errors='coerce').fillna(0).astype(int)
df_all['Periodo'] = tag_primo_secondo_tempo(df_all)
df_all['tempoEffettivo'] = calcola_tempo_effettivo(df_all)
df_all['tempoReale'] = calcola_tempo_reale(df_all)

# --- CALCOLO METRICHE ---
num_partite = len(partite_campionato)

# Gol per partita
gol_fatti_totali = len(df_all[(df_all['evento'] == 'Gol') & (df_all['squadra'] == 'Noi')])
gol_subiti_totali = len(df_all[(df_all['evento'] == 'Gol') & (df_all['squadra'] == 'Loro')])
gol_medi_fatti = gol_fatti_totali / num_partite if num_partite > 0 else 0
gol_medi_subiti = gol_subiti_totali / num_partite if num_partite > 0 else 0

# Tiri per partita
tiri_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Noi')])
tiri_medi = tiri_totali / num_partite if num_partite > 0 else 0

tiri_subiti_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Loro')])
tiri_subiti_medi = tiri_subiti_totali / num_partite if num_partite > 0 else 0

# Palle perse/recuperate per partita
palle_perse_totali = len(df_all[(df_all['evento'].str.contains('Palla persa', na=False))])
palle_recuperate_totali = len(df_all[(df_all['evento'].str.contains('Palla recuperata', na=False))])
palle_perse_medie = palle_perse_totali / num_partite if num_partite > 0 else 0
palle_recuperate_medie = palle_recuperate_totali / num_partite if num_partite > 0 else 0

# Falli per partita
falli_fatti_totali = len(df_all[(df_all['evento'].str.contains('Fallo', na=False)) & (df_all['squadra'] == 'Noi')])
falli_subiti_totali = len(df_all[(df_all['evento'].str.contains('Fallo', na=False)) & (df_all['squadra'] == 'Loro')])
falli_medi_fatti = falli_fatti_totali / num_partite if num_partite > 0 else 0
falli_medi_subiti = falli_subiti_totali / num_partite if num_partite > 0 else 0

# Percentuale tiri in porta
tiri_in_porta_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Noi') & df_all['esito'].isin(['Parata', 'Gol'])])
perc_tiri_in_porta = (tiri_in_porta_totali / tiri_totali * 100) if tiri_totali > 0 else 0

# Percentuale conversione tiri in gol
perc_conversione = (gol_fatti_totali / tiri_totali * 100) if tiri_totali > 0 else 0

# Calcola vittorie, pareggi, sconfitte
risultati = {'V': 0, 'P': 0, 'S': 0}
for p_id in partite_ids:
    df_partita = df_all[df_all['partita_id'] == p_id]
    gol_fatti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Noi')])
    gol_subiti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Loro')])
    if gol_fatti > gol_subiti:
        risultati['V'] += 1
    elif gol_fatti < gol_subiti:
        risultati['S'] += 1
    else:
        risultati['P'] += 1

# Calcola punti (3 per vittoria, 1 per pareggio)
punti_totali = risultati['V'] * 3 + risultati['P']

# --- VISUALIZZAZIONE METRICHE ---
st.markdown("---")

# Prima riga - Metriche principali
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{num_partite}</div>
        <div class="metric-label">Partite Giocate</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    color = "#2e7d32" if risultati['V'] >= risultati['S'] else "#c62828"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {color}; font-size: 1.5em;">{risultati['V']}V - {risultati['P']}P - {risultati['S']}S</div>
        <div class="metric-label">Risultati</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #1976d2;">{punti_totali}</div>
        <div class="metric-label">Punti Totali</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    diff_gol = gol_fatti_totali - gol_subiti_totali
    color = "#2e7d32" if diff_gol > 0 else "#c62828" if diff_gol < 0 else "#666"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {color};">{diff_gol:+d}</div>
        <div class="metric-label">Differenza Reti</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Seconda riga - Gol
col5, col6, col7, col8 = st.columns(4)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #2e7d32;">{gol_medi_fatti:.2f}</div>
        <div class="metric-label">Gol Fatti/Partita</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #c62828;">{gol_medi_subiti:.2f}</div>
        <div class="metric-label">Gol Subiti/Partita</div>
    </div>
    """, unsafe_allow_html=True)

with col7:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #2e7d32;">{gol_fatti_totali}</div>
        <div class="metric-label">Gol Totali Fatti</div>
    </div>
    """, unsafe_allow_html=True)

with col8:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #c62828;">{gol_subiti_totali}</div>
        <div class="metric-label">Gol Totali Subiti</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Terza riga - Tiri
col9, col10, col11, col12 = st.columns(4)

with col9:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{tiri_medi:.2f}</div>
        <div class="metric-label">Tiri/Partita</div>
    </div>
    """, unsafe_allow_html=True)

with col10:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{perc_tiri_in_porta:.1f}%</div>
        <div class="metric-label">Tiri in Porta</div>
    </div>
    """, unsafe_allow_html=True)

with col11:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{perc_conversione:.1f}%</div>
        <div class="metric-label">Conversione Tiri-Gol</div>
    </div>
    """, unsafe_allow_html=True)

with col12:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{tiri_subiti_medi:.2f}</div>
        <div class="metric-label">Tiri Subiti/Partita</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quarta riga - Possesso palla
col13, col14, col15, col16 = st.columns(4)

with col13:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #d84315;">{palle_perse_medie:.2f}</div>
        <div class="metric-label">Palle Perse/Partita</div>
    </div>
    """, unsafe_allow_html=True)

with col14:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #1565c0;">{palle_recuperate_medie:.2f}</div>
        <div class="metric-label">Palle Recuperate/Partita</div>
    </div>
    """, unsafe_allow_html=True)

with col15:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{falli_medi_fatti:.2f}</div>
        <div class="metric-label">Falli Fatti/Partita</div>
    </div>
    """, unsafe_allow_html=True)

with col16:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{falli_medi_subiti:.2f}</div>
        <div class="metric-label">Falli Subiti/Partita</div>
    </div>
    """, unsafe_allow_html=True)

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
        risultato_label = "➖ Pareggio"
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
st.info("👈 Usa il menu a sinistra per esplorare analisi dettagliate, statistiche individuali e molto altro!")
