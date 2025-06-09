import streamlit as st
import pandas as pd
import os

DATA_DIR = "FMP"

def lista_partite(data_dir=DATA_DIR):
    partite = []
    for subdir, dirs, files in os.walk(data_dir):
        for file in files:
            if file == "events.csv":
                rel_path = os.path.relpath(os.path.join(subdir, file), data_dir)
                path_parts = rel_path.split(os.sep)
                if len(path_parts) >= 2:
                    tipo = path_parts[0]
                    avversario = path_parts[1]
                    # Prendi la data se c'è nel file!
                    try:
                        df = pd.read_csv(os.path.join(subdir, file))
                        data = df["Data"].iloc[0] if "Data" in df.columns else ""
                    except:
                        data = ""
                    partite.append({
                        "tipo": tipo,
                        "avversario": avversario,
                        "data": data,
                        "file_path": os.path.join(subdir, file)
                    })
    return sorted(partite, key=lambda x: x['data'], reverse=True)

st.title("Tutte le partite disponibili")

partite = lista_partite()
if not partite:
    st.warning("Nessuna partita trovata.")
else:
    # Visualizzazione card stile griglia (4 per riga)
    n_cols = 4
    for i in range(0, len(partite), n_cols):
        cols = st.columns(n_cols)
        for j, partita in enumerate(partite[i:i+n_cols]):
            with cols[j]:
                st.markdown(f"### {partita['avversario'].title()}")
                st.write(f"{partita['tipo'].capitalize()} — {partita['data']}")
                if st.button("Analizza", key=f"btn_{i}_{j}"):
                    st.session_state["partita_scelta"] = partita

    # Mostra dettaglio della partita selezionata
    partita_scelta = st.session_state.get("partita_scelta", None)
    if partita_scelta:
        st.markdown("---")
        st.subheader(f"Analisi di {partita_scelta['tipo'].capitalize()} vs {partita_scelta['avversario'].title()} — {partita_scelta['data']}")
        df_events = pd.read_csv(partita_scelta["file_path"])

        # Esempio: Tiri in porta, goal, parate ecc. (modifica con i tuoi criteri)
        num_tiri = df_events[df_events["Evento"].str.lower().str.contains("tiro", na=False)].shape[0]
        num_parate = df_events[df_events["Esito"].str.lower().str.contains("parata", na=False)]["Esito"].count() if "Esito" in df_events.columns else 0
        num_goal = df_events[df_events["Evento"].str.lower().str.contains("goal", na=False)].shape[0]
        num_goal_subiti = df_events[df_events["Evento"].str.lower().str.contains("goal subito", na=False)].shape[0]

        st.metric("Tiri Totali", num_tiri)
        st.metric("Parate", num_parate)
        st.metric("Goal Segnati", num_goal)
        st.metric("Goal Subiti", num_goal_subiti)

        with st.expander("Mostra eventi dettagliati"):
            st.dataframe(df_events)

