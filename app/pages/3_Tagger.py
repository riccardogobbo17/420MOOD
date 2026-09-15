"""Tagger stile Dartfish: shortcut, pannello keyword, sync video, CSV 2026/27."""

from pathlib import Path
import sys

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Tagger", layout="wide", page_icon="🏷️")

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from tagger.standalone import standalone_html  # noqa: E402


st.markdown(
    """
    <style>
      .block-container { padding-top: 1.1rem; padding-bottom: 0.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.header("🏷️ Tagger partita")
st.caption(
    "Stesso flusso di Dartfish Pro S: tasto → riga evento, pannello per le colonne, "
    "poi sync sul video e correzione timestamp."
)

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    st.markdown(
        """
**Live** — cronometro compatto e pannello tagging a tutta larghezza.
**Video** — file o YouTube, cambiabili in qualsiasi momento. Click su un evento per saltare lì.
**Sessione** — *Salva sessione* (JSON) prima di chiudere; *Carica sessione* per riprendere. YouTube torna da solo, un file locale va ricollegato.
**DB** — *Invia a DB* carica gli eventi su Supabase come in Admin (serve.py).
**Secondo schermo** — *Apri video su altra finestra*, trascinala sulla TV, Schermo intero.
        """
    )
with col_b:
    st.download_button(
        "Scarica HTML standalone",
        data=standalone_html(),
        file_name="fmp-tagger.html",
        mime="text/html",
        use_container_width=True,
    )
with col_c:
    st.code("python app/tagger/serve.py", language="bash")

st.info(
    "Per i tasti al 100% apri il tagger in una scheda dedicata "
    "(`python app/tagger/serve.py` oppure lo HTML scaricato). "
    "Fine primo tempo scarica da solo il CSV `…_primo-tempo.csv`. "
    "Genera PDF funziona da `serve.py` (http://127.0.0.1:8765/)."
)

html = standalone_html()
components.html(html, height=980, scrolling=True)
