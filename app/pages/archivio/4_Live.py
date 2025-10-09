import streamlit as st
import pandas as pd
from futsal_analysis.config_supabase import get_supabase_client
from futsal_analysis.utils_eventi import calcola_palle_recuperate_perse, calcola_attacco, calcola_difesa
from futsal_analysis.zone_analysis import calcola_report_zona

# Page configuration
st.set_page_config(
    page_title="Live Stats - 420MOOD",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Live Statistics")

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

def create_stats_table(df):
    """Create a comprehensive stats table showing lost balls, recovered balls, shots by zones"""
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Calculate zone-based statistics
    zone_report = calcola_report_zona(df)
    
    # Get zone stats for team
    zone_stats = zone_report['squadra']
    
    # Create comprehensive table data
    table_data = []
    
    # Define zones - only 1, 2, 3
    zones = [1, 2, 3]
    
    for zone in zones:
        zone_name = f"Zona {zone}"
        
        # Get stats for this zone
        attacco_stats = zone_stats['attacco'].get(zone, {})
        difesa_stats = zone_stats['difesa'].get(zone, {})
        palle_stats = zone_stats['palle_recuperate_perse'].get(zone, {})
        
        # Extract key metrics
        row_data = {
            "Zona": zone_name,
            "Palle Perse": palle_stats.get('palla_persa_totali', 0),
            "Palle Recuperate": palle_stats.get('palla_recuperata_totali', 0),
            "Tiri Fatti": attacco_stats.get('tiri_totali', 0),
            "Tiri in Porta": attacco_stats.get('tiri_in_porta_totali', 0),
            "Tiri Subiti": difesa_stats.get('tiri_totali_subiti', 0),
            "Tiri in Porta Subiti": difesa_stats.get('tiri_in_porta_totali_subiti', 0),
            "Efficacia Tiro": f"{(attacco_stats.get('tiri_in_porta_totali', 0) / max(attacco_stats.get('tiri_totali', 1), 1) * 100):.1f}%" if attacco_stats.get('tiri_totali', 0) > 0 else "0%"
        }
        
        table_data.append(row_data)
    
    return pd.DataFrame(table_data)


# Main app
def main():
    # Auto-refresh every 30 seconds
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Fetch live data
    with st.spinner("Loading live data..."):
        df = get_live_data()
    
    if not df.empty:
        st.success(f"✅ Loaded {len(df)} live events")
        
        # Show single table since zones are only 1-3
        st.subheader("Statistics by Zone (Zones 1-3)")
        complete_table = create_stats_table(df)
        st.dataframe(complete_table, use_container_width=True)
        
        # Download button
        csv = complete_table.to_csv(index=False)
        st.download_button(
            label="📥 Download Stats",
            data=csv,
            file_name="live_stats.csv",
            mime="text/csv"
        )
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        
        total_palle_perse = complete_table['Palle Perse'].sum()
        total_palle_recuperate = complete_table['Palle Recuperate'].sum()
        total_tiri_fatti = complete_table['Tiri Fatti'].sum()
        total_tiri_subiti = complete_table['Tiri Subiti'].sum()
        
        with col1:
            st.metric("Total Balls Lost", total_palle_perse)
            st.metric("Total Balls Recovered", total_palle_recuperate)
        
        with col2:
            st.metric("Total Shots Made", total_tiri_fatti)
            st.metric("Total Shots Received", total_tiri_subiti)
        
        with col3:
            ball_balance = total_palle_recuperate - total_palle_perse
            shot_balance = total_tiri_fatti - total_tiri_subiti
            st.metric("Ball Balance", ball_balance, delta=f"{ball_balance:+d}")
            st.metric("Shot Balance", shot_balance, delta=f"{shot_balance:+d}")
    
    else:
        st.error("❌ No live data available. Please check your connection and try again.")

if __name__ == "__main__":
    main()
