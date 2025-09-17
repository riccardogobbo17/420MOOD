import streamlit as st
from futsal_analysis.config_supabase import get_supabase_client

st.set_page_config(page_title="Video Partite", layout="wide", page_icon="🎥")
st.header("Tutte le partite disponibili")

# --- Connessione Supabase ---
supabase = get_supabase_client()
res = supabase.table("partite").select("*").order("data", desc=True).execute()
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
