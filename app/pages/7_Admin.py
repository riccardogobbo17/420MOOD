import streamlit as st
import pandas as pd
from supabase import create_client
from futsal_analysis.config_supabase import get_supabase_client

# === CONFIG ===
supabase = get_supabase_client()

# === UTILS ===
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


def preprocess_eventi(df: pd.DataFrame, partita_id: str) -> pd.DataFrame:
    df = df.rename(columns={
        "Posizione": "posizione",
        "Position": "posizione",
        "Data": "data",
        "Evento": "evento",
        "Portiere": "portiere",
        "Quartetto": "quartetto",
        "Chi": "chi",
        "Esito": "esito",
        "Field Position": "field_position",
        "Piede": "piede",
        "Squadra": "squadra"
    })

    df["partita_id"] = partita_id

    if "quartetto" in df.columns:
        # splitto in massimo 5 colonne (0–4)
        split_cols = df["quartetto"].fillna("").astype(str).str.split(";", expand=True)

        # sostituisco la colonna originale col primo giocatore
        df["quartetto"] = split_cols[0].str.strip()

    # creo le altre colonne (dal 2° giocatore in poi)
    for i in range(1, 5):  # dal secondo fino al quinto
        col_name = f"quartetto_{i}"
        if i < split_cols.shape[1]:
            df[col_name] = split_cols[i].str.strip()
        else:
            df[col_name] = None  # oppure "" se vuoi stringa vuota


    # # Split quartetto
    # if "quartetto" in df.columns:
    #     split_cols = df["quartetto"].fillna("").astype(str).str.split(";", expand=True)
    #     for i in range(4):
    #         col_name = f"quartetto_{i+1}"
    #         if i < split_cols.shape[1]:
    #             df[col_name] = split_cols[i].str.strip()
    #         else:
    #             df[col_name] = ""

    # Conversione data → YYYY-MM-DD
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")

    # 🔑 Qui NON converto più Position a numerico: la tengo come stringa
    if "posizione" in df.columns:
        df["posizione"] = df["posizione"].fillna("").astype(str).str.strip()

    colonne_finali = [
        "posizione", "data", "evento", "portiere", "quartetto",
        "quartetto_1", "quartetto_2", "quartetto_3", "quartetto_4",
        "chi", "esito", "field_position", "piede", "squadra", "partita_id"
    ]
    for col in colonne_finali:
        if col not in df.columns:
            df[col] = ""

    df = df[colonne_finali]
    df = df.fillna("")

    return df



# === STREAMLIT APP ===
st.set_page_config(page_title="Admin", layout="wide", page_icon="🔧")
st.header("Pannello Admin")

# Password di accesso
admin_password = "admin"
password = st.text_input("Password", type="password")
if password != admin_password:
    st.stop()

# --- SEZIONE 1: Inserisci nuova partita ---
st.markdown("#### ➕ Inserisci nuova partita")
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
    df_raw = pd.read_csv(file)

    # ✅ Preprocessing
    df = preprocess_eventi(df_raw, partita_id)
    eventi_data = df.to_dict(orient="records")

    st.write("Anteprima dati preprocessati:")
    st.dataframe(df.head(20))

    if st.button("Carica eventi nel DB"):
        batch_size = 500
        for i in range(0, len(eventi_data), batch_size):
            supabase.table("eventi").insert(eventi_data[i:i+batch_size]).execute()
        st.success(f"✅ Caricati {len(eventi_data)} eventi per la partita {partita_id}")
