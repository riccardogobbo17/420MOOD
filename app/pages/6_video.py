import streamlit as st
from futsal_analysis.config_supabase import get_supabase_client

st.set_page_config(page_title="Video Partite", layout="wide", page_icon="🎥")

# --- VERIFICA CATEGORIA SELEZIONATA ---
supabase = get_supabase_client()

# Se non c'è una categoria in session_state, imposta un default
if 'categoria_selezionata' not in st.session_state:
    # Carica le categorie disponibili
    res_all = supabase.table("partite").select("categoria").execute()
    categorie_disponibili = sorted(list(set([p.get('categoria', 'Prima Squadra') for p in res_all.data if p.get('categoria')])))
    st.session_state['categoria_selezionata'] = categorie_disponibili[0] if categorie_disponibili else 'Prima Squadra'

categoria_attiva = st.session_state['categoria_selezionata']

st.header(f"Tutte le partite disponibili - {categoria_attiva}")
st.info(f"📂 Categoria attiva: **{categoria_attiva}** (modificabile dalla Homepage)")

# --- Carica partite FILTRATE PER CATEGORIA ---
res = supabase.table("partite").select("*").eq("categoria", categoria_attiva).order("data", desc=True).execute()
partite = res.data

if not partite:
    st.warning("Nessuna partita trovata.")
    st.stop()

# --- Griglia partite con video ---
n_cols = 2  # 2 colonne per non stringere troppo i video
for i in range(0, len(partite), n_cols):
    cols = st.columns(n_cols)
    for j, partita in enumerate(partite[i:i+n_cols]):
        with cols[j]:
            st.markdown(f"### {partita['avversario'].title()}")
            st.write(f"{partita['competizione'].capitalize()} — {partita['data']}")
            if partita.get("yt_link"):
                st.video(partita["yt_link"])
            else:
                st.warning("Nessun link YouTube disponibile per questa partita.")
