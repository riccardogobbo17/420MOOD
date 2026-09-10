import streamlit as st
import pandas as pd
from supabase import create_client
from futsal_analysis.config_supabase import get_supabase_client, TABELLA_PARTITE, TABELLA_EVENTI

# === CONFIG ===
supabase = get_supabase_client()

# Unica categoria gestita dall'app.
CATEGORIA = "Prima Squadra"

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


def rileva_separatore(file) -> str:
    """Deduce il separatore dalla riga di intestazione.

    L'export 2026/27 usa il punto e virgola, i CSV precedenti la virgola. Non si
    puo' usare il dialect sniffer di pandas perche' nel vecchio formato il campo
    Quartetto contiene a sua volta dei punti e virgola.
    """
    posizione = file.tell()
    header = file.readline()
    file.seek(posizione)
    if isinstance(header, bytes):
        header = header.decode("utf-8", errors="ignore")
    return ";" if header.count(";") > header.count(",") else ","


def preprocess_eventi(df: pd.DataFrame, partita_id: str, categoria: str = None) -> pd.DataFrame:
    # `categoria` non serve piu' al preprocessing (prima distingueva il CSV
    # semplificato di U15/U17); resta nella firma per compatibilita'.
    df = df.rename(columns={
        "Posizione": "posizione",
        "Position": "posizione",
        "Data": "data",
        "Evento": "evento",
        "Portiere": "portiere",
        "Quartetto": "quartetto",
        "Chi": "chi",
        "Esito": "esito",
        "Field Position": "dove",
        "Piede": "piede",
        "Squadra": "squadra",
        "Dove": "dove",
        "Lato": "lato",
    })

    df["partita_id"] = partita_id

    # Dal formato 2026/27 il CSV non esporta piu' Quartetto e Piede. Le colonne
    # restano nel DB (verranno salvate vuote) ma non vengono piu' usate a valle.
    split_cols = None
    if "quartetto" in df.columns:
        # splitto in massimo 5 colonne (0–4)
        split_cols = df["quartetto"].fillna("").astype(str).str.split(";", expand=True)

        # sostituisco la colonna originale col primo giocatore
        df["quartetto"] = split_cols[0].str.strip()

    # creo le altre colonne (dal 2° giocatore in poi)
    for i in range(1, 5):  # dal secondo fino al quinto
        col_name = f"quartetto_{i}"
        if split_cols is not None and i < split_cols.shape[1]:
            df[col_name] = split_cols[i].str.strip()
        else:
            df[col_name] = ""

    # Conversione data → YYYY-MM-DD
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")

    # 🔑 Qui NON converto più Position a numerico: la tengo come stringa
    if "posizione" in df.columns:
        df["posizione"] = df["posizione"].fillna("").astype(str).str.strip()

    colonne_finali = [
        "posizione", "data", "evento", "chi", "esito", "dove", "lato", "piede", 
         "portiere", 
         "quartetto",
         "quartetto_1", "quartetto_2", "quartetto_3", "quartetto_4",
         "squadra",
         "partita_id"
    ]
    for col in colonne_finali:
        if col not in df.columns:
            df[col] = ""

    df = df[colonne_finali]
    df = df.fillna("")
    
    # Sostituisci anche le stringhe 'nan' con stringhe vuote
    df = df.replace('nan', '')
    
    # ✅ ORDINAMENTO per posizione prima del salvataggio
    df = df.sort_values("posizione")

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
    # Si lavora solo con la Prima Squadra: la colonna resta a DB ma non e' piu'
    # modificabile dal form (niente U15/U17/U19).
    categoria = CATEGORIA
    yt_link = st.text_input("Link YouTube (opzionale)")
    submitted = st.form_submit_button("Salva partita")

    if submitted:
        if not data or not avversario:
            st.error("⚠️ Devi inserire almeno data e avversario.")
        else:
            partita_id = to_id_partita(str(data), avversario)
            # Il link YouTube e' opzionale: se il campo e' vuoto si manda None
            # (colonna nullable a DB) invece della stringa vuota, cosi' le
            # pagine a valle possono usare un semplice test di verita'.
            yt_link_pulito = yt_link.strip() if yt_link else ""
            supabase.table(TABELLA_PARTITE).insert({
                "id": partita_id,
                "data": str(data),
                "avversario": avversario,
                "competizione": competizione,
                "categoria": categoria,
                "yt_link": yt_link_pulito or None
            }).execute()
            st.success(f"✅ Partita '{avversario}' inserita con ID {partita_id} nella categoria '{categoria}'")

