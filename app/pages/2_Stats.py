import streamlit as st
import pandas as pd
from datetime import datetime
from matplotlib import cm
import matplotlib.pyplot as plt

# Moduli locali
from futsal_analysis.config_supabase import get_supabase_client
from futsal_analysis.utils_time import *
from futsal_analysis.utils_eventi import *
from futsal_analysis.utils_minutaggi import *
from futsal_analysis.pitch_drawer import FutsalPitch
from futsal_analysis.zone_analysis import *
from futsal_analysis.dashboard_utils import render_panoramica_stagione
from futsal_analysis.utils_pdf import (
    PdfImageSection,
    PdfTableSection,
    figure_to_png_bytes,
    generate_pdf_report,
)

st.set_page_config(page_title="Stats Stagione", layout="wide", page_icon="📊")

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
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #1565c0;
    }
    .metric-label {
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
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
    # Cerca "Campionato" come default, altrimenti usa la prima categoria disponibile
    if 'Campionato' in categorie_disponibili:
        st.session_state['categoria_selezionata'] = 'Campionato'
    else:
        st.session_state['categoria_selezionata'] = categorie_disponibili[0] if categorie_disponibili else 'Prima Squadra'

categoria_attiva = st.session_state['categoria_selezionata']

st.header(f"📊 Statistiche di Stagione - {categoria_attiva}")
st.info(f"📂 Categoria attiva: **{categoria_attiva}** (modificabile dalla Homepage)")

# --- Carica tutte le partite FILTRATE PER CATEGORIA ---
res = supabase.table("partite").select("*").eq("categoria", categoria_attiva).order("data", desc=True).execute()
partite = res.data

if not partite:
    st.warning(f"Nessuna partita trovata per la categoria '{categoria_attiva}'.")
    st.stop()

# --- Multi-select per competizione ---
competizioni = sorted(list(set([p['competizione'] for p in partite])))

# Default: Campionato se presente, altrimenti tutte le competizioni
if 'Campionato' in competizioni:
    default_competizioni = ['Campionato']
else:
    default_competizioni = competizioni

competizioni_scelte = st.multiselect(
    "Seleziona competizione",
    competizioni,
    default=default_competizioni,
    key="competizioni_select"
)

if not competizioni_scelte:
    st.warning("Seleziona almeno una competizione per visualizzare le statistiche.")
    st.stop()

# Filtra partite per le competizioni selezionate
partite_filtrate = [p for p in partite if p['competizione'] in competizioni_scelte]

if not partite_filtrate:
    st.warning(f"Nessuna partita trovata per le competizioni selezionate: {', '.join(competizioni_scelte)}.")
    st.stop()

# --- Carica eventi per tutte le partite filtrate ---
competizioni_label = ", ".join(competizioni_scelte)
st.info(f"Caricamento dati per {len(partite_filtrate)} partite nelle competizioni: {competizioni_label}.")

# Carica eventi: una query per ogni partita
partite_ids = [p['id'] for p in partite_filtrate]
eventi_totali = []

with st.spinner("Caricamento eventi in corso..."):
    for partita_id in partite_ids:
        eventi_res = supabase.table("eventi").select("*").eq("partita_id", partita_id).order("posizione").execute()
        if eventi_res.data:
            eventi_totali.extend(eventi_res.data)

if not eventi_totali:
    st.warning("Nessun evento trovato per le partite selezionate.")
    st.stop()

# Crea DataFrame completo
df_all = pd.DataFrame(eventi_totali)

# --- Data cleaning/normalizzazione ---
df_all.columns = df_all.columns.str.strip().str.lower().str.replace(" ", "_")
df_all = df_all.copy()
df_all['dove'] = pd.to_numeric(df_all.get('dove', None), errors='coerce').fillna(0).astype(int)
df_all['Periodo'] = tag_primo_secondo_tempo(df_all)
df_all['tempoEffettivo'] = calcola_tempo_effettivo(df_all)
df_all['tempoReale'] = calcola_tempo_reale(df_all)

# --- PANORAMICA STAGIONE ---
render_panoramica_stagione(df_all, partite_ids)

# --- Calcola report completo per tutti gli eventi ---
st.markdown("---")
report_eventi = calcola_report_completo(df_all)
pdf_table_sections = []
MAX_ROWS_PER_PDF_SECTION = 30

def append_pdf_section(title: str, df: pd.DataFrame):
    if df.empty:
        return
    df_pdf = df.copy()
    if "Portieri" in title:
        cols_da_rimuovere = [
            c for c in df_pdf.columns
            if str(c).strip().lower().replace(" ", "_").startswith("integrazione_portiere")
        ]
        df_pdf = df_pdf.drop(columns=cols_da_rimuovere, errors='ignore')
    if len(df_pdf) > MAX_ROWS_PER_PDF_SECTION:
        df_pdf = df_pdf.head(MAX_ROWS_PER_PDF_SECTION)
    pdf_table_sections.append(PdfTableSection(title, df_pdf))

zone_pdf_context = {
    "report_zona": {},
    "team_att_metrics": [],
    "team_dif_metrics": [],
    "player_metrics": {},
}

# --- Funzioni helper ---

def format_column_names(df):
    """Formatta i nomi delle colonne rimuovendo underscore e capitalizzando"""
    new_columns = {}
    for col in df.columns:
        formatted = col.replace('_', ' ').title().replace(' Per Partita', ' x P')
        new_columns[col] = formatted
    return df.rename(columns=new_columns)

def format_index_names(df):
    """Formatta i nomi delle righe rimuovendo underscore e capitalizzando"""
    new_index = {}
    for idx in df.index:
        if isinstance(idx, tuple):
            formatted = tuple(part.replace('_', ' ').title().replace(' Per Partita', ' x P') for part in idx)
            new_index[idx] = formatted
        elif isinstance(idx, str):
            if ';' in idx:
                parts = [p.strip().replace('_', ' ').title().replace(' Per Partita', ' x P') for p in idx.split(';')]
                formatted = tuple(parts)
                new_index[idx] = formatted
            else:
                formatted = idx.replace('_', ' ').title().replace(' Per Partita', ' x P')
                new_index[idx] = formatted
        else:
            new_index[idx] = str(idx)
    return df.rename(index=new_index)

def render_section(title, data_dict, show_title=True, pdf_title=None):
    if show_title:
        st.markdown(f"**{title}**")
    try:
        df_sec = pd.DataFrame(data_dict).fillna(0).astype(int)
    except Exception:
        df_sec = pd.DataFrame(data_dict).fillna(0)
    
    df_sec = format_column_names(df_sec)
    df_sec = format_index_names(df_sec)
    
    st.dataframe(df_sec, use_container_width=True)
    if pdf_title and not df_sec.empty:
        append_pdf_section(pdf_title, df_sec)

quartetti_columns_to_drop = [
    'angoli',
    'laterali',
    'angoli_subiti',
    'laterali_subiti',
    'ammonizioni',
    'espulsioni',
]

def clean_quartetti_columns(df_input: pd.DataFrame) -> pd.DataFrame:
    if df_input.empty:
        return df_input
    cols_to_drop = [col for col in quartetti_columns_to_drop if col in df_input.columns]
    if cols_to_drop:
        df_input = df_input.drop(columns=cols_to_drop)
    return df_input

# Funzione per aggregare minutaggi di più partite (deve stare prima dell'uso)
def aggrega_minutaggi_partite(partite_ids, df_eventi):
    """
    Calcola i minutaggi per ogni partita e poi li aggrega sommando i secondi totali.
    """
    from collections import defaultdict
    import pandas as pd
    
    # Accumulatori per secondi totali per ogni combinazione
    acc_totale = defaultdict(float)
    acc_primo_tempo = defaultdict(float)
    acc_secondo_tempo = defaultdict(float)
    
    # Durate totali per calcolare le percentuali finali
    durata_totale_tot = 0
    durata_totale_1t = 0
    durata_totale_2t = 0
    
    for p_id in partite_ids:
        # Filtra eventi per questa partita
        df_partita = df_eventi[df_eventi['partita_id'] == p_id].copy()
        if df_partita.empty:
            continue
        
        # Reset degli indici per evitare problemi con loc
        df_partita = df_partita.reset_index(drop=True)
        
        # IMPORTANTE: Ricalcola Periodo, tempoEffettivo e tempoReale per QUESTA partita
        # (non usare quelli calcolati su df_all con tutte le partite mischiate!)
        df_partita['Periodo'] = tag_primo_secondo_tempo(df_partita)
        df_partita['tempoEffettivo'] = calcola_tempo_effettivo(df_partita)
        df_partita['tempoReale'] = calcola_tempo_reale(df_partita)
        
        # Filtra per periodo
        df_1t = df_partita[df_partita['Periodo'] == 'Primo tempo'].reset_index(drop=True)
        df_2t = df_partita[df_partita['Periodo'] == 'Secondo tempo'].reset_index(drop=True)
        
        # Calcola minutaggi per questa partita
        try:
            # Verifica e pulisci i valori di tempoReale prima del calcolo
            def clean_tempo_reale(df):
                """Pulisce e valida i valori di tempoReale"""
                df = df.copy()
                if 'tempoReale' in df.columns:
                    # Funzione per validare e pulire il tempo
                    def validate_time(val):
                        if pd.isna(val) or val == '' or val is None:
                            return "00:00"
                        val_str = str(val).strip()
                        # Rimuovi caratteri non validi (mantieni solo numeri e :)
                        val_str = ''.join(c for c in val_str if c.isdigit() or c == ':')
                        if not val_str or ':' not in val_str:
                            return "00:00"
                        # Verifica formato MM:SS
                        parts = val_str.split(':')
                        if len(parts) != 2:
                            return "00:00"
                        try:
                            mm = int(parts[0])
                            ss = int(parts[1])
                            # Valida i valori
                            if mm < 0 or ss < 0 or ss >= 60:
                                return "00:00"
                            return f"{mm:02d}:{ss:02d}"
                        except (ValueError, TypeError):
                            return "00:00"
                    
                    df['tempoReale'] = df['tempoReale'].apply(validate_time)
                return df
            
            # Pulisci i DataFrame prima di calcolare i minutaggi
            df_partita_clean = clean_tempo_reale(df_partita)
            df_1t_clean = clean_tempo_reale(df_1t)
            df_2t_clean = clean_tempo_reale(df_2t)
            
            minutaggi_partita = calcola_minutaggi(df_partita_clean, df_1t_clean, df_2t_clean)
            
            # Funzione helper per estrarre i secondi da una stringa MM:SS
            def mmss_to_seconds(mmss_str):
                try:
                    parts = mmss_str.split(':')
                    return int(parts[0]) * 60 + int(parts[1])
                except:
                    return 0
            
            # Calcola la durata REALE della partita (non il max dei minutaggi!)
            def calcola_durata_reale(df):
                """Calcola la durata reale sommando i delta tra eventi consecutivi"""
                if df.empty or 'tempoReale' not in df.columns:
                    return 0
                
                def clean_time_value(time_val):
                    if pd.isna(time_val) or time_val == '' or time_val is None:
                        return "00:00"
                    time_str = str(time_val).strip()
                    if not time_str or ':' not in time_str:
                        return "00:00"
                    return time_str
                
                tempo_reale_clean = df['tempoReale'].apply(clean_time_value)
                tempo_reale_next_clean = tempo_reale_clean.shift(-1).fillna("00:00")
                
                try:
                    delta = (
                        pd.to_timedelta("00:" + tempo_reale_next_clean).dt.total_seconds()
                        - pd.to_timedelta("00:" + tempo_reale_clean).dt.total_seconds()
                    ).values
                    import numpy as np
                    return int(np.clip(delta, a_min=0, a_max=None).sum())
                except:
                    return 0
            
            # Aggrega i risultati per ogni periodo
            for periodo, acc_periodo, label in [
                (minutaggi_partita.get('totale', {}), acc_totale, 'totale'),
                (minutaggi_partita.get('primo_tempo', {}), acc_primo_tempo, 'primo_tempo'),
                (minutaggi_partita.get('secondo_tempo', {}), acc_secondo_tempo, 'secondo_tempo')
            ]:
                if not periodo:
                    continue
                
                for cat_name, df_cat in periodo.items():
                    if df_cat.empty:
                        continue
                    
                    # Per ogni riga nel DataFrame della categoria
                    for _, row in df_cat.iterrows():
                        # Crea una chiave unica in base alla categoria
                        if cat_name == "mov4_portieri":
                            key = (cat_name, row['Portiere'])
                        elif cat_name == "mov4_singoli":
                            key = (cat_name, row['Giocatore'])
                        elif cat_name == "mov4_singolo_portiere":
                            key = (cat_name, row['Portiere'], row['Giocatore'])
                        # elif cat_name == "mov4_coppie":  # COMMENTATO
                        #     key = (cat_name, row['Giocatori'])
                        # elif cat_name == "mov4_coppia_portiere":  # COMMENTATO
                        #     key = (cat_name, row['Portiere'], row['Giocatori'])
                        elif cat_name in ["mov4_quartetto", "mov3_senza_portiere", "mov3_con_portiere", "mov5_senza_portiere"]:
                            key = (cat_name, row['Giocatori_movimento'])
                        elif cat_name == "mov4_quartetto_portiere":
                            key = (cat_name, row['Portiere'], row['Giocatori_movimento'])
                        else:
                            continue
                        
                        # Somma i secondi
                        secondi = mmss_to_seconds(row['Minuti_giocati'])
                        acc_periodo[key] += secondi
            
            # Calcola le durate REALI della partita (somma delta tra eventi)
            durata_tot_partita = calcola_durata_reale(df_partita_clean)
            durata_1t_partita = calcola_durata_reale(df_1t_clean)
            durata_2t_partita = calcola_durata_reale(df_2t_clean)
            
            # Aggiungi alle durate totali aggregate
            durata_totale_tot += durata_tot_partita
            durata_totale_1t += durata_1t_partita
            durata_totale_2t += durata_2t_partita
                    
        except Exception as e:
            # Mostra warning solo per errori non banali
            if "empty" not in str(e).lower() and len(df_partita) > 0:
                st.warning(f"⚠️ Errore nel calcolo minutaggi per partita {p_id}: {e}")
            continue
    
    # Converti gli accumulatori in DataFrame
    def acc_to_dataframes(acc, durata_totale):
        dfs = defaultdict(list)
        
        for key, secondi in acc.items():
            cat_name = key[0]
            mmss = f"{int(secondi//60):02}:{int(secondi%60):02}"
            perc = f"{int(round(100 * secondi / durata_totale))}%" if durata_totale > 0 else "0%"
            
            if cat_name == "mov4_portieri":
                dfs[cat_name].append({
                    "Portiere": key[1],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })
            elif cat_name == "mov4_singoli":
                dfs[cat_name].append({
                    "Giocatore": key[1],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })
            elif cat_name == "mov4_singolo_portiere":
                dfs[cat_name].append({
                    "Portiere": key[1],
                    "Giocatore": key[2],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })
            # elif cat_name == "mov4_coppie":  # COMMENTATO
            #     dfs[cat_name].append({
            #         "Giocatori": key[1],
            #         "Minuti_giocati": mmss,
            #         "Percentuale": perc
            #     })
            # elif cat_name == "mov4_coppia_portiere":  # COMMENTATO
            #     dfs[cat_name].append({
            #         "Portiere": key[1],
            #         "Giocatori": key[2],
            #         "Minuti_giocati": mmss,
            #         "Percentuale": perc
            #     })
            elif cat_name in ["mov4_quartetto", "mov3_senza_portiere", "mov3_con_portiere", "mov5_senza_portiere"]:
                dfs[cat_name].append({
                    "Giocatori_movimento": key[1],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })
            elif cat_name == "mov4_quartetto_portiere":
                dfs[cat_name].append({
                    "Portiere": key[1],
                    "Giocatori_movimento": key[2],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })
        
        # Converti in DataFrame e ordina
        return {k: pd.DataFrame(v).sort_values("Minuti_giocati", ascending=False) 
                for k, v in dfs.items()}
    
    return {
        'totale': acc_to_dataframes(acc_totale, durata_totale_tot),
        'primo_tempo': acc_to_dataframes(acc_primo_tempo, durata_totale_1t),
        'secondo_tempo': acc_to_dataframes(acc_secondo_tempo, durata_totale_2t)
    }

# Funzione per normalizzare le statistiche individuali
def normalizza_stats_individuali(df_stats, minutaggi_data, tipo='giocatore'):
    """
    Normalizza le statistiche per 80 minuti (durata reale di una partita completa).
    I minutaggi sono in tempo reale, non effettivo, quindi 80min = partita intera.
    
    Args:
        df_stats: DataFrame con le statistiche grezze
        minutaggi_data: Dict con i minutaggi calcolati
        tipo: 'giocatore' o 'portiere'
    """
    df = df_stats.copy()
    
    # Estrai i minuti giocati da minutaggi_data (formato MM:SS e decimale)
    minuti_dict_mmss = {}  # Per visualizzazione
    minuti_dict_decimal = {}  # Per calcoli
    
    if tipo == 'giocatore':
        if 'mov4_singoli' in minutaggi_data and not minutaggi_data['mov4_singoli'].empty:
            for _, row in minutaggi_data['mov4_singoli'].iterrows():
                giocatore = row['Giocatore']
                mmss = row['Minuti_giocati']
                minuti_dict_mmss[giocatore] = mmss
                try:
                    parts = mmss.split(':')
                    minuti_decimal = int(parts[0]) + int(parts[1]) / 60
                    minuti_dict_decimal[giocatore] = minuti_decimal
                except:
                    minuti_dict_decimal[giocatore] = 0
    elif tipo == 'portiere':
        if 'mov4_portieri' in minutaggi_data and not minutaggi_data['mov4_portieri'].empty:
            for _, row in minutaggi_data['mov4_portieri'].iterrows():
                portiere = row['Portiere']
                mmss = row['Minuti_giocati']
                minuti_dict_mmss[portiere] = mmss
                try:
                    parts = mmss.split(':')
                    minuti_decimal = int(parts[0]) + int(parts[1]) / 60
                    minuti_dict_decimal[portiere] = minuti_decimal
                except:
                    minuti_dict_decimal[portiere] = 0
    
    # Colonne da normalizzare
    colonne_da_normalizzare = [
        'gol_fatti', 'gol_subiti', 'tiri_totali', 'tiri_in_porta_totali', 'tiri_fuori', 
        'tiri_ribattuti', 'palo_traversa', 'palle_perse', 'tiri_ribattuti_noi',
        'palle_recuperate', 'falli_fatti', 'falli_subiti', 'ammonizioni', 'espulsioni',
        'parate', 'lanci', 'lanci_corretti', 'lanci_sbagliati',
        'integrazione_portiere', 'integrazione_portiere_ok', 'integrazione_portiere_ko'
    ]
    
    # Aggiungi colonna con i minuti giocati (formato MM:SS)
    df['minuti_giocati'] = df.index.map(lambda x: minuti_dict_mmss.get(x, "00:00"))
    
    # Normalizza le colonne esistenti per 80 minuti (= partita completa)
    for col in df.columns:
        if col in colonne_da_normalizzare:
            col_norm = f"{col}_per_partita"
            df[col_norm] = df.apply(
                lambda row: round(row[col] / minuti_dict_decimal.get(row.name, 1) * 80, 2) 
                if minuti_dict_decimal.get(row.name, 0) > 0 else 0,
                axis=1
            )
    
    return df

# Funzione per normalizzare le statistiche dei quartetti
def normalizza_stats_quartetti(df_stats, minutaggi_data):
    """
    Normalizza le statistiche dei quartetti per 80 minuti (partita completa).
    """
    df = df_stats.copy()
    
    # Estrai i minuti giocati da minutaggi_data (formato MM:SS e decimale)
    minuti_dict_mmss = {}  # Per visualizzazione
    minuti_dict_decimal = {}  # Per calcoli
    
    if 'mov4_quartetto' in minutaggi_data and not minutaggi_data['mov4_quartetto'].empty:
        for _, row in minutaggi_data['mov4_quartetto'].iterrows():
            quartetto = row['Giocatori_movimento']
            mmss = row['Minuti_giocati']
            minuti_dict_mmss[quartetto] = mmss
            try:
                parts = mmss.split(':')
                minuti_decimal = int(parts[0]) + int(parts[1]) / 60
                minuti_dict_decimal[quartetto] = minuti_decimal
            except:
                minuti_dict_decimal[quartetto] = 0
    
    # Colonne da normalizzare
    colonne_da_normalizzare = [
        'gol_fatti', 'gol_subiti', 'tiri_totali', 'tiri_in_porta', 'tiri_fuori',
        'tiri_ribattuti', 'palo_traversa', 'angoli', 'laterali',
        'tiri_subiti', 'tiri_in_porta_subiti', 'tiri_fuori_subiti',
        'tiri_loro_ribattuti_da_noi', 'angoli_subiti', 'laterali_subiti',
        'palle_perse', 'palle_recuperate', 'ripartenze', 'ripartenze_subite',
        'falli_fatti', 'falli_subiti', 'ammonizioni', 'espulsioni'
    ]
    
    # Aggiungi colonna con i minuti giocati (formato MM:SS)
    df['minuti_giocati'] = df.index.map(lambda x: minuti_dict_mmss.get(x, "00:00"))
    
    # Normalizza le colonne esistenti per 80 minuti (= partita completa)
    for col in df.columns:
        if col in colonne_da_normalizzare:
            col_norm = f"{col}_per_partita"
            df[col_norm] = df.apply(
                lambda row: round(row[col] / minuti_dict_decimal.get(row.name, 1) * 80, 2) 
                if minuti_dict_decimal.get(row.name, 0) > 0 else 0,
                axis=1
            )
    
    return df

# --- Calcola minutaggi una volta per tutti i tabs (solo per categorie complete) ---
if categoria_attiva.lower() not in ['u15', 'u17']:
    minutaggi = aggrega_minutaggi_partite(partite_ids, df_all)
else:
    minutaggi = None

# --- TABS DINAMICI BASATI SULLA CATEGORIA ---
# Per u15/u17 nascondiamo Stats Individuali, Stats Quartetti e Minutaggi
if categoria_attiva.lower() in ['u15', 'u17']:
    tabs = st.tabs(["Stats Squadra", "Zone"])
    tab_names = ["Stats Squadra", "Zone"]
else:
    tabs = st.tabs(["Stats Squadra", "Top 5", "Stats Individuali", "Stats Quartetti", "Zone", "Minutaggi"])
    tab_names = ["Stats Squadra", "Top 5", "Stats Individuali", "Stats Quartetti", "Zone", "Minutaggi"]

# === TAB 1: Stats Squadra ===
with tabs[0]:
    st.header("Statistiche di squadra aggregate")
    
    # Sezione Possesso
    with st.expander("⚽ Possesso", expanded=False):
        render_section("Attacco", report_eventi['squadra']['attacco'], show_title=False, pdf_title="Stats Squadra - Possesso Attacco")
    
    # Sezione Non Possesso
    with st.expander("🛡️ Non Possesso", expanded=False):
        render_section("Difesa", report_eventi['squadra']['difesa'], show_title=False, pdf_title="Stats Squadra - Non Possesso Difesa")
    
    # Sezione Perse/Recuperate
    with st.expander("🔄 Perse/Recuperate", expanded=False):
        palle_stats = {}
        for periodo, data in report_eventi['squadra']['attacco'].items():
            if periodo == 'Totale':
                df_periodo = df_all
            elif periodo == '1T':
                df_periodo = df_all[df_all['Periodo'] == 'Primo tempo']
            elif periodo == '2T':
                df_periodo = df_all[df_all['Periodo'] == 'Secondo tempo']
            else:
                df_periodo = df_all
            
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
        
        render_section("Perse/Recuperate", palle_stats, show_title=False, pdf_title="Stats Squadra - Perse e Recuperate")
    
    # Sezione Falli
    with st.expander("⚠️ Falli", expanded=False):
        render_section("Falli", report_eventi['squadra']['falli'], show_title=False, pdf_title="Stats Squadra - Falli")
    
    # Sezione Portieri
    with st.expander("🥅 Portieri", expanded=False):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            render_section("Noi", report_eventi['squadra']['portieri_noi'], pdf_title="Stats Squadra - Portieri Noi")
        with col_p2:
            render_section("Loro", report_eventi['squadra']['portieri_loro'], pdf_title="Stats Squadra - Portieri Loro")

# === TAB 2: Top 5 ===
if "Top 5" in tab_names:
    with tabs[tab_names.index("Top 5")]:
        st.header("🏆 Top 5")
        
        # Lista delle statistiche da mostrare (facilmente modificabile)
        # Formato: (chiave_statistica, 'Nome Visualizzato', è_calcolata)
        # Se è_calcolata=True, la statistica viene calcolata invece di essere letta direttamente
        top5_stats = [
            ('gol_fatti', 'Gol', False),
            ('tiri_totali', 'Tiri', False),
            ('tiri_in_porta_totali', 'Tiri in Porta', False),
            ('precisione_tiri', 'Precisione Tiri (%)', True),  # Calcolata: tiri_in_porta / tiri_totali * 100
            ('tiri_fuori', 'Tiri Fuori', False),
            ('tiri_ribattuti', 'Tiri Ribattuti', False),
            ('palo_traversa', 'Palo/Traversa', False),
            ('palle_perse', 'Palle Perse', False),
            ('tiri_ribattuti_noi', 'Tiri Ribattuti da Noi', False),
            ('palle_recuperate', 'Palle Recuperate', False),
            ('falli_fatti', 'Falli Fatti', False),
            ('falli_subiti', 'Falli Subiti', False),
            # ('ammonizioni', 'Ammonizioni', False),
            # ('espulsioni', 'Espulsioni', False),
        ]
        
        # Estrai i dati individuali totali
        stats_individuali = report_eventi['individuali_split']['Totale']
        
        # Raccogli tutte le tabelle da visualizzare
        tabelle_da_mostrare = []
        
        # Genera una tabella per ogni statistica
        for stat_key, stat_label, is_calculated in top5_stats:
            # Raccogli i valori per tutti i giocatori per questa statistica
            giocatori_stats = []
            for giocatore, stats in stats_individuali.items():
                if is_calculated:
                    # Calcola la precisione di tiri
                    if stat_key == 'precisione_tiri':
                        tiri_totali = stats.get('tiri_totali', 0)
                        tiri_in_porta = stats.get('tiri_in_porta_totali', 0)
                        if tiri_totali > 0:
                            precisione = round((tiri_in_porta / tiri_totali) * 100, 1)
                            giocatori_stats.append({
                                'Giocatore': giocatore.title(),
                                stat_label: precisione
                            })
                else:
                    # Statistica diretta
                    if stat_key in stats:
                        valore = stats[stat_key]
                        if pd.notna(valore) and valore > 0:  # Solo giocatori con valore > 0
                            giocatori_stats.append({
                                'Giocatore': giocatore.title(),
                                stat_label: int(valore)
                            })
            
            # Se ci sono dati, crea la tabella Top 5
            if giocatori_stats:
                df_top5 = pd.DataFrame(giocatori_stats)
                # Ordina per valore decrescente e prendi i top 5
                df_top5 = df_top5.sort_values(by=stat_label, ascending=False).head(5).reset_index(drop=True)
                # Aggiungi colonna Posizione
                df_top5.insert(0, 'Posizione', range(1, len(df_top5) + 1))
                
                # Salva per visualizzazione successiva
                tabelle_da_mostrare.append((stat_label, df_top5))
        
        # Mostra le tabelle in layout a 4 colonne
        for i in range(0, len(tabelle_da_mostrare), 4):
            cols = st.columns(4)
            for j, (stat_label, df_top5) in enumerate(tabelle_da_mostrare[i:i+4]):
                with cols[j]:
                    st.markdown(f"**{stat_label}**")
                    st.dataframe(df_top5, use_container_width=True, hide_index=True)
                    if not df_top5.empty:
                        append_pdf_section(f"Top 5 - {stat_label}", df_top5)

# === TAB 3: Stats Individuali ===
if "Stats Individuali" in tab_names:
    with tabs[tab_names.index("Stats Individuali")]:
        st.header("Statistiche individuali giocatori aggregate")
        
        def reorder_columns_gol(df):
            """Riordina le colonne per mettere gol_subiti subito dopo gol_fatti"""
            if df.empty:
                return df
            cols = list(df.columns)
            if 'gol_fatti' in cols and 'gol_subiti' in cols:
                # Trova l'indice di gol_fatti
                idx_gol_fatti = cols.index('gol_fatti')
                # Rimuovi gol_subiti dalla sua posizione attuale
                cols.remove('gol_subiti')
                # Inserisci gol_subiti subito dopo gol_fatti
                cols.insert(idx_gol_fatti + 1, 'gol_subiti')
                return df[cols]
            return df
        
        with st.expander("👥 Giocatori - Totale", expanded=False):
            df_tot = pd.DataFrame(report_eventi['individuali_split']['Totale']).T
            # Normalizza le statistiche
            df_tot = normalizza_stats_individuali(df_tot, minutaggi['totale'], tipo='giocatore')
            # Riordina colonne: metti minuti_giocati all'inizio, poi stats grezze (con gol_subiti dopo gol_fatti), poi normalizzate
            cols_grezze = [c for c in df_tot.columns if c != 'minuti_giocati' and '_per_partita' not in c]
            df_temp = df_tot[cols_grezze]
            df_temp = reorder_columns_gol(df_temp)
            cols_grezze_ordinate = list(df_temp.columns)
            cols = ['minuti_giocati'] + cols_grezze_ordinate + [c for c in df_tot.columns if '_per_partita' in c]
            # Riordina anche le colonne normalizzate (gol_subiti_per_partita dopo gol_fatti_per_partita)
            cols_norm = [c for c in cols if '_per_partita' in c]
            if 'gol_fatti_per_partita' in cols_norm and 'gol_subiti_per_partita' in cols_norm:
                idx_gol_fatti_norm = cols_norm.index('gol_fatti_per_partita')
                cols_norm.remove('gol_subiti_per_partita')
                cols_norm.insert(idx_gol_fatti_norm + 1, 'gol_subiti_per_partita')
            cols = ['minuti_giocati'] + cols_grezze_ordinate + cols_norm
            df_tot = df_tot[cols]
            df_tot = format_column_names(df_tot)
            df_tot = format_index_names(df_tot)
            st.dataframe(df_tot, use_container_width=True)
            if not df_tot.empty:
                append_pdf_section("Stats Individuali - Totale", df_tot)
        
        with st.expander("👥 Giocatori - Primo Tempo", expanded=False):
            df_1t = pd.DataFrame(report_eventi['individuali_split']['1T']).T
            df_1t = normalizza_stats_individuali(df_1t, minutaggi['primo_tempo'], tipo='giocatore')
            cols_grezze = [c for c in df_1t.columns if c != 'minuti_giocati' and '_per_partita' not in c]
            df_temp = df_1t[cols_grezze]
            df_temp = reorder_columns_gol(df_temp)
            cols_grezze_ordinate = list(df_temp.columns)
            cols_norm = [c for c in df_1t.columns if '_per_partita' in c]
            if 'gol_fatti_per_partita' in cols_norm and 'gol_subiti_per_partita' in cols_norm:
                idx_gol_fatti_norm = cols_norm.index('gol_fatti_per_partita')
                cols_norm.remove('gol_subiti_per_partita')
                cols_norm.insert(idx_gol_fatti_norm + 1, 'gol_subiti_per_partita')
            cols = ['minuti_giocati'] + cols_grezze_ordinate + cols_norm
            df_1t = df_1t[cols]
            df_1t = format_column_names(df_1t)
            df_1t = format_index_names(df_1t)
            st.dataframe(df_1t, use_container_width=True)
            if not df_1t.empty:
                append_pdf_section("Stats Individuali - Primo Tempo", df_1t)
        
        with st.expander("👥 Giocatori - Secondo Tempo", expanded=False):
            df_2t = pd.DataFrame(report_eventi['individuali_split']['2T']).T
            df_2t = normalizza_stats_individuali(df_2t, minutaggi['secondo_tempo'], tipo='giocatore')
            cols_grezze = [c for c in df_2t.columns if c != 'minuti_giocati' and '_per_partita' not in c]
            df_temp = df_2t[cols_grezze]
            df_temp = reorder_columns_gol(df_temp)
            cols_grezze_ordinate = list(df_temp.columns)
            cols_norm = [c for c in df_2t.columns if '_per_partita' in c]
            if 'gol_fatti_per_partita' in cols_norm and 'gol_subiti_per_partita' in cols_norm:
                idx_gol_fatti_norm = cols_norm.index('gol_fatti_per_partita')
                cols_norm.remove('gol_subiti_per_partita')
                cols_norm.insert(idx_gol_fatti_norm + 1, 'gol_subiti_per_partita')
            cols = ['minuti_giocati'] + cols_grezze_ordinate + cols_norm
            df_2t = df_2t[cols]
            df_2t = format_column_names(df_2t)
            df_2t = format_index_names(df_2t)
            st.dataframe(df_2t, use_container_width=True)
            if not df_2t.empty:
                append_pdf_section("Stats Individuali - Secondo Tempo", df_2t)

        st.header("Statistiche portieri individuali aggregate")
        
        with st.expander("🥅 Portieri - Totale", expanded=False):
            df_port_tot = pd.DataFrame(report_eventi['portieri_individuali_split']['Totale']).T
            df_port_tot = normalizza_stats_individuali(df_port_tot, minutaggi['totale'], tipo='portiere')
            cols = ['minuti_giocati'] + [c for c in df_port_tot.columns if c != 'minuti_giocati' and '_per_partita' not in c] + [c for c in df_port_tot.columns if '_per_partita' in c]
            df_port_tot = df_port_tot[cols]
            df_port_tot = format_column_names(df_port_tot)
            df_port_tot = format_index_names(df_port_tot)
            st.dataframe(df_port_tot, use_container_width=True)
            if not df_port_tot.empty:
                append_pdf_section("Stats Portieri Individuali - Totale", df_port_tot)
        
        with st.expander("🥅 Portieri - Primo Tempo", expanded=False):
            df_port_1t = pd.DataFrame(report_eventi['portieri_individuali_split']['1T']).T
            df_port_1t = normalizza_stats_individuali(df_port_1t, minutaggi['primo_tempo'], tipo='portiere')
            cols = ['minuti_giocati'] + [c for c in df_port_1t.columns if c != 'minuti_giocati' and '_per_partita' not in c] + [c for c in df_port_1t.columns if '_per_partita' in c]
            df_port_1t = df_port_1t[cols]
            df_port_1t = format_column_names(df_port_1t)
            df_port_1t = format_index_names(df_port_1t)
            st.dataframe(df_port_1t, use_container_width=True)
            if not df_port_1t.empty:
                append_pdf_section("Stats Portieri Individuali - Primo Tempo", df_port_1t)
        
        with st.expander("🥅 Portieri - Secondo Tempo", expanded=False):
            df_port_2t = pd.DataFrame(report_eventi['portieri_individuali_split']['2T']).T
            df_port_2t = normalizza_stats_individuali(df_port_2t, minutaggi['secondo_tempo'], tipo='portiere')
            cols = ['minuti_giocati'] + [c for c in df_port_2t.columns if c != 'minuti_giocati' and '_per_partita' not in c] + [c for c in df_port_2t.columns if '_per_partita' in c]
            df_port_2t = df_port_2t[cols]
            df_port_2t = format_column_names(df_port_2t)
            df_port_2t = format_index_names(df_port_2t)
            st.dataframe(df_port_2t, use_container_width=True)
            if not df_port_2t.empty:
                append_pdf_section("Stats Portieri Individuali - Secondo Tempo", df_port_2t)

# === TAB 4: Stats Quartetti ===
if "Stats Quartetti" in tab_names:
    with tabs[tab_names.index("Stats Quartetti")]:
        st.header("Statistiche per quartetti aggregate")
        
        report_quartetti = calcola_report_quartetti_completo(df_all)
        report_quinto_uomo = calcola_report_quinto_uomo_completo(df_all)
        
        with st.expander("👥 Quartetti - Totale", expanded=False):
            if report_quartetti['Totale']:
                df_quartetti_tot = pd.DataFrame(report_quartetti['Totale']).T
                df_quartetti_tot.index = [tuple(idx.split(';')) if ';' in str(idx) else idx for idx in df_quartetti_tot.index]
                df_quartetti_tot = normalizza_stats_quartetti(df_quartetti_tot, minutaggi['totale'])
                cols = ['minuti_giocati'] + [c for c in df_quartetti_tot.columns if c != 'minuti_giocati' and '_per_partita' not in c] + [c for c in df_quartetti_tot.columns if '_per_partita' in c]
                df_quartetti_tot = df_quartetti_tot[cols]
                df_quartetti_tot = format_column_names(df_quartetti_tot)
                df_quartetti_tot = format_index_names(df_quartetti_tot)
                st.dataframe(df_quartetti_tot, use_container_width=True)
                if not df_quartetti_tot.empty:
                    df_quartetti_tot_pdf = clean_quartetti_columns(df_quartetti_tot.copy())
                    append_pdf_section("Stats Quartetti - Totale", df_quartetti_tot_pdf)
            else:
                st.info("Nessun quartetto trovato.")
        
        with st.expander("👥 Quartetti - Primo Tempo", expanded=False):
            if report_quartetti['1T']:
                df_quartetti_1t = pd.DataFrame(report_quartetti['1T']).T
                df_quartetti_1t.index = [tuple(idx.split(';')) if ';' in str(idx) else idx for idx in df_quartetti_1t.index]
                df_quartetti_1t = normalizza_stats_quartetti(df_quartetti_1t, minutaggi['primo_tempo'])
                cols = ['minuti_giocati'] + [c for c in df_quartetti_1t.columns if c != 'minuti_giocati' and '_per_partita' not in c] + [c for c in df_quartetti_1t.columns if '_per_partita' in c]
                df_quartetti_1t = df_quartetti_1t[cols]
                df_quartetti_1t = format_column_names(df_quartetti_1t)
                df_quartetti_1t = format_index_names(df_quartetti_1t)
                st.dataframe(df_quartetti_1t, use_container_width=True)
                # Non aggiungere al PDF - solo Totale per i quartetti (come in 1_Partite.py)
            else:
                st.info("Nessun quartetto trovato nel primo tempo.")
        
        with st.expander("👥 Quartetti - Secondo Tempo", expanded=False):
            if report_quartetti['2T']:
                df_quartetti_2t = pd.DataFrame(report_quartetti['2T']).T
                df_quartetti_2t.index = [tuple(idx.split(';')) if ';' in str(idx) else idx for idx in df_quartetti_2t.index]
                df_quartetti_2t = normalizza_stats_quartetti(df_quartetti_2t, minutaggi['secondo_tempo'])
                cols = ['minuti_giocati'] + [c for c in df_quartetti_2t.columns if c != 'minuti_giocati' and '_per_partita' not in c] + [c for c in df_quartetti_2t.columns if '_per_partita' in c]
                df_quartetti_2t = df_quartetti_2t[cols]
                df_quartetti_2t = format_column_names(df_quartetti_2t)
                df_quartetti_2t = format_index_names(df_quartetti_2t)
                st.dataframe(df_quartetti_2t, use_container_width=True)
                # Non aggiungere al PDF - solo Totale per i quartetti (come in 1_Partite.py)
            else:
                st.info("Nessun quartetto trovato nel secondo tempo.")
        
        st.header("Statistiche quinto uomo aggregate")
        
        with st.expander("👤 Quinto Uomo - Totale", expanded=False):
            if report_quinto_uomo['Totale']:
                df_quinto_tot = pd.DataFrame(report_quinto_uomo['Totale']).T
                df_quinto_tot = clean_quartetti_columns(df_quinto_tot)
                df_quinto_tot = format_column_names(df_quinto_tot)
                df_quinto_tot = format_index_names(df_quinto_tot)
                st.dataframe(df_quinto_tot, use_container_width=True)
                if not df_quinto_tot.empty:
                    append_pdf_section("Quinto Uomo - Totale", df_quinto_tot)
            else:
                st.info("Nessuna situazione con quinto uomo trovata.")
        
        with st.expander("👤 Quinto Uomo - Primo Tempo", expanded=False):
            if report_quinto_uomo['1T']:
                df_quinto_1t = pd.DataFrame(report_quinto_uomo['1T']).T
                df_quinto_1t = clean_quartetti_columns(df_quinto_1t)
                df_quinto_1t = format_column_names(df_quinto_1t)
                df_quinto_1t = format_index_names(df_quinto_1t)
                st.dataframe(df_quinto_1t, use_container_width=True)
                if not df_quinto_1t.empty:
                    append_pdf_section("Quinto Uomo - Primo Tempo", df_quinto_1t)
            else:
                st.info("Nessuna situazione con quinto uomo trovata nel primo tempo.")
        
        with st.expander("👤 Quinto Uomo - Secondo Tempo", expanded=False):
            if report_quinto_uomo['2T']:
                df_quinto_2t = pd.DataFrame(report_quinto_uomo['2T']).T
                df_quinto_2t = clean_quartetti_columns(df_quinto_2t)
                df_quinto_2t = format_column_names(df_quinto_2t)
                df_quinto_2t = format_index_names(df_quinto_2t)
                st.dataframe(df_quinto_2t, use_container_width=True)
                if not df_quinto_2t.empty:
                    append_pdf_section("Quinto Uomo - Secondo Tempo", df_quinto_2t)
            else:
                st.info("Nessuna situazione con quinto uomo trovata nel secondo tempo.")

# === TAB Zone ===
with tabs[tab_names.index("Zone")]:
    st.header("Analisi per zone di campo aggregate")
    campo = FutsalPitch()
    report_zona = calcola_report_zona(df_all)
    zone_pdf_context["report_zona"] = report_zona

    with st.expander("🏆 Analisi Zone di Squadra", expanded=False):
        st.subheader("Statistiche di squadra per zona")
        per_side_team = st.checkbox("Mostra split per lato (Sx/Dx)", value=True, key="zona_team_per_side")
        zone_pdf_context["team_per_side"] = per_side_team
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Attacco")
            zone_attacco = report_zona['squadra']['attacco']
            if zone_attacco:
                first_zone = next(iter(zone_attacco.values()))
                metriche_attacco = ['gol_fatti', 'tiri_totali', 'tiri_in_porta_totali', 'tiri_ribattuti', 'tiri_fuori', 'palo_traversa', 'laterali', 'palle_perse']
                stat_keys_att_sel = st.multiselect(
                    "Statistiche attacco (squadra)",
                    metriche_attacco,
                    default=metriche_attacco[:3],
                    key="zona_stats_attacco_squadra"
                )
                if stat_keys_att_sel:
                    zone_pdf_context["team_att_metrics"] = stat_keys_att_sel
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
                metriche_difesa = ['gol_subiti', 'tiri_totali_subiti', 'tiri_in_porta_totali_subiti', 'tiri_ribattuti_da_noi', 'tiri_fuori_loro', 'palo_traversa_loro', 'laterale_loro', 'palle_recuperate']
                stat_keys_dif_sel = st.multiselect(
                    "Statistiche difesa (squadra)",
                    metriche_difesa,
                    default=metriche_difesa[:3],
                    key="zona_stats_difesa_squadra"
                )
                if stat_keys_dif_sel:
                    zone_pdf_context["team_dif_metrics"] = stat_keys_dif_sel
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

    # Per u15/u17 non mostriamo l'analisi zonale individuale (non abbiamo dati dei singoli giocatori)
    if categoria_attiva.lower() not in ['u15', 'u17']:
        with st.expander("👤 Analisi Zone Individuali", expanded=False):
            st.subheader("Statistiche individuali per zona")
            per_side_player = st.checkbox("Mostra split per lato (Sx/Dx) – giocatore", value=True, key="zona_player_per_side")
            zone_pdf_context["player_per_side"] = per_side_player
            giocatori = sorted({
                g for zona in report_zona['individuali'].values()
                for g in zona.keys() if g.strip()
            })
            
            if giocatori:
                player_att_metrics_all = ['gol_fatti', 'tiri_totali', 'tiri_in_porta_totali', 'tiri_ribattuti', 'tiri_fuori', 'palo_traversa', 'palle_perse']
                player_dif_metrics_all = ['tiri_ribattuti_noi', 'palle_recuperate', 'falli_subiti']

                player_metrics_map = {}
                for giocatore in giocatori:
                    sample_stats = None
                    for zona in report_zona['individuali'].values():
                        if giocatore in zona:
                            sample_stats = zona[giocatore]
                            break
                    if sample_stats:
                        att_metrics = [m for m in player_att_metrics_all if m in sample_stats]
                        dif_metrics = [m for m in player_dif_metrics_all if m in sample_stats]
                    else:
                        att_metrics = []
                        dif_metrics = []
                    player_metrics_map[giocatore] = {"attacco": att_metrics, "difesa": dif_metrics}

                # Per il PDF includi tutti i giocatori (non solo quello selezionato nella UI)
                zone_pdf_context["player_metrics"] = player_metrics_map

                giocatore_scelto = st.selectbox("Scegli giocatore", giocatori, key="zona_giocatore")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"#### Attacco – {giocatore_scelto}")
                    metriche_attacco_gioc = player_metrics_map.get(giocatore_scelto, {}).get("attacco", [])

                    stat_keys_att_gioc_sel = st.multiselect(
                        "Statistiche attacco (giocatore)",
                        metriche_attacco_gioc,
                        default=metriche_attacco_gioc[:3],
                        key="zona_stats_attacco_gioc"
                    )
                    if stat_keys_att_gioc_sel:
                        zone_pdf_context.setdefault("player_metrics", {}).setdefault(giocatore_scelto, {})["attacco"] = stat_keys_att_gioc_sel

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
                    metriche_difesa_gioc = player_metrics_map.get(giocatore_scelto, {}).get("difesa", [])

                    stat_keys_dif_gioc_sel = st.multiselect(
                        "Statistiche difesa (giocatore)",
                        metriche_difesa_gioc,
                        default=metriche_difesa_gioc[:3],
                        key="zona_stats_difesa_gioc"
                    )
                    if stat_keys_dif_gioc_sel:
                        zone_pdf_context.setdefault("player_metrics", {}).setdefault(giocatore_scelto, {})["difesa"] = stat_keys_dif_gioc_sel

                    if stat_keys_dif_gioc_sel:
                        fig, ax = draw_player_metric_per_zone(
                            report_zona['individuali'], campo, stat_keys_dif_gioc_sel,
                            chi=giocatore_scelto,
                            title=f"Difesa per zona – {giocatore_scelto}",
                            cmap=cm.BuPu,
                            per_side=per_side_player
                        )
                        st.pyplot(fig)
            else:
                st.info("Nessun giocatore trovato.")

