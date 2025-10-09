import streamlit as st
import pandas as pd
from matplotlib import cm
import matplotlib.pyplot as plt

# Moduli locali
from futsal_analysis.config_supabase import get_supabase_client
from futsal_analysis.utils_time import *
from futsal_analysis.utils_eventi import *
from futsal_analysis.utils_minutaggi import *
from futsal_analysis.pitch_drawer import FutsalPitch
from futsal_analysis.zone_analysis import *

st.set_page_config(page_title="Analisi Partite", layout="wide", page_icon="⚽")

# CSS per ridurre la grandezza del font
st.markdown("""
<style>
    .main .block-container {
        font-size: 14px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2em !important;
    }
    .stMarkdown {
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- VERIFICA CATEGORIA SELEZIONATA ---
supabase = get_supabase_client()

# Se non c'è una categoria in session_state, imposta un default
if 'categoria_selezionata' not in st.session_state:
    # Carica le categorie disponibili
    res_all = supabase.table("partite").select("categoria").execute()
    categorie_disponibili = sorted(list(set([p.get('categoria', 'Prima Squadra') for p in res_all.data if p.get('categoria')])))
    st.session_state['categoria_selezionata'] = categorie_disponibili[0] if categorie_disponibili else 'Prima Squadra'

categoria_attiva = st.session_state['categoria_selezionata']

st.header(f"Tutte le partite disponibili - {categoria_attiva}")
st.info(f"📂 Categoria attiva: **{categoria_attiva}** (modificabile dalla Homepage)")

# --- Carica partite FILTRATE PER CATEGORIA ---
res = supabase.table("partite").select("*").eq("categoria", categoria_attiva).order("data", desc=True).execute()
partite = res.data

if not partite:
    st.warning("Nessuna partita trovata.")
    st.stop()

# --- Griglia partite con pulsante Analizza ---
n_cols = 4
for i in range(0, len(partite), n_cols):
    cols = st.columns(n_cols)
    for j, partita in enumerate(partite[i:i+n_cols]):
        with cols[j]:
            st.markdown(f"#### {partita['avversario'].title()}")
            st.write(f"{partita['competizione'].capitalize()} — {partita['data']}")
            if st.button("Analizza", key=f"btn_{i}_{j}"):
                st.session_state["partita_scelta"] = partita["id"]

if "partita_scelta" not in st.session_state:
    st.stop()

partita_id = st.session_state["partita_scelta"]
partita_info = next((p for p in partite if p["id"] == partita_id), None)
st.markdown("---")
# st.subheader(f"Analisi di {partita_info['competizione'].capitalize()} vs {partita_info['avversario'].title()} — {partita_info['data']}")

# --- Carica eventi della partita scelta ---
eventi = supabase.table("eventi").select("*").eq("partita_id", partita_id).order("posizione").execute().data
df = pd.DataFrame(eventi)
if df.empty:
    st.warning("Nessun evento trovato per questa partita.")
    st.stop()

# --- Data cleaning/normalizzazione ---
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.copy()
df['dove'] = pd.to_numeric(df.get('dove', None), errors='coerce').fillna(0).astype(int)
df['Periodo'] = tag_primo_secondo_tempo(df)
df['tempoEffettivo'] = calcola_tempo_effettivo(df)
df['tempoReale'] = calcola_tempo_reale(df)

# --- RISULTATO ---
gol_fatti = len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Noi')])
gol_subiti = len(df[(df['evento'] == 'Gol') & (df['squadra'] == 'Loro')])
st.markdown(f"## FMP **{gol_fatti}** – **{gol_subiti}** {partita_info['avversario'].title()}")

gol_df = df[(df['evento'] == 'Gol') | (df['evento'] == 'Autogol')].copy()
if not gol_df.empty:
    gol_df = gol_df.copy()
    gol_df['Minuto'] = gol_df['tempoEffettivo']  # Usa tempoEffettivo invece di tempoReale
    gol_df['Marcatore'] = gol_df['chi'].fillna('').str.title()
    gol_df['Squadra'] = gol_df['squadra']
    # Ordina per minuto crescente (MM:SS) usando timedelta per evitare ordinamenti lessicografici
    try:
        gol_df['_minuto_td'] = pd.to_timedelta(gol_df['Minuto'].astype(str))
        gol_df = gol_df.sort_values('_minuto_td').drop(columns=['_minuto_td']).reset_index(drop=True)
    except Exception:
        gol_df = gol_df.sort_values('Minuto').reset_index(drop=True)

    # Timeline gol espandibile
    with st.expander("⚽ Timeline Gol", expanded=False):
        # Mostra i gol in ordine cronologico verticale
        for _, row in gol_df.iterrows():
            if row['Squadra'] == 'Noi':
                st.markdown(
                    f"""
                    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding: 6px; background-color: #f0f8ff; border-radius: 4px;'>
                        <span style='font-size: 16px;'>⚽</span>
                        <span style='font-weight: bold; color: #1565c0; font-size: 12px;'>{row['Minuto']}'</span>
                        <span style='color: #1565c0; font-size: 12px;'>{row['Marcatore']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding: 6px; background-color: #fff0f0; border-radius: 4px;'>
                        <span style='font-size: 16px;'>❌</span>
                        <span style='font-weight: bold; color: #d32f2f; font-size: 12px;'>{row['Minuto']}'</span>
                        <span style='color: #d32f2f; font-size: 12px;'>Gol subito</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# --- TABS ---
tabs = st.tabs(["Stats Squadra", "Stats Individuali", "Stats Quartetti", "Zone", "Minutaggi"])

# === TAB 1: Stats Squadra ===
with tabs[0]:
    st.header("Statistiche di squadra")
    report_eventi = calcola_report_completo(df)

    def format_column_names(df):
        """Formatta i nomi delle colonne rimuovendo underscore e capitalizzando"""
        new_columns = {}
        for col in df.columns:
            # Rimuovi underscore e capitalizza ogni parola
            formatted = col.replace('_', ' ').title()
            new_columns[col] = formatted
        return df.rename(columns=new_columns)
    
    def format_index_names(df):
        """Formatta i nomi delle righe rimuovendo underscore e capitalizzando"""
        new_index = {}
        for idx in df.index:
            if isinstance(idx, str):
                formatted = idx.replace('_', ' ').title()
                new_index[idx] = formatted
        return df.rename(index=new_index)

    def render_section(title, data_dict, show_title=True):
        if show_title:
            st.markdown(f"**{title}**")
        try:
            df_sec = pd.DataFrame(data_dict).fillna(0).astype(int)
        except Exception:
            df_sec = pd.DataFrame(data_dict).fillna(0)
        
        # Formatta nomi colonne e righe
        df_sec = format_column_names(df_sec)
        df_sec = format_index_names(df_sec)
        
        st.dataframe(df_sec, use_container_width=True)

    # Sezione Possesso
    with st.expander("⚽ Possesso", expanded=False):
        render_section("Attacco", report_eventi['squadra']['attacco'], show_title=False)
    
    # Sezione Non Possesso
    with st.expander("🛡️ Non Possesso", expanded=False):
        render_section("Difesa", report_eventi['squadra']['difesa'], show_title=False)
    
    # Sezione Perse/Recuperate
    with st.expander("🔄 Perse/Recuperate", expanded=False):
        # Calcola le statistiche per palle perse e recuperate usando la funzione dedicata
        palle_stats = {}
        for periodo, data in report_eventi['squadra']['attacco'].items():
            # Calcola le statistiche per questo periodo
            if periodo == 'Totale':
                df_periodo = df
            elif periodo == '1T':
                df_periodo = df[df['Periodo'] == 'Primo tempo']
            elif periodo == '2T':
                df_periodo = df[df['Periodo'] == 'Secondo tempo']
            else:
                df_periodo = df
            
            # Calcola palle perse e ripartenze per la nostra squadra
            palle_perse = len(df_periodo[(df_periodo['evento'].str.contains('Palla persa', na=False))])
            ripartenze = len(df_periodo[(df_periodo['evento'].str.contains('Ripartenza', na=False)) & (df_periodo['squadra'] == 'Noi')])
            palle_recuperate = len(df_periodo[(df_periodo['evento'].str.contains('Palla recuperata', na=False))])
            ripartenze_loro = len(df_periodo[(df_periodo['evento'].str.contains('Ripartenza', na=False)) & (df_periodo['squadra'] == 'Loro')])
            
            palle_stats[periodo] = {
                'palle_perse': palle_perse,
                'ripartenze': ripartenze,
                'palle_recuperate': palle_recuperate,
                'ripartenze_loro': ripartenze_loro
            }
        
        render_section("Perse/Recuperate", palle_stats, show_title=False)
    
    # Sezione Falli
    with st.expander("⚠️ Falli", expanded=False):
        render_section("Falli", report_eventi['squadra']['falli'], show_title=False)
    
    # Sezione Portieri
    with st.expander("🥅 Portieri", expanded=False):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            render_section("Noi", report_eventi['squadra']['portieri_noi'])
        with col_p2:
            render_section("Loro", report_eventi['squadra']['portieri_loro'])


# === TAB 2: Stats Individuali ===
with tabs[1]:
    st.header("Statistiche individuali giocatori")
    
    # Sezione Giocatori con sezioni espandibili
    with st.expander("👥 Giocatori - Totale", expanded=False):
        df_tot = pd.DataFrame(report_eventi['individuali_split']['Totale']).T
        df_tot = format_column_names(df_tot)
        df_tot = format_index_names(df_tot)
        st.dataframe(df_tot, use_container_width=True)
    
    with st.expander("👥 Giocatori - Primo Tempo", expanded=False):
        df_1t = pd.DataFrame(report_eventi['individuali_split']['1T']).T
        df_1t = format_column_names(df_1t)
        df_1t = format_index_names(df_1t)
        st.dataframe(df_1t, use_container_width=True)
    
    with st.expander("👥 Giocatori - Secondo Tempo", expanded=False):
        df_2t = pd.DataFrame(report_eventi['individuali_split']['2T']).T
        df_2t = format_column_names(df_2t)
        df_2t = format_index_names(df_2t)
        st.dataframe(df_2t, use_container_width=True)

    st.header("Statistiche portieri individuali")
    
    # Sezione Portieri con sezioni espandibili
    with st.expander("🥅 Portieri - Totale", expanded=False):
        df_port_tot = pd.DataFrame(report_eventi['portieri_individuali_split']['Totale']).T
        df_port_tot = format_column_names(df_port_tot)
        df_port_tot = format_index_names(df_port_tot)
        st.dataframe(df_port_tot, use_container_width=True)
    
    with st.expander("🥅 Portieri - Primo Tempo", expanded=False):
        df_port_1t = pd.DataFrame(report_eventi['portieri_individuali_split']['1T']).T
        df_port_1t = format_column_names(df_port_1t)
        df_port_1t = format_index_names(df_port_1t)
        st.dataframe(df_port_1t, use_container_width=True)
    
    with st.expander("🥅 Portieri - Secondo Tempo", expanded=False):
        df_port_2t = pd.DataFrame(report_eventi['portieri_individuali_split']['2T']).T
        df_port_2t = format_column_names(df_port_2t)
        df_port_2t = format_index_names(df_port_2t)
        st.dataframe(df_port_2t, use_container_width=True)

# === TAB 3: Stats Quartetti ===
with tabs[2]:
    st.header("Statistiche per quartetti")
    
    # Calcola le statistiche dei quartetti
    report_quartetti = calcola_report_quartetti_completo(df)
    report_quinto_uomo = calcola_report_quinto_uomo_completo(df)
    
    # Sezione Quartetti
    with st.expander("👥 Quartetti - Totale", expanded=False):
        if report_quartetti['Totale']:
            df_quartetti_tot = pd.DataFrame(report_quartetti['Totale']).T
            # Converti gli indici da stringhe con punti e virgola a tuple
            df_quartetti_tot.index = [tuple(idx.split(';')) if ';' in str(idx) else idx for idx in df_quartetti_tot.index]
            df_quartetti_tot = format_column_names(df_quartetti_tot)
            df_quartetti_tot = format_index_names(df_quartetti_tot)
            st.dataframe(df_quartetti_tot, use_container_width=True)
        else:
            st.info("Nessun quartetto trovato.")
    
    with st.expander("👥 Quartetti - Primo Tempo", expanded=False):
        if report_quartetti['1T']:
            df_quartetti_1t = pd.DataFrame(report_quartetti['1T']).T
            # Converti gli indici da stringhe con punti e virgola a tuple
            df_quartetti_1t.index = [tuple(idx.split(';')) if ';' in str(idx) else idx for idx in df_quartetti_1t.index]
            df_quartetti_1t = format_column_names(df_quartetti_1t)
            df_quartetti_1t = format_index_names(df_quartetti_1t)
            st.dataframe(df_quartetti_1t, use_container_width=True)
        else:
            st.info("Nessun quartetto trovato nel primo tempo.")
    
    with st.expander("👥 Quartetti - Secondo Tempo", expanded=False):
        if report_quartetti['2T']:
            df_quartetti_2t = pd.DataFrame(report_quartetti['2T']).T
            # Converti gli indici da stringhe con punti e virgola a tuple
            df_quartetti_2t.index = [tuple(idx.split(';')) if ';' in str(idx) else idx for idx in df_quartetti_2t.index]
            df_quartetti_2t = format_column_names(df_quartetti_2t)
            df_quartetti_2t = format_index_names(df_quartetti_2t)
            st.dataframe(df_quartetti_2t, use_container_width=True)
        else:
            st.info("Nessun quartetto trovato nel secondo tempo.")
    
    # Sezione Quinto Uomo
    st.header("Statistiche quinto uomo")
    
    with st.expander("👤 Quinto Uomo - Totale", expanded=False):
        if report_quinto_uomo['Totale']:
            df_quinto_tot = pd.DataFrame([report_quinto_uomo['Totale']]).T
            df_quinto_tot = format_column_names(df_quinto_tot)
            df_quinto_tot = format_index_names(df_quinto_tot)
            st.dataframe(df_quinto_tot, use_container_width=True)
        else:
            st.info("Nessuna situazione con quinto uomo trovata.")
    
    with st.expander("👤 Quinto Uomo - Primo Tempo", expanded=False):
        if report_quinto_uomo['1T']:
            df_quinto_1t = pd.DataFrame([report_quinto_uomo['1T']]).T
            df_quinto_1t = format_column_names(df_quinto_1t)
            df_quinto_1t = format_index_names(df_quinto_1t)
            st.dataframe(df_quinto_1t, use_container_width=True)
        else:
            st.info("Nessuna situazione con quinto uomo trovata nel primo tempo.")
    
    with st.expander("👤 Quinto Uomo - Secondo Tempo", expanded=False):
        if report_quinto_uomo['2T']:
            df_quinto_2t = pd.DataFrame([report_quinto_uomo['2T']]).T
            df_quinto_2t = format_column_names(df_quinto_2t)
            df_quinto_2t = format_index_names(df_quinto_2t)
            st.dataframe(df_quinto_2t, use_container_width=True)
        else:
            st.info("Nessuna situazione con quinto uomo trovata nel secondo tempo.")

# === TAB 4: Zone ===

with tabs[3]:
    st.header("Analisi per zone di campo")
    campo = FutsalPitch()
    report_zona = calcola_report_zona(df)

    # --- SEZIONE SQUADRA ---
    with st.expander("🏆 Analisi Zone di Squadra", expanded=False):
        st.subheader("Statistiche di squadra per zona")
        per_side_team = st.checkbox("Mostra split per lato (Sx/Dx)", value=True, key="zona_team_per_side")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Attacco")
            zone_attacco = report_zona['squadra']['attacco']
            if zone_attacco:
                first_zone = next(iter(zone_attacco.values()))
                metriche_attacco = ['gol_fatti', 'tiri_totali', 'tiri_in_porta_totali', 'tiri_ribattuti', 'tiri_fuori', 'palo_traversa', 'laterali'] # list(first_zone.keys())
                stat_keys_att_sel = st.multiselect(
                    "Statistiche attacco (squadra)",
                    metriche_attacco,
                    default=metriche_attacco[:3],
                    key="zona_stats_attacco_squadra"
                )
                if stat_keys_att_sel:
                    fig, ax = draw_team_metric_per_zone(
                        report_zona, campo, stat_keys_att_sel,
                        team_key="attacco",
                        title="Attacco per zona (squadra)",
                        cmap=cm.Reds,
                        per_side=per_side_team
                    )
                    st.pyplot(fig)
            else:
                st.info("Nessun dato di attacco disponibile.")

        with col2:
            st.markdown("#### Difesa")
            zone_difesa = report_zona['squadra']['difesa']
            if zone_difesa:
                first_zone = next(iter(zone_difesa.values()))
                metriche_difesa = ['gol_subiti', 'tiri_totali_subiti', 'tiri_in_porta_totali_subiti', 'tiri_ribattuti_da_noi', 'tiri_fuori_loro', 'palo_traversa_loro', 'laterale_loro'] # list(first_zone.keys())
                stat_keys_dif_sel = st.multiselect(
                    "Statistiche difesa (squadra)",
                    metriche_difesa,
                    default=metriche_difesa[:3],
                    key="zona_stats_difesa_squadra"
                )
                if stat_keys_dif_sel:
                    fig, ax = draw_team_metric_per_zone(
                        report_zona, campo, stat_keys_dif_sel,
                        team_key="difesa",
                        title="Difesa per zona (squadra)",
                        cmap=cm.Blues,
                        per_side=per_side_team
                    )
                    st.pyplot(fig)
            else:
                st.info("Nessun dato di difesa disponibile.")

    # --- SEZIONE INDIVIDUALE ---
    with st.expander("👤 Analisi Zone Individuali", expanded=False):
        st.subheader("Statistiche individuali per zona")
        per_side_player = st.checkbox("Mostra split per lato (Sx/Dx) – giocatore", value=True, key="zona_player_per_side")
        giocatori = sorted({
            g for zona in report_zona['individuali'].values()
            for g in zona.keys() if g.strip()
        })
        giocatore_scelto = st.selectbox("Scegli giocatore", giocatori, key="zona_giocatore")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"#### Attacco – {giocatore_scelto}")
            # Trovo metriche attacco per quel giocatore
            metriche_attacco_gioc = []
            for zona in report_zona['individuali'].values():
                if giocatore_scelto in zona:
                    #metriche_attacco_gioc = [k for k in zona[giocatore_scelto].keys() if "tiro" in k or "palla_persa" in k]
                    metriche_attacco_gioc = ['gol_fatti', 'tiri_totali', 'tiri_in_porta_totali', 'tiri_ribattuti', 'tiri_fuori', 'palo_traversa', 'palle_perse']
                    break

            stat_keys_att_gioc_sel = st.multiselect(
                "Statistiche attacco (giocatore)",
                metriche_attacco_gioc,
                default=metriche_attacco_gioc[:3],
                key="zona_stats_attacco_gioc"
            )

            if stat_keys_att_gioc_sel:
                fig, ax = draw_player_metric_per_zone(
                    report_zona['individuali'], campo, stat_keys_att_gioc_sel,
                    chi=giocatore_scelto,
                    title=f"Attacco per zona – {giocatore_scelto}",
                    cmap=cm.OrRd,
                    per_side=per_side_player
                )
                st.pyplot(fig)

        with col2:
            st.markdown(f"#### Difesa – {giocatore_scelto}")
            # Trovo metriche difesa per quel giocatore
            metriche_difesa_gioc = []
            for zona in report_zona['individuali'].values():
                if giocatore_scelto in zona:
                    # metriche_difesa_gioc = [k for k in zona[giocatore_scelto].keys() if "recuperata" in k or "falli" in k or "ribattuti" in k]
                    metriche_difesa_gioc = ['tiri_ribattuti_noi', 'palle_recuperate', 'falli_subiti']
                    break

            stat_keys_dif_gioc_sel = st.multiselect(
                "Statistiche difesa (giocatore)",
                metriche_difesa_gioc,
                default=metriche_difesa_gioc[:3],
                key="zona_stats_difesa_gioc"
            )

            if stat_keys_dif_gioc_sel:
                fig, ax = draw_player_metric_per_zone(
                    report_zona['individuali'], campo, stat_keys_dif_gioc_sel,
                    chi=giocatore_scelto,
                    title=f"Difesa per zona – {giocatore_scelto}",
                    cmap=cm.BuPu,
                    per_side=per_side_player
                )
                st.pyplot(fig)


# === TAB 5: Minutaggi ===
with tabs[4]:
    st.header("Minutaggi")
    # Durata complessiva, 1T e 2T (tempo reale)
    try:
        dati_durate = calcola_durate(df)
        st.subheader("Durata partita (tempo reale)")
        dati_durate = format_column_names(dati_durate)
        st.dataframe(dati_durate)
    except Exception:
        pass
    df_1t = filtra_per_tempo(df, 'Primo tempo')
    df_2t = filtra_per_tempo(df, 'Secondo tempo')
    minutaggi = calcola_minutaggi(df, df_1t, df_2t)

    # Mostra solo le categorie richieste, con titoli parlanti, raggruppate per periodo in sezioni comprimibili
    categorie_viste = [
        ("mov4_portieri", "Portieri"),
        ("mov4_singoli", "Giocatori di movimento (singoli)")
        ,
        ("mov4_coppie", "Coppie di movimento"),
        ("mov4_quartetto", "Quartetto di movimento"),
        ("mov5_senza_portiere", "Quinto uomo (5 giocatori di movimento)")
    ]

    label_to_title = {
        "totale": "Totale",
        "primo_tempo": "Primo tempo",
        "secondo_tempo": "Secondo tempo",
    }

    for periodo, categorie in minutaggi.items():
        with st.expander(label_to_title.get(periodo, periodo).upper(), expanded=False):
            for key_cat, titolo in categorie_viste:
                if key_cat in categorie and not categorie[key_cat].empty:
                    st.markdown(f"**{titolo}**")
                    df_minutaggi = categorie[key_cat].copy()
                    df_minutaggi = format_column_names(df_minutaggi)
                    st.dataframe(df_minutaggi)
