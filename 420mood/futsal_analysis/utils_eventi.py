import pandas as pd

def _get_zonadict(df, group_key, stat_keys):
    """Restituisce dict: zona -> (chi/portiere/None) -> stats dict."""
    df = df.copy()
    df['zona'] = pd.to_numeric(df['field_position'], errors='coerce').astype('Int64')
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
        df_zona = df[mask_noi & (df['field_position'].notnull())].copy()
        stat_keys = {
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
        stats['tiri_totali'] = len(df[mask_tiro])
        stats['tiri_in_porta_totali'] = len(df[mask_tiro & df['esito'].isin(['Parata', 'Gol'])])
        stats['tiri_fuori'] = len(df[mask_tiro & (df['esito'] == 'Fuori')])
        stats['tiri_ribattuti'] = len(df[mask_tiro & (df['esito'] == 'Ribattuto')])
        stats['palo_traversa'] = len(df[mask_tiro & (df['esito'] == 'Palo')])
        stats['angoli'] = len(df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Noi')])
        stats['laterale'] = len(df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Noi')])
        return stats

def calcola_difesa(df, by_zona=False):
    mask_loro = (df['squadra'] == 'Loro') & (df['evento'].str.contains('Tiro|Laterale|Angolo', na=False))
    if by_zona:
        df_zona = df[mask_loro & (df['field_position'].notnull())].copy()
        stat_keys = {
            'tiri_totali_subiti': lambda d: d['evento'].str.contains('Tiro', na=False),
            'tiri_in_porta_totali_subiti': lambda d: d['evento'].str.contains('Tiro', na=False) & d['esito'].isin(['Parata', 'Gol']),
            'tiri_fuori_loro': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Fuori'),
            'tiri_ribattuti_da_noi': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Ribattuto'),
            'palo_traversa_loro': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Palo'),
            'angoli_loro': lambda d: d['evento'].str.contains('Angolo', na=False),
            'laterale_loro': lambda d: d['evento'].str.contains('Laterale', na=False),
        }
        return _get_zonadict(df_zona, group_key=None, stat_keys=stat_keys)
    else:
        stats = {}
        mask_tiro = (df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro')
        stats['tiri_totali_subiti'] = len(df[mask_tiro])
        stats['tiri_in_porta_totali_subiti'] = len(df[mask_tiro & df['esito'].isin(['Parata', 'Gol'])])
        stats['tiri_fuori_loro'] = len(df[mask_tiro & (df['esito'] == 'Fuori')])
        stats['tiri_ribattuti_noi'] = len(df[mask_tiro & (df['esito'] == 'Ribattuto')])
        stats['palo_traversa_loro'] = len(df[mask_tiro & (df['esito'] == 'Palo')])
        stats['angoli_loro'] = len(df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Loro')])
        stats['laterale_loro'] = len(df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Loro')])
        return stats

def calcola_palle_recuperate_perse(df, by_zona=False):
    mask_noi = (df['squadra'] == 'Noi') & (df['evento'].str.contains('Palla recuperata|Palla persa', na=False))
    if by_zona:
        df_zona = df[mask_noi & (df['field_position'].notnull())].copy()
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
        mask_falli = df['evento'].str.contains('Fallo', na=False) & df['field_position'].notnull()
        df_falli = df[mask_falli].copy()
        df_falli['fieldpos'] = pd.to_numeric(df_falli['field_position'], errors='coerce').astype('Int64')
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
        stats['falli_fatti_totali'] = len(df[mask_fatti])
        stats['falli_subiti_totali'] = len(df[mask_subiti])

        mask_fatti_attacco = mask_fatti & (df['field_position'] > 0)
        mask_fatti_difesa  = mask_fatti & (df['field_position'] == 0)
        mask_subiti_attacco = mask_subiti & (df['field_position'] > 0)
        mask_subiti_difesa  = mask_subiti & (df['field_position'] == 0)

        stats['falli_fatti_zona_attacco'] = len(df[mask_fatti_attacco])
        stats['falli_fatti_zona_difesa'] = len(df[mask_fatti_difesa])
        stats['falli_subiti_zona_attacco'] = len(df[mask_subiti_attacco])
        stats['falli_subiti_zona_difesa'] = len(df[mask_subiti_difesa])

        stats['ammonizioni_noi'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Noi')])
        stats['espulsioni_noi'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Noi')])
        stats['ammonizioni_loro'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Loro')])
        stats['espulsioni_loro'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Loro')])
        return stats

def calcola_ripartenze(df):
    rip = {}
    rip['3v2'] = len(df[(df['evento'].str.contains('3v2', na=False)) & (df['squadra'] == 'Noi')])
    rip['2v2'] = len(df[(df['evento'].str.contains('2v2', na=False)) & (df['squadra'] == 'Noi')])
    rip['2v1'] = len(df[(df['evento'].str.contains('2v1', na=False)) & (df['squadra'] == 'Noi')])
    rip['1v1'] = len(df[(df['evento'].str.contains('1v1', na=False)) & (df['squadra'] == 'Noi')])
    rip['3v2_subiti'] = len(df[(df['evento'].str.contains('3v2', na=False)) & (df['squadra'] == 'Loro')])
    rip['2v2_subiti'] = len(df[(df['evento'].str.contains('2v2', na=False)) & (df['squadra'] == 'Loro')])
    rip['2v1_subiti'] = len(df[(df['evento'].str.contains('2v1', na=False)) & (df['squadra'] == 'Loro')])
    rip['1v1_subiti'] = len(df[(df['evento'].str.contains('1v1', na=False)) & (df['squadra'] == 'Loro')])
    return rip

# ----------- STATS INDIVIDUALI -----------

def calcola_stats_individuali(df, by_zona=False):
    def stat_keys_fn():
        return {
            # ATTACCO
            'tiri_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi'),
            'tiri_in_porta_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & d['esito'].isin(['Parata', 'Gol']),
            'tiri_fuori': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & (d['esito'] == 'Fuori'),
            'tiri_ribattuti': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & (d['esito'] == 'Ribattuto'),
            'palo_traversa': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & (d['esito'] == 'Palo'),
            # PALLE PERSE
            'palla_persa_totali': lambda d: d['evento'].str.contains('Palla persa', na=False),
            'palla_persa_ripartenza': lambda d: d['evento'].str.contains('Palla persa', na=False) & (d['esito'] == 'Ripartenza'),
            'palla_persa_costruzione': lambda d: d['evento'].str.contains('Palla persa', na=False) & (d['esito'] == 'Costruzione'),
            'palla_persa_fuori': lambda d: d['evento'].str.contains('Palla persa', na=False) & (d['esito'] == 'Fuori'),
            # DIFESA
            'tiri_ribattuti_noi': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Loro') & (d['esito'] == 'Ribattuto'),
            'palla_recuperata_totali': lambda d: d['evento'].str.contains('Palla recuperata', na=False),
            'palla_recuperata_ripartenza': lambda d: d['evento'].str.contains('Palla recuperata', na=False) & (d['esito'] == 'Ripartenza'),
            'palla_recuperata_costruzione': lambda d: d['evento'].str.contains('Palla recuperata', na=False) & (d['esito'] == 'Costruzione'),
            'palla_recuperata_fuori': lambda d: d['evento'].str.contains('Palla recuperata', na=False) & (d['esito'] == 'Fuori'),
            # FALLI
            'falli_fatti_totali': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Noi'),
            'falli_subiti_totali': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Loro'),
            'falli_fatti_zona_attacco': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Noi') & (d['field_position'].fillna(1).astype(int) == 0),
            'falli_fatti_zona_difesa': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Noi') & (d['field_position'].fillna(1).astype(int) > 0),
            'falli_subiti_zona_attacco': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Loro') & (d['field_position'].fillna(1).astype(int) == 0),
            'falli_subiti_zona_difesa': lambda d: d['evento'].str.contains('Fallo', na=False) & (d['squadra'] == 'Loro') & (d['field_position'].fillna(1).astype(int) > 0),
            'ammonizioni': lambda d: d['evento'].str.contains('Ammonizione', na=False) & (d['squadra'] == 'Noi'),
            'espulsioni': lambda d: d['evento'].str.contains('Espulsione', na=False) & (d['squadra'] == 'Noi'),
        }

    if by_zona:
        mask = df['field_position'].notnull()
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
            'integrazione_portiere': lambda d: (d['evento'].str.contains('Integrazione portiere', na=False)) & (d['squadra'] == 'Noi'),
            'integrazione_portiere_ok': lambda d: (d['evento'].str.contains('Integrazione portiere', na=False)) & (d['squadra'] == 'Noi') & (d['esito'].isin(['', None])),
            'integrazione_portiere_ko': lambda d: (d['evento'].str.contains('Integrazione portiere', na=False)) & (d['squadra'] == 'Noi') & (d['esito'].isin(['Intercetto', 'Fuori'])),
        }

    if by_zona:
        mask = df['field_position'].notnull()
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

    mask_int = (df['evento'].str.contains('Integrazione portiere', na=False)) & mask_sq
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
        'attacco': calcola_attacco(df, by_zona=False),
        'difesa': calcola_difesa(df, by_zona=False),
        'palle_recuperate_perse': calcola_palle_recuperate_perse(df, by_zona=False),
        'ripartenze': calcola_ripartenze(df),  # Non ha parametro by_zona
        'falli': calcola_falli(df, by_zona=False),
        'portieri_noi': calcola_stats_portieri_squadra(df, squadra='Noi'),
        'portieri_loro': calcola_stats_portieri_squadra(df, squadra='Loro')
    }

    # STATS INDIVIDUALI GIOCATORI (dizionario)
    report['individuali'] = calcola_stats_individuali(df, by_zona=False)

    # STATS PORTIERI INDIVIDUALI (dizionario)
    report['portieri_individuali'] = calcola_stats_portieri_individuali(df, by_zona=False)

    return report
