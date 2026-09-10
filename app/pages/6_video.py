import streamlit as st
from futsal_analysis.config_supabase import get_supabase_client, TABELLA_PARTITE

st.set_page_config(page_title="Video Partite", layout="wide", page_icon="🎥")

# Unica categoria gestita dall'app (allineata a Home / Admin / Partite).
CATEGORIA = "Prima Squadra"

supabase = get_supabase_client()
categoria_attiva = CATEGORIA

st.header(f"Tutte le partite disponibili - {categoria_attiva}")
st.caption(f"Prima Squadra · stagione 2026/27")

# --- Carica partite FILTRATE PER CATEGORIA ---
res = supabase.table(TABELLA_PARTITE).select("*").eq("categoria", categoria_attiva).order("data", desc=True).execute()
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
            # Avversario e competizione possono essere nulli a DB: uso 'or ""'
            # per non far esplodere .title() / .capitalize() su None.
            st.markdown(f"### {(partita.get('avversario') or '').title()}")
            st.write(f"{(partita.get('competizione') or '').capitalize()} — {partita.get('data', '')}")
            # Il link YouTube e' opzionale: puo' arrivare None o stringa vuota.
            yt_link = (partita.get("yt_link") or "").strip()
            if yt_link:
                st.video(yt_link)
            else:
                st.info("🎥 Nessun link YouTube disponibile per questa partita.")
