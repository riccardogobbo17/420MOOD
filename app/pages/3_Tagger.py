"""Tagger stile Dartfish: shortcut, pannello keyword, sync video, CSV 2026/27."""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Tagger", layout="wide", page_icon="🏷️")

TAGGER_DIR = Path(__file__).resolve().parents[1] / "tagger"
INDEX = TAGGER_DIR / "index.html"
CSS = TAGGER_DIR / "tagger.css"
JS = TAGGER_DIR / "tagger.js"


def standalone_html() -> str:
    html = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="tagger.css" />',
        f"<style>\n{css}\n</style>",
    )
    html = html.replace('<script src="tagger.js"></script>', f"<script>\n{js}\n</script>")
    return html


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
**Live** — avvia il cronometro e tagga da tastiera mentre guardi la partita.
**Video** — carica il file (o YouTube), click su un evento per saltare a quel momento.
**Sync** — seleziona un evento ancora, posiziona il video, *Allinea tutti*.
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
    "Qui sotto funziona comunque: clicca dentro il riquadro prima di taggare."
)

html = standalone_html()
components.html(html, height=980, scrolling=True)