# === TAB Minutaggi ===
if "Minutaggi" in tab_names:
    with tabs[tab_names.index("Minutaggi")]:
        st.header("Minutaggi aggregati")
        
        # I minutaggi sono già stati calcolati prima dei tabs (variabile `minutaggi`)

        categorie_viste = [
            ("mov4_portieri", "Portieri"),
            ("mov4_singoli", "Singoli"),
            # ("mov4_coppie", "Coppie di movimento"),  # COMMENTATO - mantenere solo singoli e quartetti
            ("mov4_quartetto", "Quartetto"),
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
                        if not df_minutaggi.empty:
                            # Escludi Minutaggi - Quartetti per Primo tempo e Secondo tempo, mantieni solo Totale
                            if titolo == "Quartetto" and periodo != "totale":
                                continue
                            append_pdf_section(f"Minutaggi - {titolo} ({label_to_title.get(periodo, periodo)})", df_minutaggi)

st.markdown("---")
st.subheader("Esporta report stagione")

has_zone_pdf_content = bool(zone_pdf_context.get("team_att_metrics") or zone_pdf_context.get("team_dif_metrics") or zone_pdf_context.get("player_metrics"))
if pdf_table_sections or has_zone_pdf_content:
    if st.button("📄 Genera PDF", key="generate_stats_pdf"):
        with st.spinner("Generazione report PDF in corso..."):
            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            export_title = f"Report Stagione - {categoria_attiva} ({competizioni_label})"
            image_sections = []

            def metric_label(name: str) -> str:
                return name.replace('_', ' ').title()

            zona_report = zone_pdf_context.get("report_zona", {})
            per_side_team_pdf = zone_pdf_context.get("team_per_side", True)
            per_side_player_pdf = zone_pdf_context.get("player_per_side", True)

            for metric in zone_pdf_context.get("team_att_metrics", []):
                try:
                    fig, _ = draw_team_metric_per_zone(
                        zona_report,
                        FutsalPitch(),
                        [metric],
                        team_key="attacco",
                        title=f"Attacco - {metric_label(metric)}",
                        cmap=cm.Reds,
                        per_side=per_side_team_pdf,
                    )
                    fig.set_size_inches(4.0, 3.0)
                    image_sections.append(
                        PdfImageSection(
                            f"Zone Squadra Attacco - {metric_label(metric)}",
                            figure_to_png_bytes(fig),
                            max_width=320,
                        )
                    )
                    plt.close(fig)
                except Exception:
                    continue

            for metric in zone_pdf_context.get("team_dif_metrics", []):
                try:
                    fig, _ = draw_team_metric_per_zone(
                        zona_report,
                        FutsalPitch(),
                        [metric],
                        team_key="difesa",
                        title=f"Difesa - {metric_label(metric)}",
                        cmap=cm.Blues,
                        per_side=per_side_team_pdf,
                    )
                    fig.set_size_inches(4.0, 3.0)
                    image_sections.append(
                        PdfImageSection(
                            f"Zone Squadra Difesa - {metric_label(metric)}",
                            figure_to_png_bytes(fig),
                            max_width=320,
                        )
                    )
                    plt.close(fig)
                except Exception:
                    continue

            zona_individuali = zona_report.get("individuali", {})
            for giocatore, metriche in zone_pdf_context.get("player_metrics", {}).items():
                for metric in metriche.get("attacco", []):
                    try:
                        fig, _ = draw_player_metric_per_zone(
                            zona_individuali,
                            FutsalPitch(),
                            [metric],
                            chi=giocatore,
                            title=f"{giocatore} - Attacco {metric_label(metric)}",
                            cmap=cm.OrRd,
                            per_side=per_side_player_pdf,
                        )
                        fig.set_size_inches(4.0, 3.0)
                        image_sections.append(
                            PdfImageSection(
                                f"Zone {giocatore} Attacco - {metric_label(metric)}",
                                figure_to_png_bytes(fig),
                                max_width=320,
                            )
                        )
                        plt.close(fig)
                    except Exception:
                        continue

                for metric in metriche.get("difesa", []):
                    try:
                        fig, _ = draw_player_metric_per_zone(
                            zona_individuali,
                            FutsalPitch(),
                            [metric],
                            chi=giocatore,
                            title=f"{giocatore} - Difesa {metric_label(metric)}",
                            cmap=cm.BuPu,
                            per_side=per_side_player_pdf,
                        )
                        fig.set_size_inches(4.0, 3.0)
                        image_sections.append(
                            PdfImageSection(
                                f"Zone {giocatore} Difesa - {metric_label(metric)}",
                                figure_to_png_bytes(fig),
                                max_width=320,
                            )
                        )
                        plt.close(fig)
                    except Exception:
                        continue

            pdf_bytes = generate_pdf_report(
                export_title,
                table_sections=pdf_table_sections,
                image_sections=image_sections,
                compact_tables=True,
            )

        st.download_button(
            "⬇️ Scarica PDF",
            data=pdf_bytes,
            file_name=f"report_stats_{file_timestamp}.pdf",
            mime="application/pdf",
            key="download_stats_pdf",
        )
else:
    st.info("Nessun dato disponibile per l'esportazione PDF.")
