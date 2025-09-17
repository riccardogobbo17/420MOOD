import streamlit as st
import pandas as pd

# Percorso relativo invece che assoluto (così funziona anche su Streamlit Cloud)
GIOCATORI_FILE = "./giocatori.csv"
st.set_page_config(page_title="Giocatori", page_icon="🌹", layout="wide")
st.header("Giocatori")

try:
    giocatori = pd.read_csv(GIOCATORI_FILE)

    # Controllo che ci sia la colonna "Categoria"
    if "Categoria" in giocatori.columns:
        # Creazione del filtro
        categorie = giocatori["Categoria"].dropna().unique()
        categoria_scelta = st.selectbox("Seleziona la categoria", sorted(categorie))

        # Filtraggio del DataFrame
        rosa_filtrata = giocatori[giocatori["Categoria"] == categoria_scelta]
        st.subheader(f"Rosa {categoria_scelta}")
        st.dataframe(rosa_filtrata.reset_index(drop=True))
    else:
        st.warning("⚠️ Il file non contiene la colonna 'Categoria'. Aggiungila per poter filtrare.")
    
except Exception as e:
    st.warning(f"Impossibile caricare {GIOCATORI_FILE}: {e}")

