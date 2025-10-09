import pandas as pd

def _get_zonadict(df, group_key, stat_keys):
    """Restituisce dict: zona -> (chi/portiere/None) -> stats dict."""
    df = df.copy()
    df['zona'] = pd.to_numeric(df['dove'], errors='coerce').astype('Int64')
    result = {}
    for zona, gruppo in df.groupby('zona'):
        if group_key in gruppo.columns:
            group_stats = {}
            for name, sub in gruppo.groupby(group_key):
                # SALTA chiavi vuote o nan
                if (isinstance(name, str) and name.strip() == '') or pd.isnull(name):
                    continue
                stat_dict = {k: len(sub[m(sub)]) for k, m in stat_keys.items()}
                group_stats[name] = stat_dict
            result[int(zona)] = group_stats
        else:
            stat_dict = {k: len(gruppo[m(gruppo)]) for k, m in stat_keys.items()}
            result[int(zona)] = stat_dict
    return result


# ----------- STATS DI SQUADRA -----------

def calcola_attacco(df, by_zona=False):
    mask_noi = (df['squadra'] == 'Noi') & (df['evento'].str.contains('Tiro|Laterale|Angolo', na=False))
    if by_zona:
        df_zona = df[mask_noi & (df['dove'].notnull())].copy()
        stat_keys = {
            'gol_fatti': lambda d: d['evento'].str.contains('Gol', na=False) & (d['squadra'] == 'Noi'),
            'tiri_totali': lambda d: d['evento'].str.contains('Tiro', na=False),
            'tiri_in_porta_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & d['esito'].isin(['Parata', 'Gol']),
            'tiri_fuori': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Fuori'),
            'tiri_ribattuti': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Ribattuto'),
            'palo_traversa': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Palo'),
            'angoli': lambda d: d['evento'].str.contains('Angolo', na=False),
            'laterale': lambda d: d['evento'].str.contains('Laterale', na=False),
        }
        return _get_zonadict(df_zona, group_key=None, stat_keys=stat_keys)
    else:
        stats = {}
        mask_tiro = (df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Noi')
        mask_gol = (df['evento'].str.contains('Gol', na=False)) & (df['squadra'] == 'Noi')
        stats['gol_fatti'] = len(df[mask_gol])
        stats['tiri_totali'] = len(df[mask_tiro])
        stats['tiri_in_porta'] = len(df[mask_tiro & df['esito'].isin(['Parata', 'Gol'])])
        stats['tiri_fuori'] = len(df[mask_tiro & (df['esito'] == 'Fuori')])
        stats['tiri_ribattuti'] = len(df[mask_tiro & (df['esito'] == 'Ribattuto')])
        stats['palo_traversa'] = len(df[mask_tiro & (df['esito'] == 'Palo')])
        stats['angoli'] = len(df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Noi')])
        stats['laterali'] = len(df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Noi')])
        stats['rigori'] = len(df[(df['evento'].str.contains('Rigore', na=False)) & (df['squadra'] == 'Noi')])
        stats['tiri_liberi'] = len(df[(df['evento'].str.contains('Tiro libero', na=False)) & (df['squadra'] == 'Noi')])
        return stats

def calcola_difesa(df, by_zona=False):
    mask_loro = (df['squadra'] == 'Loro') & (df['evento'].str.contains('Tiro|Laterale|Angolo', na=False))
    if by_zona:
        df_zona = df[mask_loro & (df['dove'].notnull())].copy()
        stat_keys = {
            'gol_subiti': lambda d: d['evento'].str.contains('Gol', na=False) & (d['squadra'] == 'Loro'),
            'tiri_totali_subiti': lambda d: d['evento'].str.contains('Tiro', na=False),
            'tiri_in_porta_totali_subiti': lambda d: d['evento'].str.contains('Tiro', na=False) & d['esito'].isin(['Parata', 'Gol']),
            'tiri_fuori_loro': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Fuori'),
            'tiri_ribattuti_da_noi': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Ribattuto'),
            'palo_traversa_loro': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Palo'),
            'angoli_loro': lambda d: d['evento'].str.contains('Angolo', na=False),
            'laterale_loro': lambda d: d['evento'].str.contains('Laterale', na=False),
            'tiri_liberi_subiti': lambda d: d['evento'].str.contains('Tiro libero', na=False),
        }
        return _get_zonadict(df_zona, group_key=None, stat_keys=stat_keys)
    else:
        stats = {}
        mask_tiro = (df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro')
        mask_gol = (df['evento'].str.contains('Gol', na=False)) & (df['squadra'] == 'Loro')
        stats['gol_subiti'] = len(df[mask_gol])
        stats['tiri_subiti'] = len(df[mask_tiro])
        stats['tiri_in_porta_subiti'] = len(df[mask_tiro & df['esito'].isin(['Parata', 'Gol'])])
        stats['tiri_fuori_subiti'] = len(df[mask_tiro & (df['esito'] == 'Fuori')])
        stats['tiri_loro_ribattuti_da_noi'] = len(df[mask_tiro & (df['esito'] == 'Ribattuto')])
        stats['tiri_loro_palo_traversa'] = len(df[mask_tiro & (df['esito'] == 'Palo')])
        stats['angoli_subiti'] = len(df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Loro')])
        stats['laterali_subiti'] = len(df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Loro')])
        stats['rigori_subiti'] = len(df[(df['evento'].str.contains('Rigore', na=False)) & (df['squadra'] == 'Loro')])
        stats['tiri_liberi_subiti'] = len(df[(df['evento'].str.contains('Tiro libero', na=False)) & (df['squadra'] == 'Loro')])
        return stats

def calcola_palle_recuperate_perse(df, by_zona=False):
    mask_noi = (df['squadra'] == 'Noi') & (df['evento'].str.contains('Palla recuperata|Palla persa', na=False))
    if by_zona:
        df_zona = df[mask_noi & (df['dove'].notnull())].copy()
        stat_keys = {
            'palla_recuperata_totali': lambda d: d['evento'].str.contains('Palla recuperata', na=False),
            'palla_recuperata_ripartenza': lambda d: d['evento'].str.contains('Palla recuperata', na=False) & (d['esito'] == 'Ripartenza'),
            'palla_recuperata_costruzione': lambda d: d['evento'].str.contains('Palla recuperata', na=False) & (d['esito'] == 'Costruzione'),
            'palla_recuperata_fuori': lambda d: d['evento'].str.contains('Palla recuperata', na=False) & (d['esito'] == 'Fuori'),
            'palla_persa_totali': lambda d: d['evento'].str.contains('Palla persa', na=False),
            'palla_persa_ripartenza': lambda d: d['evento'].str.contains('Palla persa', na=False) & (d['esito'] == 'Ripartenza'),
            'palla_persa_costruzione': lambda d: d['evento'].str.contains('Palla persa', na=False) & (d['esito'] == 'Costruzione'),
            'palla_persa_fuori': lambda d: d['evento'].str.contains('Palla persa', na=False) & (d['esito'] == 'Fuori'),
        }
        return _get_zonadict(df_zona, group_key=None, stat_keys=stat_keys)
    else:
        stats = {}
        mask_rec = (df['evento'].str.contains('Palla recuperata', na=False))
        stats['palla_recuperata_totali'] = len(df[mask_rec])
        stats['palla_recuperata_ripartenza'] = len(df[mask_rec & (df['esito'] == 'Ripartenza')])
        stats['palla_recuperata_costruzione'] = len(df[mask_rec & (df['esito'] == 'Costruzione')])
        stats['palla_recuperata_fuori'] = len(df[mask_rec & (df['esito'] == 'Fuori')])
        mask_persa = (df['evento'].str.contains('Palla persa', na=False))
        stats['palla_persa_totali'] = len(df[mask_persa])
        stats['palla_persa_ripartenza'] = len(df[mask_persa & (df['esito'] == 'Ripartenza')])
        stats['palla_persa_costruzione'] = len(df[mask_persa & (df['esito'] == 'Costruzione')])
        stats['palla_persa_fuori'] = len(df[mask_persa & (df['esito'] == 'Fuori')])
        return stats

def calcola_falli(df, by_zona=False):
    if by_zona:
        mask_falli = df['evento'].str.contains('Fallo', na=False) & df['dove'].notnull()
        df_falli = df[mask_falli].copy()
        df_falli['fieldpos'] = pd.to_numeric(df_falli['dove'], errors='coerce').astype('Int64')
        stat_keys = {
            'falli_fatti_totali': lambda d: (d['squadra'] == 'Noi'),
            'falli_fatti_zona_attacco': lambda d: (d['squadra'] == 'Noi') & (d['fieldpos'] == 0),
            'falli_fatti_zona_difesa': lambda d: (d['squadra'] == 'Noi') & (d['fieldpos'] > 0),
            'falli_subiti_totali': lambda d: (d['squadra'] == 'Loro'),
            'falli_subiti_zona_attacco': lambda d: (d['squadra'] == 'Loro') & (d['fieldpos'] == 0),
            'falli_subiti_zona_difesa': lambda d: (d['squadra'] == 'Loro') & (d['fieldpos'] > 0),
        }
        return _get_zonadict(df_falli, group_key=None, stat_keys=stat_keys)
    else:
        stats = {}
        mask_fatti = (df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Noi')
        mask_subiti = (df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Loro')
        stats['falli_fatti'] = len(df[mask_fatti])
        stats['falli_subiti'] = len(df[mask_subiti])

        mask_fatti_attacco = mask_fatti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) > 0)
        mask_fatti_difesa  = mask_fatti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) == 0)
        mask_subiti_attacco = mask_subiti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) > 0)
        mask_subiti_difesa  = mask_subiti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) == 0)

        stats['falli_fatti_zona_attacco'] = len(df[mask_fatti_attacco])
        stats['falli_fatti_zona_difesa'] = len(df[mask_fatti_difesa])
        stats['falli_subiti_zona_attacco'] = len(df[mask_subiti_attacco])
        stats['falli_subiti_zona_difesa'] = len(df[mask_subiti_difesa])

        stats['ammonizioni_fatti'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Noi')])
        stats['espulsioni_fatti'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Noi')])
        stats['ammonizioni_subiti'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Loro')])
        stats['espulsioni_subiti'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Loro')])
        return stats

def calcola_ripartenze(df):
    rip = {}
    # Ripartenze create da noi
    rip['3v2'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('3v2', na=False))])
    rip['2v2'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('2v2', na=False))])
    rip['2v1'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('2v1', na=False))])
    rip['1v1'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('1v1', na=False))])
    rip['ripartenze_totali'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi')])
    
    # Ripartenze subite da noi (create da loro)
    rip['3v2_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('3v2', na=False))])
    rip['2v2_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('2v2', na=False))])
    rip['2v1_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('2v1', na=False))])
    rip['1v1_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('1v1', na=False))])
    rip['ripartenze_subite_totali'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro')])
    return rip

# ----------- STATS INDIVIDUALI -----------

def calcola_stats_individuali(df, by_zona=False):
    def stat_keys_fn():
        return {
            # ATTACCO
            'gol_fatti': lambda d: d['evento'].str.contains('Gol', na=False) & (d['squadra'] == 'Noi'),
            'tiri_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi'),
            'tiri_in_porta_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & d['esito'].isin(['Parata', 'Gol']),
            'tiri_fuori': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & (d['esito'] == 'Fuori'),
            'tiri_ribattuti': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & (d['esito'] == 'Ribattuto'),
            'palo_traversa': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & (d['esito'] == 'Palo'),
            # PALLE PERSE
            'palle_perse': lambda d: d['evento'].str.contains('Palla persa', na=False),
            # DIFESA
            'tiri_ribattuti_noi': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Loro') & (d['esito'] == 'Ribattuto'),
            'palle_recuperate': lambda d: d['evento'].str.contains('Palla recuperata', na=False),
            # FALLI
            'falli_fatti': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Noi'),
            'falli_subiti': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Loro'),
            'ammonizioni': lambda d: d['evento'].str.contains('Ammonizione', na=False) & (d['squadra'] == 'Noi'),
            'espulsioni': lambda d: d['evento'].str.contains('Espulsione', na=False) & (d['squadra'] == 'Noi'),
        }

    if by_zona:
        mask = df['dove'].notnull()
        return _get_zonadict(df[mask], group_key='chi', stat_keys=stat_keys_fn())
    else:
        # Per tutti i giocatori, tutte le stats
        stats = {}
        chi_list = df['chi'].dropna()
        chi_list = chi_list[chi_list.str.strip() != ''].unique()

        for chi in chi_list:
            sub = df[df['chi'] == chi]
            stats[chi] = {k: len(sub[m(sub)]) for k, m in stat_keys_fn().items()}
        return stats

# ----------- STATS PORTIERI -----------

def calcola_stats_portieri_individuali(df, by_zona=False):
    def stat_keys_fn():
        return {
            'parate': lambda d: ((d['evento'].str.contains('Parata', na=False)) & (d['squadra'] == 'Noi')) |
                                ((d['evento'].str.contains('Tiro', na=False)) & (d['squadra'] == 'Loro') & (d['esito'] == 'Parata')),
            'lanci': lambda d: (d['evento'].str.contains('Lancio', na=False)) & (d['squadra'] == 'Noi'),
            'lanci_corretti': lambda d: (d['evento'].str.contains('Lancio', na=False)) & (d['squadra'] == 'Noi') & (d['esito'].isin(['Gol', '', None])),
            'lanci_sbagliati': lambda d: (d['evento'].str.contains('Lancio', na=False)) & (d['squadra'] == 'Noi') & (d['esito'].isin(['Intercetto', 'Fuori'])),
            'integrazione_portiere': lambda d: (d['evento'].str.contains('Integrazione portier', na=False)) & (d['squadra'] == 'Noi'),
            'integrazione_portiere_ok': lambda d: (d['evento'].str.contains('Integrazione portier', na=False)) & (d['squadra'] == 'Noi') & (d['esito'].isin(['', None])),
            'integrazione_portiere_ko': lambda d: (d['evento'].str.contains('Integrazione portier', na=False)) & (d['squadra'] == 'Noi') & (d['esito'].isin(['Intercetto', 'Fuori'])),
        }

    if by_zona:
        mask = df['dove'].notnull()
        return _get_zonadict(df[mask], group_key='portiere', stat_keys=stat_keys_fn())
    else:
        stats = {}
        portieri = df['portiere'].dropna()
        portieri = portieri[portieri.str.strip() != ''].unique()
        for portiere in portieri:
            sub = df[df['portiere'] == portiere]
            stats[portiere] = {k: len(sub[m(sub)]) for k, m in stat_keys_fn().items()}
        return stats

def calcola_stats_portieri_squadra(df, squadra='Noi'):
    mask_sq = (df['squadra'] == squadra)
    if squadra == 'Noi':
        mask_parata = ((df['evento'].str.contains('Parata', na=False)) & mask_sq) | \
                      ((df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro') & (df['esito'] == 'Parata'))
    else:
        mask_parata = ((df['evento'].str.contains('Parata', na=False)) & mask_sq) | \
                      ((df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Noi') & (df['esito'] == 'Parata'))

    mask_lancio = (df['evento'].str.contains('Lancio', na=False)) & mask_sq
    mask_lancio_ok = mask_lancio & (df['esito'].isin(['Gol', '', None]))
    mask_lancio_ko = mask_lancio & (df['esito'].isin(['Intercetto', 'Fuori']))

    mask_int = (df['evento'].str.contains('Integrazione portier', na=False)) & mask_sq
    mask_int_ok = mask_int & (df['esito'].isin(['', None]))
    mask_int_ko = mask_int & (df['esito'].isin(['Intercetto', 'Fuori']))

    stats = {
        'parate': len(df[mask_parata]),
        'lanci': len(df[mask_lancio]),
        'lanci_corretti': len(df[mask_lancio_ok]),
        'lanci_sbagliati': len(df[mask_lancio_ko]),
        'integrazione_portiere': len(df[mask_int]),
        'integrazione_portiere_ok': len(df[mask_int_ok]),
        'integrazione_portiere_ko': len(df[mask_int_ko])
    }
    return stats


# ----------- STATS SQUADRA CON SPLIT PER PERIODO -----------

def _split_per_periodo(df):
    df_1t = df[df['Periodo'] == 'Primo tempo'] if 'Periodo' in df.columns else df.iloc[0:0]
    df_2t = df[df['Periodo'] == 'Secondo tempo'] if 'Periodo' in df.columns else df.iloc[0:0]
    return df, df_1t, df_2t

def _with_split(calc_fn, df):
    df_tot, df_1t, df_2t = _split_per_periodo(df)
    return {
        'Totale': calc_fn(df_tot),
        '1T': calc_fn(df_1t),
        '2T': calc_fn(df_2t)
    }

def calcola_report_completo(df):
    """
    Restituisce tutte le statistiche aggregate in un unico dizionario strutturato:
      - report['squadra']           : stats di squadra (tutte le sezioni)
      - report['individuali']       : dizionario stats individuali giocatori
      - report['portieri_individuali'] : dizionario stats individuali portieri
    """
    report = {}

    # STATS DI SQUADRA
    report['squadra'] = {
        'attacco': _with_split(calcola_attacco, df),
        'difesa': _with_split(calcola_difesa, df),
        'falli': _with_split(calcola_falli, df),
        'portieri_noi': _with_split(lambda d: calcola_stats_portieri_squadra(d, squadra='Noi'), df),
        'portieri_loro': _with_split(lambda d: calcola_stats_portieri_squadra(d, squadra='Loro'), df),
    }

    # STATS INDIVIDUALI GIOCATORI (dizionario)
    report['individuali'] = calcola_stats_individuali(df, by_zona=False)

    # STATS PORTIERI INDIVIDUALI (dizionario)
    report['portieri_individuali'] = calcola_stats_portieri_individuali(df, by_zona=False)

    # Split per periodo anche per individuali
    _, df_1t, df_2t = _split_per_periodo(df)
    report['individuali_split'] = {
        'Totale': calcola_stats_individuali(df, by_zona=False),
        '1T': calcola_stats_individuali(df_1t, by_zona=False),
        '2T': calcola_stats_individuali(df_2t, by_zona=False),
    }
    report['portieri_individuali_split'] = {
        'Totale': calcola_stats_portieri_individuali(df, by_zona=False),
        '1T': calcola_stats_portieri_individuali(df_1t, by_zona=False),
        '2T': calcola_stats_portieri_individuali(df_2t, by_zona=False),
    }

    return report


# ----------- STATS QUARTETTI -----------

def calcola_stats_quartetti(df):
    """
    Calcola le statistiche raggruppate per quartetto (4 giocatori di movimento).
    Esclude il portiere e le situazioni con 5 giocatori di movimento.
    """
    # Filtra solo le righe con 4 giocatori di movimento (escludi portiere)
    df_quartetti = df.copy()
    
    # Crea una colonna per identificare i quartetti
    def get_quartetto(row):
        # Prendi i 4 giocatori di movimento (escludi portiere)
        giocatori = []
        # Prova prima i nomi delle colonne del database Supabase
        for col in ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3']:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                giocatori.append(str(row[col]).strip())
        
        # Se non troviamo giocatori, prova i nomi delle colonne normalizzate dal CSV
        if not giocatori:
            for col in ['quartetto', 'quartetto.1', 'quartetto.2', 'quartetto.3']:
                if col in row and pd.notna(row[col]) and str(row[col]).strip():
                    giocatori.append(str(row[col]).strip())
        
        # Se abbiamo esattamente 4 giocatori, crea il quartetto
        if len(giocatori) == 4:
            return ';'.join(sorted(giocatori))
        return None
    
    # Applica la funzione per creare la colonna quartetto
    df_quartetti['quartetto_id'] = df_quartetti.apply(get_quartetto, axis=1)
    
    # Filtra solo le righe con quartetti validi
    df_quartetti = df_quartetti[df_quartetti['quartetto_id'].notna()]
    
    if df_quartetti.empty:
        return {}
    
    # Calcola le statistiche per ogni quartetto
    stats_quartetti = {}
    
    for quartetto, gruppo in df_quartetti.groupby('quartetto_id'):
        stats = {}
        
        # GOL
        stats['gol_fatti'] = len(gruppo[(gruppo['evento'].str.contains('Gol', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['gol_subiti'] = len(gruppo[(gruppo['evento'].str.contains('Gol', na=False)) & (gruppo['squadra'] == 'Loro')])
        
        # ATTACCO
        mask_tiro = (gruppo['evento'].str.contains('Tiro', na=False)) & (gruppo['squadra'] == 'Noi')
        stats['tiri_totali'] = len(gruppo[mask_tiro])
        stats['tiri_in_porta'] = len(gruppo[mask_tiro & gruppo['esito'].isin(['Parata', 'Gol'])])
        stats['tiri_fuori'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Fuori')])
        stats['tiri_ribattuti'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Ribattuto')])
        stats['palo_traversa'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Palo')])
        stats['angoli'] = len(gruppo[(gruppo['evento'].str.contains('Angolo', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['laterali'] = len(gruppo[(gruppo['evento'].str.contains('Laterale', na=False)) & (gruppo['squadra'] == 'Noi')])
        
        # DIFESA
        mask_tiro_loro = (gruppo['evento'].str.contains('Tiro', na=False)) & (gruppo['squadra'] == 'Loro')
        stats['tiri_subiti'] = len(gruppo[mask_tiro_loro])
        stats['tiri_in_porta_subiti'] = len(gruppo[mask_tiro_loro & gruppo['esito'].isin(['Parata', 'Gol'])])
        stats['tiri_fuori_subiti'] = len(gruppo[mask_tiro_loro & (gruppo['esito'] == 'Fuori')])
        stats['tiri_loro_ribattuti_da_noi'] = len(gruppo[mask_tiro_loro & (gruppo['esito'] == 'Ribattuto')])
        stats['angoli_subiti'] = len(gruppo[(gruppo['evento'].str.contains('Angolo', na=False)) & (gruppo['squadra'] == 'Loro')])
        stats['laterali_subiti'] = len(gruppo[(gruppo['evento'].str.contains('Laterale', na=False)) & (gruppo['squadra'] == 'Loro')])
        
        # PALLE PERSE/RECUPERATE
        stats['palle_perse'] = len(gruppo[(gruppo['evento'].str.contains('Palla persa', na=False))])
        stats['palle_recuperate'] = len(gruppo[(gruppo['evento'].str.contains('Palla recuperata', na=False))])
        
        # RIPARTENZE
        stats['ripartenze'] = len(gruppo[(gruppo['evento'].str.contains('Ripartenza', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['ripartenze_subite'] = len(gruppo[(gruppo['evento'].str.contains('Ripartenza', na=False)) & (gruppo['squadra'] == 'Loro')])
        
        # FALLI
        mask_falli_noi = (gruppo['evento'].str.contains('Fallo', na=False)) & (gruppo['squadra'] == 'Noi')
        mask_falli_loro = (gruppo['evento'].str.contains('Fallo', na=False)) & (gruppo['squadra'] == 'Loro')
        stats['falli_fatti'] = len(gruppo[mask_falli_noi])
        stats['falli_subiti'] = len(gruppo[mask_falli_loro])
        stats['ammonizioni'] = len(gruppo[(gruppo['evento'].str.contains('Ammonizione', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['espulsioni'] = len(gruppo[(gruppo['evento'].str.contains('Espulsione', na=False)) & (gruppo['squadra'] == 'Noi')])
        
        stats_quartetti[quartetto] = stats
    
    return stats_quartetti


def calcola_stats_quinto_uomo(df):
    """
    Calcola le statistiche per le situazioni con 5 giocatori di movimento (quinto uomo).
    """
    # Filtra solo le righe con 5 giocatori di movimento
    df_quinto = df.copy()
    
    def is_quinto_uomo(row):
        # Conta i giocatori di movimento (escludi portiere)
        giocatori = []
        # Prova prima i nomi delle colonne del database Supabase
        for col in ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3']:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                giocatori.append(str(row[col]).strip())
        
        # Se non troviamo giocatori, prova i nomi delle colonne normalizzate dal CSV
        if not giocatori:
            for col in ['quartetto', 'quartetto.1', 'quartetto.2', 'quartetto.3']:
                if col in row and pd.notna(row[col]) and str(row[col]).strip():
                    giocatori.append(str(row[col]).strip())
        
        # Se abbiamo 5 giocatori, è quinto uomo
        return len(giocatori) == 5
    
    # Applica la funzione per identificare quinto uomo
    df_quinto['is_quinto_uomo'] = df_quinto.apply(is_quinto_uomo, axis=1)
    
    # Filtra solo le righe con quinto uomo
    df_quinto = df_quinto[df_quinto['is_quinto_uomo']]
    
    if df_quinto.empty:
        return {}
    
    # Calcola le statistiche per quinto uomo
    stats = {}
    
    # GOL
    stats['gol_fatti'] = len(df_quinto[(df_quinto['evento'].str.contains('Gol', na=False)) & (df_quinto['squadra'] == 'Noi')])
    stats['gol_subiti'] = len(df_quinto[(df_quinto['evento'].str.contains('Gol', na=False)) & (df_quinto['squadra'] == 'Loro')])
    
    # ATTACCO
    mask_tiro = (df_quinto['evento'].str.contains('Tiro', na=False)) & (df_quinto['squadra'] == 'Noi')
    stats['tiri_totali'] = len(df_quinto[mask_tiro])
    stats['tiri_in_porta'] = len(df_quinto[mask_tiro & df_quinto['esito'].isin(['Parata', 'Gol'])])
    stats['tiri_fuori'] = len(df_quinto[mask_tiro & (df_quinto['esito'] == 'Fuori')])
    stats['tiri_ribattuti'] = len(df_quinto[mask_tiro & (df_quinto['esito'] == 'Ribattuto')])
    stats['palo_traversa'] = len(df_quinto[mask_tiro & (df_quinto['esito'] == 'Palo')])
    stats['angoli'] = len(df_quinto[(df_quinto['evento'].str.contains('Angolo', na=False)) & (df_quinto['squadra'] == 'Noi')])
    stats['laterali'] = len(df_quinto[(df_quinto['evento'].str.contains('Laterale', na=False)) & (df_quinto['squadra'] == 'Noi')])
    
    # DIFESA
    mask_tiro_loro = (df_quinto['evento'].str.contains('Tiro', na=False)) & (df_quinto['squadra'] == 'Loro')
    stats['tiri_subiti'] = len(df_quinto[mask_tiro_loro])
    stats['tiri_in_porta_subiti'] = len(df_quinto[mask_tiro_loro & df_quinto['esito'].isin(['Parata', 'Gol'])])
    stats['tiri_fuori_subiti'] = len(df_quinto[mask_tiro_loro & (df_quinto['esito'] == 'Fuori')])
    stats['tiri_loro_ribattuti_da_noi'] = len(df_quinto[mask_tiro_loro & (df_quinto['esito'] == 'Ribattuto')])
    stats['angoli_subiti'] = len(df_quinto[(df_quinto['evento'].str.contains('Angolo', na=False)) & (df_quinto['squadra'] == 'Loro')])
    stats['laterali_subiti'] = len(df_quinto[(df_quinto['evento'].str.contains('Laterale', na=False)) & (df_quinto['squadra'] == 'Loro')])
    
    # PALLE PERSE/RECUPERATE
    stats['palle_perse'] = len(df_quinto[(df_quinto['evento'].str.contains('Palla persa', na=False))])
    stats['palle_recuperate'] = len(df_quinto[(df_quinto['evento'].str.contains('Palla recuperata', na=False))])
    
    # RIPARTENZE
    stats['ripartenze'] = len(df_quinto[(df_quinto['evento'].str.contains('Ripartenza', na=False)) & (df_quinto['squadra'] == 'Noi')])
    stats['ripartenze_subite'] = len(df_quinto[(df_quinto['evento'].str.contains('Ripartenza', na=False)) & (df_quinto['squadra'] == 'Loro')])
    
    # FALLI
    mask_falli_noi = (df_quinto['evento'].str.contains('Fallo', na=False)) & (df_quinto['squadra'] == 'Noi')
    mask_falli_loro = (df_quinto['evento'].str.contains('Fallo', na=False)) & (df_quinto['squadra'] == 'Loro')
    stats['falli_fatti'] = len(df_quinto[mask_falli_noi])
    stats['falli_subiti'] = len(df_quinto[mask_falli_loro])
    stats['ammonizioni'] = len(df_quinto[(df_quinto['evento'].str.contains('Ammonizione', na=False)) & (df_quinto['squadra'] == 'Noi')])
    stats['espulsioni'] = len(df_quinto[(df_quinto['evento'].str.contains('Espulsione', na=False)) & (df_quinto['squadra'] == 'Noi')])
    
    return stats


def calcola_report_quartetti_completo(df):
    """
    Calcola le statistiche dei quartetti con split per periodo (Totale, 1T, 2T).
    """
    # Split per periodo
    df_tot, df_1t, df_2t = _split_per_periodo(df)
    
    return {
        'Totale': calcola_stats_quartetti(df_tot),
        '1T': calcola_stats_quartetti(df_1t),
        '2T': calcola_stats_quartetti(df_2t)
    }


def calcola_report_quinto_uomo_completo(df):
    """
    Calcola le statistiche del quinto uomo con split per periodo (Totale, 1T, 2T).
    """
    # Split per periodo
    df_tot, df_1t, df_2t = _split_per_periodo(df)
    
    return {
        'Totale': calcola_stats_quinto_uomo(df_tot),
        '1T': calcola_stats_quinto_uomo(df_1t),
        '2T': calcola_stats_quinto_uomo(df_2t)
    }
