import streamlit as st
import pandas as pd
from supabase import create_client
from futsal_analysis.config_supabase import get_supabase_client

# === CONFIG ===
supabase = get_supabase_client()

def to_id_partita(data, avversario):
    return f"{data}_{avversario}".replace(" ", "_").replace("/", "-")

def parse_data_sicura(data_str):
    try:
        return pd.to_datetime(data_str, format="%d/%m/%Y", errors="raise")
    except Exception:
        try:
            return pd.to_datetime(data_str, errors="raise")
        except:
            return pd.NaT

st.set_page_config(page_title="Admin - Futsal", layout="wide")
st.title("Pannello Admin")
admin_password = "admin"
password = st.text_input("Password", type="password")
if password != admin_password:
    st.stop()

# --- SEZIONE 1: Inserisci nuova partita ---
st.header("➕ Inserisci nuova partita")
with st.form("nuova_partita"):
    data = st.date_input("Data partita")
    avversario = st.text_input("Avversario")
    competizione = st.text_input("Competizione")
    yt_link = st.text_input("Link YouTube (opzionale)")
    submitted = st.form_submit_button("Salva partita")

    if submitted:
        if not data or not avversario:
            st.error("⚠️ Devi inserire almeno data e avversario.")
        else:
            partita_id = to_id_partita(str(data), avversario)
            supabase.table("partite").insert({
                "id": partita_id,
                "data": str(data),
                "avversario": avversario,
                "competizione": competizione,
                "yt_link": yt_link
            }).execute()
            st.success(f"✅ Partita '{avversario}' inserita con ID {partita_id}")

# --- SEZIONE 2: Upload CSV eventi ---
st.header("📂 Carica eventi da CSV")
partite = supabase.table("partite").select("id, avversario, data").order("data", desc=True).execute().data
if not partite:
    st.warning("Nessuna partita trovata, crea prima una nuova partita.")
    st.stop()

partita_scelta = st.selectbox("Seleziona partita", [f"{p['data']} - {p['avversario']} ({p['id']})" for p in partite])
file = st.file_uploader("Carica CSV eventi", type=["csv"])

if file and partita_scelta:
    partita_id = partita_scelta.split("(")[-1].strip(")")
    df = pd.read_csv(file)

    # Preprocessing (come nel tuo script)
    df = df.rename(columns={
        "Quartetto.1": "quartetto_1",
        "Quartetto.2": "quartetto_2",
        "Quartetto.3": "quartetto_3",
        "Quartetto.4": "quartetto_4"
    })

    df["partita_id"] = partita_id

    colonne_valide = [
        "Posizione", "Data", "Evento", "Portiere", "Quartetto",
        "quartetto_1", "quartetto_2", "quartetto_3", "quartetto_4",
        "Chi", "Esito", "Field Position", "Piede", "Squadra", "partita_id"
    ]
    for col in colonne_valide:
        if col not in df.columns:
            df[col] = None

    df = df[colonne_valide]
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.fillna("")

    eventi_data = df.to_dict(orient="records")

    if st.button("Carica eventi nel DB"):
        batch_size = 500
        for i in range(0, len(eventi_data), batch_size):
            supabase.table("eventi").insert(eventi_data[i:i+batch_size]).execute()
        st.success(f"✅ Caricati {len(eventi_data)} eventi per la partita {partita_id}")
