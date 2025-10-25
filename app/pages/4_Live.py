import streamlit as st
import pandas as pd
from futsal_analysis.config_supabase import get_supabase_client
from futsal_analysis.utils_eventi import calcola_palle_recuperate_perse, calcola_attacco, calcola_difesa, calcola_report_completo

# Page configuration
st.set_page_config(
    page_title="Live Stats - 420MOOD",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Live")

@st.cache_data(ttl=30)  # Cache for 30 seconds to avoid too many API calls
def get_live_data():
    """Fetch live data from Supabase"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("live").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        return pd.DataFrame()

def preprocess_live_data(df):
    """
    Preprocess live data to match the format expected by calcola_report_completo.
    Handles period division based on 'fine primo tempo' event and removes quartetto column.
    """
    if df.empty:
        return df
    
    df_processed = df.copy()
    
    # Remove quartetto column if it exists (will be empty for live data)
    if 'quartetto' in df_processed.columns:
        df_processed = df_processed.drop('quartetto', axis=1)
    
    # Determine period division based on 'fine primo tempo' event
    # All events before 'fine primo tempo' are first period
    # All events after 'fine primo tempo' are second period
    fine_primo_tempo_index = None
    
    # Look for 'fine primo tempo' event
    if 'evento' in df_processed.columns:
        fine_primo_mask = df_processed['evento'].str.contains('fine primo tempo', case=False, na=False)
        if fine_primo_mask.any():
            fine_primo_tempo_index = df_processed[fine_primo_mask].index[0]
    
    # Create Periodo column
    df_processed['Periodo'] = 'Primo tempo'  # Default to first period
    
    # If we found 'fine primo tempo', mark events after it as second period
    if fine_primo_tempo_index is not None:
        df_processed.loc[fine_primo_tempo_index + 1:, 'Periodo'] = 'Secondo tempo'
    
    return df_processed



# Main app
def main():
    # Auto-refresh every 30 seconds
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Fetch live data
    with st.spinner("Loading live data..."):
        df_raw = get_live_data()
    
    if not df_raw.empty:
        st.success(f"✅ Loaded {len(df_raw)} live events")
        
        # Preprocess live data
        df = preprocess_live_data(df_raw)
        
        # Calculate complete report using the same function as Partite page
        report_eventi = calcola_report_completo(df)
        
        # Helper functions for formatting (same as Partite page)
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
    
    else:
        st.error("❌ No live data available. Please check your connection and try again.")

if __name__ == "__main__":
    main()