# --- SEZIONE 2: Upload CSV eventi ---
st.header("📂 Carica eventi da CSV")

partite = supabase.table(TABELLA_PARTITE).select("id, avversario, data, categoria").order("data", desc=True).execute().data
if not partite:
    st.warning("Nessuna partita trovata, crea prima una nuova partita.")
    st.stop()

partita_scelta = st.selectbox("Seleziona partita", [f"{p['data']} - {p['avversario']} - {p.get('categoria', 'N/A')} ({p['id']})" for p in partite])
file = st.file_uploader("Carica CSV eventi", type=["csv"])

if file and partita_scelta:
    partita_id = partita_scelta.split("(")[-1].strip(")")
    
    # Estrai la categoria dalla partita selezionata
    partita_info = next((p for p in partite if p['id'] == partita_id), None)
    categoria = partita_info.get('categoria', 'Prima Squadra') if partita_info else 'Prima Squadra'
    
    # Forza le colonne problematiche a essere stringhe per evitare errori PyArrow
    dtype_dict = {
        'Dove': str,
        'Field Position': str,
        'Posizione': str,
        'Position': str,
        'Chi': str,
        'Esito': str,
        'Piede': str,
        'Squadra': str,
        'Lato': str
    }
    df_raw = pd.read_csv(file, dtype=dtype_dict, sep=rileva_separatore(file))

    # ✅ Preprocessing con categoria
    df = preprocess_eventi(df_raw, partita_id, categoria)
    eventi_data = df.to_dict(orient="records")

    st.write("Anteprima dati preprocessati:")
    st.dataframe(df.head(20))

    if st.button("Carica eventi nel DB"):
        batch_size = 500
        for i in range(0, len(eventi_data), batch_size):
            supabase.table(TABELLA_EVENTI).insert(eventi_data[i:i+batch_size]).execute()
        st.success(f"✅ Caricati {len(eventi_data)} eventi per la partita {partita_id}")

# --- SEZIONE 3: Elimina eventi partita ---
st.header("🗑️ Elimina eventi partita")

# Selectbox per selezionare la partita di cui eliminare gli eventi
partita_elimina = st.selectbox(
    "Seleziona partita di cui eliminare gli eventi", 
    [f"{p['data']} - {p['avversario']} - {p.get('categoria', 'N/A')} ({p['id']})" for p in partite],
    key="elimina_partita"
)

if partita_elimina:
    partita_id_elimina = partita_elimina.split("(")[-1].strip(")")
    
    # Mostra informazioni sulla partita
    partita_info = next((p for p in partite if p['id'] == partita_id_elimina), None)
    if partita_info:
        st.info(f"**Partita selezionata:** {partita_info['data']} - {partita_info['avversario']}")
        
        # Conta gli eventi associati a questa partita
        try:
            eventi_count = supabase.table(TABELLA_EVENTI).select("id", count="exact").eq("partita_id", partita_id_elimina).execute()
            num_eventi = eventi_count.count if eventi_count.count else 0
            st.warning(f"⚠️ Questa partita ha {num_eventi} eventi associati.")
        except Exception as e:
            st.error(f"Errore nel contare gli eventi: {e}")
            num_eventi = "sconosciuto"
    
    # Checkbox di conferma
    conferma_elimina = st.checkbox(
        "Confermo di voler eliminare tutti gli EVENTI di questa partita (la partita rimarrà nel sistema)", 
        key="conferma_elimina"
    )
    
    # Pulsante di eliminazione
    if conferma_elimina and st.button("🗑️ Elimina tutti gli eventi della partita", type="primary"):
        try:
            # Elimina solo tutti gli eventi associati alla partita
            result_eventi = supabase.table(TABELLA_EVENTI).delete().eq("partita_id", partita_id_elimina).execute()
            
            st.success(f"✅ Eliminati con successo tutti gli eventi della partita '{partita_info['avversario']}' (la partita rimane nel sistema)")
            st.balloons()
            
            # Ricarica la pagina per aggiornare la lista partite
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Errore durante l'eliminazione degli eventi: {e}")
