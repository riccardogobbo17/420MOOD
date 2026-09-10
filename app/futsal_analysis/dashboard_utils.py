"""
Utilities per la dashboard di panoramica stagionale
"""
import streamlit as st
import pandas as pd

from .utils_eventi import ESITI_IN_PORTA, _col, mask_evento, mask_gol, mask_parata, mask_tiro


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
    
    esito_all = _col(df_all, 'esito')
    squadra_all = _col(df_all, 'squadra')

    # Gol per partita
    gol_fatti_totali = int(mask_gol(df_all, 'Noi').sum())
    gol_subiti_totali = int(mask_gol(df_all, 'Loro').sum())
    gol_medi_fatti = gol_fatti_totali / num_partite if num_partite > 0 else 0
    gol_medi_subiti = gol_subiti_totali / num_partite if num_partite > 0 else 0
    
    # Tiri per partita (i Tiro con Esito='Assist' non sono conclusioni)
    tiri_totali = int(mask_tiro(df_all, 'Noi').sum())
    tiri_medi = tiri_totali / num_partite if num_partite > 0 else 0
    
    tiri_subiti_totali = int(mask_tiro(df_all, 'Loro').sum())
    tiri_subiti_medi = tiri_subiti_totali / num_partite if num_partite > 0 else 0
    
    # Palle perse/recuperate per partita (taggate solo per noi)
    palle_perse_totali = int(mask_evento(df_all, 'Palla persa').sum())
    palle_recuperate_totali = int(mask_evento(df_all, 'Palla recuperata').sum())
    palle_perse_medie = palle_perse_totali / num_partite if num_partite > 0 else 0
    palle_recuperate_medie = palle_recuperate_totali / num_partite if num_partite > 0 else 0
    
    # Falli per partita
    falli_fatti_totali = int((mask_evento(df_all, 'Fallo') & (squadra_all == 'Noi')).sum())
    falli_subiti_totali = int((mask_evento(df_all, 'Fallo') & (squadra_all == 'Loro')).sum())
    falli_medi_fatti = falli_fatti_totali / num_partite if num_partite > 0 else 0
    falli_medi_subiti = falli_subiti_totali / num_partite if num_partite > 0 else 0
    
    # Percentuale tiri in porta
    tiri_in_porta_totali = int((mask_tiro(df_all, 'Noi') & esito_all.isin(ESITI_IN_PORTA)).sum())
    perc_tiri_in_porta = (tiri_in_porta_totali / tiri_totali * 100) if tiri_totali > 0 else 0
    
    # Calcola vittorie, pareggi, sconfitte
    risultati = {'V': 0, 'P': 0, 'S': 0}
    for p_id in partite_ids:
        df_partita = df_all[df_all['partita_id'] == p_id]
        gol_fatti = int(mask_gol(df_partita, 'Noi').sum())
        gol_subiti = int(mask_gol(df_partita, 'Loro').sum())
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
    
    # Parate del portiere (le punizioni parate contano, i tiri Assist no)
    parate_totali = int(mask_parata(df_all, 'Noi').sum())
    tiri_in_porta_subiti = parate_totali + gol_subiti_totali
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

