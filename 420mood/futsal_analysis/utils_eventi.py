
import pandas as pd

def calcola_attacco(df):
    df = df.copy()
    df['fieldpos'] = pd.to_numeric(df['field_position'], errors='coerce').fillna(0).astype(int)
    att = {}
    att['tiri_totali'] = len(df[(df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Noi')])
    att['tiri_in_porta_totali'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'].isin(['Parata', 'Gol']))
    ])
    att['tiri_fuori'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Fuori')
    ])
    att['tiri_ribattuti'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Ribattuto')
    ])
    att['palo_traversa'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Palo')
    ])
    att['angoli'] = len(df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Noi')])
    att['laterale'] = len(df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Noi')])
    att['laterale_zona_attacco'] = len(df[
        (df['evento'].str.contains('Laterale', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['fieldpos'] > 0)
    ])
    att['laterale_zona_difesa'] = len(df[
        (df['evento'].str.contains('Laterale', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['fieldpos'] == 0)
    ])
    return att


def calcola_difesa(df):
    df = df.copy()
    df['fieldpos'] = pd.to_numeric(df['field_position'], errors='coerce').fillna(0).astype(int)
    dif = {}
    dif['tiri_totali_subiti'] = len(df[(df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro')])
    dif['tiri_in_porta_totali_subiti'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['esito'].isin(['Parata', 'Gol']))
    ])
    dif['tiri_fuori_loro'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['esito'] == 'Fuori')
    ])
    dif['tiri_ribattuti_noi'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['esito'] == 'Ribattuto')
    ])
    dif['palo_traversa_loro'] = len(df[
        (df['evento'].str.contains('Tiro', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['esito'] == 'Palo')
    ])
    dif['angoli_loro'] = len(df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Loro')])
    dif['laterale_loro'] = len(df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Loro')])
    dif['laterale_zona_attacco_loro'] = len(df[
        (df['evento'].str.contains('Laterale', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['fieldpos'] > 0)
    ])
    dif['laterale_zona_difesa_loro'] = len(df[
        (df['evento'].str.contains('Laterale', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['fieldpos'] == 0)
    ])
    return dif


def calcola_palle_recuperate_perse(df):
    palle = {}
    palle['palla_recuperata_totali'] = len(df[(df['evento'].str.contains('Palla recuperata', na=False)) & (df['squadra'] == 'Noi')])
    palle['palla_recuperata_ripartenza'] = len(df[
        (df['evento'].str.contains('Palla recuperata', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Ripartenza')
    ])
    palle['palla_recuperata_costruzione'] = len(df[
        (df['evento'].str.contains('Palla recuperata', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Costruzione')
    ])
    palle['palla_recuperata_fuori'] = len(df[
        (df['evento'].str.contains('Palla recuperata', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Fuori')
    ])
    palle['palla_persa_totali'] = len(df[(df['evento'].str.contains('Palla persa', na=False)) & (df['squadra'] == 'Noi')])
    palle['palla_persa_ripartenza'] = len(df[
        (df['evento'].str.contains('Palla persa', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Ripartenza')
    ])
    palle['palla_persa_costruzione'] = len(df[
        (df['evento'].str.contains('Palla persa', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Costruzione')
    ])
    palle['palla_persa_fuori'] = len(df[
        (df['evento'].str.contains('Palla persa', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['esito'] == 'Fuori')
    ])
    return palle


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


def calcola_falli(df):
    df = df.copy()
    df['fieldpos'] = pd.to_numeric(df['field_position'], errors='coerce').fillna(0).astype(int)
    falli = {}
    falli['falli_fatti_totali'] = len(df[(df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Noi')])
    falli['falli_subiti_totali'] = len(df[(df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Loro')])
    falli['falli_fatti_zona_attacco'] = len(df[
        (df['evento'].str.contains('Fallo', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['fieldpos'] == 0)
    ])
    falli['falli_fatti_zona_difesa'] = len(df[
        (df['evento'].str.contains('Fallo', na=False)) &
        (df['squadra'] == 'Noi') &
        (df['fieldpos'] > 0)
    ])
    falli['falli_subiti_zona_attacco'] = len(df[
        (df['evento'].str.contains('Fallo', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['fieldpos'] == 0)
    ])
    falli['falli_subiti_zona_difesa'] = len(df[
        (df['evento'].str.contains('Fallo', na=False)) &
        (df['squadra'] == 'Loro') &
        (df['fieldpos'] > 0)
    ])
    falli['ammonizioni_noi'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Noi')])
    falli['espulsioni_noi'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Noi')])
    falli['ammonizioni_loro'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Loro')])
    falli['espulsioni_loro'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Loro')])
    return falli


def calcola_stats_individuali(df):
    df = df.copy()
    df['fieldpos'] = pd.to_numeric(df['field_position'], errors='coerce').fillna(0).astype(int)
    stats = pd.DataFrame()
    # ATTACCO
    mask_tiro = (df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Noi')
    mask_tiro_in_porta = mask_tiro & (df['esito'].isin(['Parata', 'Gol']))
    mask_tiro_fuori = mask_tiro & (df['esito'] == 'Fuori')
    mask_tiro_ribattuto = mask_tiro & (df['esito'] == 'Ribattuto')
    mask_tiro_palo = mask_tiro & (df['esito'] == 'Palo')

    stats['tiri_totali'] = df[mask_tiro].groupby('chi').size()
    stats['tiri_in_porta_totali'] = df[mask_tiro_in_porta].groupby('chi').size()
    stats['tiri_fuori'] = df[mask_tiro_fuori].groupby('chi').size()
    stats['tiri_ribattuti'] = df[mask_tiro_ribattuto].groupby('chi').size()
    stats['palo_traversa'] = df[mask_tiro_palo].groupby('chi').size()

    # PALLE PERSE
    mask_persa = (df['evento'].str.contains('Palla persa', na=False)) & (df['squadra'] == 'Noi')
    stats['palla_persa_totali'] = df[mask_persa].groupby('chi').size()
    stats['palla_persa_ripartenza'] = df[mask_persa & (df['esito'] == 'Ripartenza')].groupby('chi').size()
    stats['palla_persa_costruzione'] = df[mask_persa & (df['esito'] == 'Costruzione')].groupby('chi').size()
    stats['palla_persa_fuori'] = df[mask_persa & (df['esito'] == 'Fuori')].groupby('chi').size()

    # DIFESA
    mask_ribattuto_noi = (df['evento'].str.contains('Tiro', na=False)) & (df['esito'] == 'Ribattuto') & (df['squadra'] == 'Loro')
    stats['tiri_ribattuti_noi'] = df[mask_ribattuto_noi].groupby('chi').size()

    mask_recuperata = (df['evento'].str.contains('Palla recuperata', na=False)) & (df['squadra'] == 'Noi')
    stats['palla_recuperata_totali'] = df[mask_recuperata].groupby('chi').size()
    stats['palla_recuperata_ripartenza'] = df[mask_recuperata & (df['esito'] == 'Ripartenza')].groupby('chi').size()
    stats['palla_recuperata_costruzione'] = df[mask_recuperata & (df['esito'] == 'Costruzione')].groupby('chi').size()
    stats['palla_recuperata_fuori'] = df[mask_recuperata & (df['esito'] == 'Fuori')].groupby('chi').size()

    # FALLI (fatti/subiti, zone, ammonizioni, espulsioni)
    mask_fallo_noi = (df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Noi')
    mask_fallo_loro = (df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Loro')
    stats['falli_fatti_totali'] = df[mask_fallo_noi].groupby('chi').size()
    stats['falli_subiti_totali'] = df[mask_fallo_loro].groupby('chi').size()

    mask_attacco = df['fieldpos'] == 0
    mask_difesa = df['fieldpos'] > 0

    stats['falli_fatti_zona_attacco'] = df[mask_fallo_noi & mask_attacco].groupby('chi').size()
    stats['falli_fatti_zona_difesa'] = df[mask_fallo_noi & mask_difesa].groupby('chi').size()
    stats['falli_subiti_zona_attacco'] = df[mask_fallo_loro & mask_attacco].groupby('chi').size()
    stats['falli_subiti_zona_difesa'] = df[mask_fallo_loro & mask_difesa].groupby('chi').size()

    stats['ammonizioni'] = df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Noi')].groupby('chi').size()
    stats['espulsioni'] = df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Noi')].groupby('chi').size()

    # Riempio con zeri dove non ci sono valori (giocatori che non hanno fatto quell'evento)
    stats = stats.fillna(0).astype(int)
    return stats


def calcola_stats_portieri_squadra(df, squadra='Noi'):
    mask_sq = (df['squadra'] == squadra)

    # Parate
    if squadra == 'Noi':
        mask_parata = ((df['evento'].str.contains('Parata', na=False)) & mask_sq) | \
                      ((df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro') & (df['esito'] == 'Parata'))
    else:
        mask_parata = ((df['evento'].str.contains('Parata', na=False)) & mask_sq) | \
                      ((df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Noi') & (df['esito'] == 'Parata'))

    # Lanci
    mask_lancio = (df['evento'].str.contains('Lancio', na=False)) & mask_sq
    mask_lancio_ok = mask_lancio & (df['esito'].isin(['Gol', '', None]))
    mask_lancio_ko = mask_lancio & (df['esito'].isin(['Intercetto', 'Fuori']))

    # Integrazione portiere
    mask_int = (df['evento'].str.contains('Integrazione portiere', na=False)) & mask_sq
    mask_int_ok = mask_int & (df['esito'].isin(['', None]))
    mask_int_ko = mask_int & (df['esito'].isin(['Intercetto', 'Fuori']))

    # Calcolo stats
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


def calcola_stats_portieri_individuali(df):
    mask_sq = (df['squadra'] == 'Noi')
    stats = pd.DataFrame()

    # Parate: evento 'Parata' noi oppure evento 'Tiro' loro con esito 'Parata'
    mask_parata = ((df['evento'].str.contains('Parata', na=False)) & mask_sq) | \
                  ((df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro') & (df['esito'] == 'Parata'))
    stats['parate'] = df[mask_parata].groupby('portiere').size()

    # Lanci
    mask_lancio = (df['evento'].str.contains('Lancio', na=False)) & mask_sq
    mask_lancio_ok = mask_lancio & (df['esito'].isin(['Gol', '', None]))
    mask_lancio_ko = mask_lancio & (df['esito'].isin(['Intercetto', 'Fuori']))
    stats['lanci'] = df[mask_lancio].groupby('portiere').size()
    stats['lanci_corretti'] = df[mask_lancio_ok].groupby('portiere').size()
    stats['lanci_sbagliati'] = df[mask_lancio_ko].groupby('portiere').size()

    # Integrazione portiere
    mask_int = (df['evento'].str.contains('Integrazione portiere', na=False)) & mask_sq
    mask_int_ok = mask_int & (df['esito'].isin(['', None]))
    mask_int_ko = mask_int & (df['esito'].isin(['Intercetto', 'Fuori']))
    stats['integrazione_portiere'] = df[mask_int].groupby('portiere').size()
    stats['integrazione_portiere_ok'] = df[mask_int_ok].groupby('portiere').size()
    stats['integrazione_portiere_ko'] = df[mask_int_ko].groupby('portiere').size()

    # Totale di squadra (sommando tutti i portieri)
    stats.loc['TOTALE'] = stats.sum()
    stats = stats.fillna(0).astype(int)
    return stats


def calcola_report_completo(df):
    """
    Restituisce tutte le statistiche aggregate in un unico dizionario strutturato:
      - report['squadra']           : stats di squadra (tutte le sezioni)
      - report['individuali']       : DataFrame stats individuali giocatori
      - report['portieri_individuali'] : DataFrame stats individuali portieri (con TOTALE)
    """
    report = {}

    # STATS DI SQUADRA
    report['squadra'] = {
        'attacco': calcola_attacco(df),
        'difesa': calcola_difesa(df),
        'palle_recuperate_perse': calcola_palle_recuperate_perse(df),
        'ripartenze': calcola_ripartenze(df),
        'falli': calcola_falli(df),
        'portieri_noi': calcola_stats_portieri_squadra(df, squadra='Noi'),
        'portieri_loro': calcola_stats_portieri_squadra(df, squadra='Loro')
    }

    # STATS INDIVIDUALI GIOCATORI
    report['individuali'] = calcola_stats_individuali(df)

    # STATS PORTIERI INDIVIDUALI (solo nostri, con riga TOTALE)
    report['portieri_individuali'] = calcola_stats_portieri_individuali(df)

    return report
