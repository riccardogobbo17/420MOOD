"""
Utilities per la dashboard di panoramica stagionale
"""
import streamlit as st
import pandas as pd


def render_panoramica_stagione(df_all, partite_ids):
    """
    Renderizza la panoramica stagionale con tutte le metriche aggregate.
    Usa una griglia CSS personalizzata per mantenere 3 colonne anche su mobile.
    
    Args:
        df_all: DataFrame con tutti gli eventi delle partite
        partite_ids: Lista degli ID delle partite da considerare
    """
    st.markdown("---")
    st.subheader("📈 Panoramica Stagione")
    
    # CSS per card compatte
    st.markdown("""
    <style>
    .metric-card-compact {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    .metric-value-compact {
        font-size: 1.5em;
        font-weight: bold;
        color: #1565c0;
        margin: 2px 0;
    }
    .metric-label-compact {
        font-size: 0.75em;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Calcola metriche aggregate
    num_partite = len(partite_ids)
    
    # Gol per partita
    gol_fatti_totali = len(df_all[(df_all['evento'] == 'Gol') & (df_all['squadra'] == 'Noi')])
    gol_subiti_totali = len(df_all[(df_all['evento'] == 'Gol') & (df_all['squadra'] == 'Loro')])
    gol_medi_fatti = gol_fatti_totali / num_partite if num_partite > 0 else 0
    gol_medi_subiti = gol_subiti_totali / num_partite if num_partite > 0 else 0
    
    # Tiri per partita
    tiri_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Noi')])
    tiri_medi = tiri_totali / num_partite if num_partite > 0 else 0
    
    tiri_subiti_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Loro')])
    tiri_subiti_medi = tiri_subiti_totali / num_partite if num_partite > 0 else 0
    
    # Palle perse/recuperate per partita
    palle_perse_totali = len(df_all[(df_all['evento'].str.contains('Palla persa', na=False))])
    palle_recuperate_totali = len(df_all[(df_all['evento'].str.contains('Palla recuperata', na=False))])
    palle_perse_medie = palle_perse_totali / num_partite if num_partite > 0 else 0
    palle_recuperate_medie = palle_recuperate_totali / num_partite if num_partite > 0 else 0
    
    # Falli per partita
    falli_fatti_totali = len(df_all[(df_all['evento'].str.contains('Fallo', na=False)) & (df_all['squadra'] == 'Noi')])
    falli_subiti_totali = len(df_all[(df_all['evento'].str.contains('Fallo', na=False)) & (df_all['squadra'] == 'Loro')])
    falli_medi_fatti = falli_fatti_totali / num_partite if num_partite > 0 else 0
    falli_medi_subiti = falli_subiti_totali / num_partite if num_partite > 0 else 0
    
    # Percentuale tiri in porta
    tiri_in_porta_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Noi') & df_all['esito'].isin(['Parata', 'Gol', 'Palo'])])
    perc_tiri_in_porta = (tiri_in_porta_totali / tiri_totali * 100) if tiri_totali > 0 else 0
    
    # Calcola vittorie, pareggi, sconfitte
    risultati = {'V': 0, 'P': 0, 'S': 0}
    for p_id in partite_ids:
        df_partita = df_all[df_all['partita_id'] == p_id]
        gol_fatti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Noi')])
        gol_subiti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Loro')])
        if gol_fatti > gol_subiti:
            risultati['V'] += 1
        elif gol_fatti < gol_subiti:
            risultati['S'] += 1
        else:
            risultati['P'] += 1
    
    # Calcola punti (3 per vittoria, 1 per pareggio)
    punti_totali = risultati['V'] * 3 + risultati['P']
    
    # Percentuale conversione tiri in gol
    perc_conversione = (gol_fatti_totali / tiri_totali * 100) if tiri_totali > 0 else 0
    
    # Percentuale conversione tiri subiti in gol subiti
    perc_conversione_subiti = (gol_subiti_totali / tiri_subiti_totali * 100) if tiri_subiti_totali > 0 else 0
    
    # Calcola vittorie, pareggi, sconfitte
    risultati = {'V': 0, 'P': 0, 'S': 0}
    for p_id in partite_ids:
        df_partita = df_all[df_all['partita_id'] == p_id]
        gol_fatti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Noi')])
        gol_subiti = len(df_partita[(df_partita['evento'] == 'Gol') & (df_partita['squadra'] == 'Loro')])
        if gol_fatti > gol_subiti:
            risultati['V'] += 1
        elif gol_fatti < gol_subiti:
            risultati['S'] += 1
        else:
            risultati['P'] += 1
    
    # Calcola punti (3 per vittoria, 1 per pareggio)
    punti_totali = risultati['V'] * 3 + risultati['P']
    
    # Percentuale conversione tiri in gol
    perc_conversione = (gol_fatti_totali / tiri_totali * 100) if tiri_totali > 0 else 0
    
    # Percentuale conversione tiri subiti in gol subiti
    perc_conversione_subiti = (gol_subiti_totali / tiri_subiti_totali * 100) if tiri_subiti_totali > 0 else 0
    
    # Parate del portiere
    parate_totali = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Loro') & (df_all['esito'] == 'Parata')])
    tiri_in_porta_subiti = len(df_all[(df_all['evento'].str.contains('Tiro', na=False)) & (df_all['squadra'] == 'Loro') & df_all['esito'].isin(['Parata', 'Gol', 'Palo'])])
    perc_parate = (parate_totali / tiri_in_porta_subiti * 100) if tiri_in_porta_subiti > 0 else 0
    
    # --- VISUALIZZAZIONE METRICHE (4 COLONNE COMPATTE) ---
    
    # Riga 1: Partite, Risultati, Gol Fatti/Part., Gol Subiti/Part.
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact">{num_partite}</div>
            <div class="metric-label-compact">Partite</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color = "#2e7d32" if risultati['V'] >= risultati['S'] else "#c62828"
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: {color};">{risultati['V']}V-{risultati['P']}P-{risultati['S']}S</div>
            <div class="metric-label-compact">Risultati</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #2e7d32;">{gol_medi_fatti:.2f}</div>
            <div class="metric-label-compact">Gol Fatti/Part.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #c62828;">{gol_medi_subiti:.2f}</div>
            <div class="metric-label-compact">Gol Subiti/Part.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Riga 2: Tiri Fatti/Part., Tiri Subiti/Part., Conv. Tiri-Gol %, Conv. Tiri Subiti-Gol %
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact">{tiri_medi:.2f}</div>
            <div class="metric-label-compact">Tiri Fatti/Part.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact">{tiri_subiti_medi:.2f}</div>
            <div class="metric-label-compact">Tiri Subiti/Part.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col7:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #2e7d32;">{perc_conversione:.1f}%</div>
            <div class="metric-label-compact">Conv. Tiri-Gol</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col8:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #c62828;">{perc_conversione_subiti:.1f}%</div>
            <div class="metric-label-compact">Conv. Tiri Sub.-Gol</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Riga 3: Tiri in Porta %, Palle Perse/Part., Palle Recuperate/Part., % Parate
    col9, col10, col11, col12 = st.columns(4)
    
    with col9:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact">{perc_tiri_in_porta:.1f}%</div>
            <div class="metric-label-compact">Tiri in Porta %</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col10:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #d84315;">{palle_perse_medie:.2f}</div>
            <div class="metric-label-compact">Palle Perse/Part.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col11:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #1565c0;">{palle_recuperate_medie:.2f}</div>
            <div class="metric-label-compact">Palle Recup./Part.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col12:
        st.markdown(f"""
        <div class="metric-card-compact">
            <div class="metric-value-compact" style="color: #1976d2;">{perc_parate:.1f}%</div>
            <div class="metric-label-compact">% Parate</div>
        </div>
        """, unsafe_allow_html=True)

