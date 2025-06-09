import streamlit as st
import pandas as pd

GIOCATORI_FILE = "giocatori.csv"
st.title("Gestione Giocatori")
try:
    giocatori = pd.read_csv(GIOCATORI_FILE)
    st.dataframe(giocatori)
except Exception as e:
    st.warning(f"Impossibile caricare {GIOCATORI_FILE}: {e}")
