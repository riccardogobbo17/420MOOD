import pandas as pd

# =========================================================================
# FORMATO TAGGING 2026/27
# -------------------------------------------------------------------------
# Colonne CSV: Name;Position;Duration;Data;Evento;Portiere;Squadra;Chi;Dove;Lato;Esito
# Rispetto al formato precedente non vengono piu raccolti:
#   - Quartetto  -> niente stats quartetti / quinto uomo / minutaggi
#   - Piede      -> niente split piede
#   - Dove/Lato  -> zone non piu utilizzate (le colonne restano nel DB, ignorate)
# Convenzioni del tagging:
#   - 'Squadra' indica chi compie l'azione ('Noi'/'Loro'), 'Chi' e' sempre un
#     nostro giocatore (marcatore, tiratore, chi ribatte, chi subisce il fallo).
#   - Palla persa / Palla recuperata sono taggate solo per noi: 'Squadra' e' vuota.
#   - Un 'Tiro' con Esito='Assist' e' un passaggio decisivo, NON una conclusione.
#   - 'Punizione' ha esiti da conclusione ma non entra nei tiri: conta solo come
#     parata per le statistiche dei portieri.
#   - L'Esito di un 'Gol' e' la tipologia dell'azione che lo ha prodotto.
# =========================================================================

ESITI_IN_PORTA = ['Parata', 'Gol', 'Palo']
TIPOLOGIE_GOL = ['Costruzione', 'Transizione', 'Palla inattiva', 'Errore', 'Autogol']


def _col(df, name):
    """Serie stringa normalizzata per la colonna richiesta (vuota se assente)."""
    if name not in df.columns:
        return pd.Series([''] * len(df), index=df.index, dtype=object)
    return df[name].fillna('').astype(str).str.strip()


def mask_evento(df, nome):
    return _col(df, 'evento').str.contains(nome, na=False)


def mask_tiro(df, squadra=None):
    """Conclusioni vere: esclude i Tiro taggati con Esito='Assist'."""
    m = mask_evento(df, 'Tiro') & (_col(df, 'esito') != 'Assist')
    if squadra is not None:
        m = m & (_col(df, 'squadra') == squadra)
    return m


def mask_gol(df, squadra):
    """Gol segnati da `squadra`, autogol avversario incluso."""
    evento = _col(df, 'evento')
    sq = _col(df, 'squadra')
    avversario = 'Loro' if squadra == 'Noi' else 'Noi'
    return ((evento == 'Gol') & (sq == squadra)) | ((evento == 'Autogol') & (sq == avversario))


def mask_assist(df, squadra='Noi'):
    """Assist: evento 'Assist' oppure Tiro con Esito='Assist'."""
    m = (_col(df, 'evento') == 'Assist') | (mask_evento(df, 'Tiro') & (_col(df, 'esito') == 'Assist'))
    sq = _col(df, 'squadra')
    # Sull'evento Assist la colonna Squadra resta vuota: e' comunque un nostro tag.
    return m & (sq != 'Loro') if squadra == 'Noi' else m & (sq == 'Loro')


def mask_parata(df, squadra='Noi'):
    """Parate del portiere di `squadra`: tiri e punizioni avversarie con Esito='Parata'."""
    avversario = 'Loro' if squadra == 'Noi' else 'Noi'
    conclusioni = (mask_evento(df, 'Tiro') | mask_evento(df, 'Punizione')) & (_col(df, 'squadra') == avversario)
    return conclusioni & (_col(df, 'esito') == 'Parata')


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
    # NOTA 2026/27: il ramo by_zona non e' piu usato dall'app (zone non raccolte).
    # Resta qui per riuso futuro se il tagging delle zone tornera' attivo.
    mask_noi = (df['squadra'] == 'Noi') & (df['evento'].str.contains('Tiro|Laterale|Angolo', na=False))
    if by_zona:
        df_zona = df[mask_noi & (df['dove'].notnull())].copy()
        stat_keys = {
            'gol_fatti': lambda d: d['evento'].str.contains('Gol', na=False) & (d['squadra'] == 'Noi'),
            'tiri_totali': lambda d: d['evento'].str.contains('Tiro', na=False),
            'tiri_in_porta_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & d['esito'].isin(['Parata', 'Gol', 'Palo']),
            'tiri_fuori': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Fuori'),
            'tiri_ribattuti': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Ribattuto'),
            'palo_traversa': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['esito'] == 'Palo'),
            'angoli': lambda d: d['evento'].str.contains('Angolo', na=False),
            'laterale': lambda d: d['evento'].str.contains('Laterale', na=False),
        }
        return _get_zonadict(df_zona, group_key=None, stat_keys=stat_keys)
    else:
        stats = {}
        m_tiro = mask_tiro(df, 'Noi')
        esito = _col(df, 'esito')
        squadra = _col(df, 'squadra')
        stats['gol_fatti'] = int(mask_gol(df, 'Noi').sum())
        stats['assist'] = int(mask_assist(df, 'Noi').sum())
        stats['tiri_totali'] = int(m_tiro.sum())
        stats['tiri_in_porta'] = int((m_tiro & esito.isin(ESITI_IN_PORTA)).sum())
        stats['tiri_fuori'] = int((m_tiro & (esito == 'Fuori')).sum())
        stats['tiri_ribattuti'] = int((m_tiro & (esito == 'Ribattuto')).sum())
        stats['palo_traversa'] = int((m_tiro & (esito == 'Palo')).sum())
        stats['angoli'] = int((mask_evento(df, 'Angolo') & (squadra == 'Noi')).sum())
        stats['laterali'] = int((mask_evento(df, 'Laterale') & (squadra == 'Noi')).sum())
        stats['punizioni'] = int((mask_evento(df, 'Punizione') & (squadra == 'Noi')).sum())
        # stats['rigori'] = len(df[(df['evento'].str.contains('Rigore', na=False)) & (df['squadra'] == 'Noi')])
        # stats['tiri_liberi'] = len(df[(df['evento'].str.contains('Tiro libero', na=False)) & (df['squadra'] == 'Noi')])
        return stats

def calcola_difesa(df, by_zona=False):
    mask_loro = (df['squadra'] == 'Loro') & (df['evento'].str.contains('Tiro|Laterale|Angolo', na=False))
    if by_zona:
        df_zona = df[mask_loro & (df['dove'].notnull())].copy()
        stat_keys = {
            'gol_subiti': lambda d: d['evento'].str.contains('Gol', na=False) & (d['squadra'] == 'Loro'),
            'tiri_totali_subiti': lambda d: d['evento'].str.contains('Tiro', na=False),
            'tiri_in_porta_totali_subiti': lambda d: d['evento'].str.contains('Tiro', na=False) & d['esito'].isin(['Parata', 'Gol', 'Palo']),
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
        m_tiro = mask_tiro(df, 'Loro')
        esito = _col(df, 'esito')
        squadra = _col(df, 'squadra')
        stats['gol_subiti'] = int(mask_gol(df, 'Loro').sum())
        stats['assist_subiti'] = int(mask_assist(df, 'Loro').sum())
        stats['tiri_subiti'] = int(m_tiro.sum())
        stats['tiri_in_porta_subiti'] = int((m_tiro & esito.isin(ESITI_IN_PORTA)).sum())
        stats['tiri_fuori_subiti'] = int((m_tiro & (esito == 'Fuori')).sum())
        stats['tiri_loro_ribattuti_da_noi'] = int((m_tiro & (esito == 'Ribattuto')).sum())
        stats['tiri_loro_palo_traversa'] = int((m_tiro & (esito == 'Palo')).sum())
        stats['angoli_subiti'] = int((mask_evento(df, 'Angolo') & (squadra == 'Loro')).sum())
        stats['laterali_subiti'] = int((mask_evento(df, 'Laterale') & (squadra == 'Loro')).sum())
        stats['punizioni_subite'] = int((mask_evento(df, 'Punizione') & (squadra == 'Loro')).sum())
        # stats['rigori_subiti'] = len(df[(df['evento'].str.contains('Rigore', na=False)) & (df['squadra'] == 'Loro')])
        # stats['tiri_liberi_subiti'] = len(df[(df['evento'].str.contains('Tiro libero', na=False)) & (df['squadra'] == 'Loro')])
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
        stats['palla_recuperata'] = len(df[mask_rec])
        # stats['palla_recuperata_ripartenza'] = len(df[mask_rec & (df['esito'] == 'Ripartenza')])
        # stats['palla_recuperata_costruzione'] = len(df[mask_rec & (df['esito'] == 'Costruzione')])
        # stats['palla_recuperata_fuori'] = len(df[mask_rec & (df['esito'] == 'Fuori')])
        mask_persa = (df['evento'].str.contains('Palla persa', na=False))
        stats['palla_persa'] = len(df[mask_persa])
        # stats['palla_persa_ripartenza'] = len(df[mask_persa & (df['esito'] == 'Ripartenza')])
        # stats['palla_persa_costruzione'] = len(df[mask_persa & (df['esito'] == 'Costruzione')])
        # stats['palla_persa_fuori'] = len(df[mask_persa & (df['esito'] == 'Fuori')])
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
        stats['falli'] = len(df[mask_fatti])
        stats['falli_subiti'] = len(df[mask_subiti])

        # mask_fatti_attacco = mask_fatti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) > 0)
        # mask_fatti_difesa  = mask_fatti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) == 0)
        # mask_subiti_attacco = mask_subiti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) > 0)
        # mask_subiti_difesa  = mask_subiti & (pd.to_numeric(df['dove'], errors='coerce').fillna(0).astype(int) == 0)

        # stats['falli_fatti_zona_attacco'] = len(df[mask_fatti_attacco])
        # stats['falli_fatti_zona_difesa'] = len(df[mask_fatti_difesa])
        # stats['falli_subiti_zona_attacco'] = len(df[mask_subiti_attacco])
        # stats['falli_subiti_zona_difesa'] = len(df[mask_subiti_difesa])

        stats['ammonizioni'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Noi')])
        stats['espulsioni'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Noi')])
        stats['ammonizioni_loro'] = len(df[(df['evento'].str.contains('Ammonizione', na=False)) & (df['squadra'] == 'Loro')])
        stats['espulsioni_loro'] = len(df[(df['evento'].str.contains('Espulsione', na=False)) & (df['squadra'] == 'Loro')])
        return stats

def calcola_ripartenze(df):
    rip = {}
    # Ripartenze create da noi
    # rip['3v2'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('3v2', na=False))])
    # rip['2v2'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('2v2', na=False))])
    # rip['2v1'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('2v1', na=False))])
    # rip['1v1'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi') & (df['esito'].str.contains('1v1', na=False))])
    rip['ripartenze'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Noi')])
    
    # Ripartenze subite da noi (create da loro)
    # rip['3v2_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('3v2', na=False))])
    # rip['2v2_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('2v2', na=False))])
    # rip['2v1_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('2v1', na=False))])
    # rip['1v1_subiti'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro') & (df['esito'].str.contains('1v1', na=False))])
    rip['ripartenze_loro'] = len(df[(df['evento'].str.contains('Ripartenza', na=False)) & (df['squadra'] == 'Loro')])
    return rip


def calcola_tipologia_gol(df):
    """Come nascono i gol: l'Esito dell'evento 'Gol' e' la tipologia dell'azione.

    Gli Autogol sono una tipologia a se: Autogol avversario (Squadra=Loro)
    conta tra i fatti, Autogol nostro (Squadra=Noi) tra i subiti.

    Restituisce {'fatti': {tipologia: n}, 'subiti': {tipologia: n}} con le
    tipologie note sempre presenti (anche a 0) piu' eventuali nuove trovate nel dato.
    """
    evento = _col(df, 'evento')
    esito = _col(df, 'esito')
    squadra = _col(df, 'squadra')

    tipologie = [t for t in TIPOLOGIE_GOL if t != 'Autogol']
    for t in sorted(esito[(evento == 'Gol') & (esito != '')].unique()):
        if t not in tipologie and t != 'Autogol':
            tipologie.append(t)

    def conta(lato):
        avversario = 'Loro' if lato == 'Noi' else 'Noi'
        m_gol = (evento == 'Gol') & (squadra == lato)
        m_autogol = (evento == 'Autogol') & (squadra == avversario)
        conteggi = {t: int((m_gol & (esito == t)).sum()) for t in tipologie}
        conteggi['Autogol'] = int(m_autogol.sum())
        conteggi['non_taggato'] = int((m_gol & (esito == '')).sum())
        return conteggi

    return {'fatti': conta('Noi'), 'subiti': conta('Loro')}

# ----------- STATS INDIVIDUALI -----------

def calcola_stats_individuali(df, by_zona=False):
    def stat_keys_fn():
        return {
            # ATTACCO
            'gol_fatti': lambda d: mask_gol(d, 'Noi'),
            'assist': lambda d: mask_assist(d, 'Noi'),
            'tiri_totali': lambda d: mask_tiro(d, 'Noi'),
            'tiri_in_porta_totali': lambda d: mask_tiro(d, 'Noi') & _col(d, 'esito').isin(ESITI_IN_PORTA),
            'tiri_fuori': lambda d: mask_tiro(d, 'Noi') & (_col(d, 'esito') == 'Fuori'),
            'tiri_ribattuti': lambda d: mask_tiro(d, 'Noi') & (_col(d, 'esito') == 'Ribattuto'),
            'palo_traversa': lambda d: mask_tiro(d, 'Noi') & (_col(d, 'esito') == 'Palo'),
            # PALLE PERSE (taggate solo per noi: colonna Squadra vuota)
            'palle_perse': lambda d: mask_evento(d, 'Palla persa'),
            # DIFESA
            'tiri_ribattuti_noi': lambda d: mask_tiro(d, 'Loro') & (_col(d, 'esito') == 'Ribattuto'),
            'palle_recuperate': lambda d: mask_evento(d, 'Palla recuperata'),
            # FALLI
            'falli_fatti': lambda d: mask_evento(d, 'Fallo') & (_col(d, 'squadra') == 'Noi'),
            'falli_subiti': lambda d: mask_evento(d, 'Fallo') & (_col(d, 'squadra') == 'Loro'),
            'ammonizioni': lambda d: mask_evento(d, 'Ammonizione') & (_col(d, 'squadra') == 'Noi'),
            'espulsioni': lambda d: mask_evento(d, 'Espulsione') & (_col(d, 'squadra') == 'Noi'),
        }

    if by_zona:
        mask = df['dove'].notnull()
        result = _get_zonadict(df[mask], group_key='chi', stat_keys=stat_keys_fn())
        # Aggiungi gol_subiti anche per by_zona
        # Per gol_subiti, controlliamo quartetto e portiere, non chi
        quartetto_cols = ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4',
                         'quartetto.1', 'quartetto.2', 'quartetto.3', 'quartetto.4']
        
        for zona_num, zona_dict in result.items():
            for giocatore in zona_dict.keys():
                # Conta i gol subiti quando il giocatore è presente nel quartetto o come portiere in quella zona
                def is_player_in_field_for_goal(row, player_name):
                    """Verifica se un giocatore è in campo (quartetto o portiere) quando viene subito un gol"""
                    # Controlla nel quartetto
                    for col in quartetto_cols:
                        if col in row and pd.notna(row.get(col)):
                            if str(row.get(col)).strip() == player_name:
                                return True
                    # Controlla come portiere
                    if 'portiere' in row and pd.notna(row.get('portiere')):
                        if str(row.get('portiere')).strip() == player_name:
                            return True
                    return False
                
                gol_subiti = 0
                for idx, row in df.iterrows():
                    if (row.get('dove') == zona_num) and \
                       isinstance(row.get('evento'), str) and 'Gol' in row.get('evento', '') and \
                       row.get('squadra') == 'Loro' and \
                       is_player_in_field_for_goal(row, giocatore):
                        gol_subiti += 1
                
                if giocatore in zona_dict:
                    zona_dict[giocatore]['gol_subiti'] = {'Sx': 0.0, 'Dx': 0.0, 'Tot': gol_subiti}
        return result
    else:
        # Un giocatore compare nelle stats individuali solo se ha almeno un evento
        # nella colonna 'chi'. Senza quartetto non sappiamo piu' chi era in campo,
        # quindi la colonna gol_subiti individuale non e' piu' calcolabile
        # (resta disponibile per i portieri in calcola_stats_portieri_individuali).
        stats = {}
        chi_series = _col(df, 'chi')
        giocatori = sorted({c for c in chi_series.unique() if c})

        for chi in giocatori:
            sub = df[chi_series == chi]
            stats[chi] = {k: int(m(sub).sum()) for k, m in stat_keys_fn().items()}

        # --- LEGACY (quartetto non piu' raccolto) -----------------------------
        # I gol subiti individuali venivano attribuiti ai 4 giocatori in campo
        # leggendo le colonne quartetto/quartetto_1..4. Codice conservato per un
        # eventuale ritorno del tagging del quartetto.
        #
        # quartetto_cols = ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4',
        #                   'quartetto.1', 'quartetto.2', 'quartetto.3', 'quartetto.4']
        # for chi in giocatori:
        #     gol_subiti = 0
        #     for _, row in df.iterrows():
        #         if str(row.get('evento', '')) == 'Gol' and row.get('squadra') == 'Loro':
        #             in_campo = any(
        #                 str(row.get(col, '')).strip() == chi
        #                 for col in quartetto_cols + ['portiere']
        #             )
        #             if in_campo:
        #                 gol_subiti += 1
        #     stats[chi]['gol_subiti'] = gol_subiti
        # ---------------------------------------------------------------------
        return stats

# ----------- STATS PORTIERI -----------

def calcola_stats_portieri_individuali(df, by_zona=False):
    # Le parate includono anche le punizioni avversarie con Esito='Parata'
    # (l'evento Punizione non entra nei tiri, vedi mask_parata).
    def stat_keys_fn():
        return {
            'parate': lambda d: mask_parata(d, 'Noi'),
            # Lanci e integrazione portiere non sono piu' taggati: restano a 0.
            # 'lanci': lambda d: mask_evento(d, 'Lancio') & (_col(d, 'squadra') == 'Noi'),
            # 'lanci_corretti': lambda d: mask_evento(d, 'Lancio') & (_col(d, 'squadra') == 'Noi') & _col(d, 'esito').isin(['Gol', 'OK']),
            # 'lanci_sbagliati': lambda d: mask_evento(d, 'Lancio') & (_col(d, 'squadra') == 'Noi') & _col(d, 'esito').isin(['Intercetto', 'Fuori', '']),
            # 'integrazione_portiere': lambda d: mask_evento(d, 'Integrazione portier') & (_col(d, 'squadra') == 'Noi'),
            # 'integrazione_portiere_ok': lambda d: mask_evento(d, 'Integrazione portier') & (_col(d, 'squadra') == 'Noi') & _col(d, 'esito').isin(['Gol', 'OK']),
            # 'integrazione_portiere_ko': lambda d: mask_evento(d, 'Integrazione portier') & (_col(d, 'squadra') == 'Noi') & _col(d, 'esito').isin(['Intercetto', 'Fuori', '']),
        }

    if by_zona:
        mask = df['dove'].notnull()
        return _get_zonadict(df[mask], group_key='portiere', stat_keys=stat_keys_fn())
    else:
        stats = {}
        portiere_series = _col(df, 'portiere')
        for portiere in sorted({p for p in portiere_series.unique() if p}):
            sub = df[portiere_series == portiere]
            portiere_stats = {k: int(m(sub).sum()) for k, m in stat_keys_fn().items()}
            gol_subiti = int(mask_gol(sub, 'Loro').sum())
            parate = portiere_stats.get('parate', 0)
            tiri_in_porta_subiti = parate + gol_subiti
            portiere_stats['gol_subiti'] = gol_subiti
            portiere_stats['tiri_in_porta_subiti'] = tiri_in_porta_subiti
            portiere_stats['percentuale_parate'] = round((parate / tiri_in_porta_subiti) * 100, 1) if tiri_in_porta_subiti > 0 else 0.0
            stats[portiere] = portiere_stats
        return stats

def calcola_stats_portieri_squadra(df, squadra='Noi'):
    parate = int(mask_parata(df, squadra).sum())
    gol_subiti = int(mask_gol(df, 'Loro' if squadra == 'Noi' else 'Noi').sum())
    tiri_in_porta_subiti = parate + gol_subiti

    stats = {
        'parate': parate,
        'gol_subiti': gol_subiti,
        'tiri_in_porta_subiti': tiri_in_porta_subiti,
        'percentuale_parate': round((parate / tiri_in_porta_subiti) * 100, 1) if tiri_in_porta_subiti > 0 else 0.0,
    }

    # LEGACY: lanci e integrazione portiere non sono piu' taggati.
    # mask_sq = (df['squadra'] == squadra)
    # mask_lancio = (df['evento'].str.contains('Lancio', na=False)) & mask_sq
    # stats['lanci'] = len(df[mask_lancio])
    # stats['lanci_corretti'] = len(df[mask_lancio & (df['esito'].isin(['Gol', 'OK']))])
    # stats['lanci_sbagliati'] = len(df[mask_lancio & (df['esito'].isin(['Intercetto', 'Fuori', '', None]))])
    # mask_int = (df['evento'].str.contains('Integrazione portier', na=False)) & mask_sq
    # stats['integrazione_portiere'] = len(df[mask_int])
    # stats['integrazione_portiere_ok'] = len(df[mask_int & (df['esito'].isin(['Gol', 'OK']))])
    # stats['integrazione_portiere_ko'] = len(df[mask_int & (df['esito'].isin(['Intercetto', 'Fuori', '', None]))])
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

def _pct(numeratore, denominatore):
    """Percentuale 0–100 arrotondata a 1 decimale; None se denominatore=0."""
    if not denominatore:
        return None
    return round((numeratore / denominatore) * 100, 1)


def calcola_kpi_executive(df):
    """KPI executive Noi vs Loro per copertina / dashboard PDF."""
    esito = _col(df, 'esito')
    squadra = _col(df, 'squadra')

    def side_stats(lato):
        mask_sq = squadra == lato
        m_tiro = mask_tiro(df, lato)
        tiri = int(m_tiro.sum())
        in_porta = int((m_tiro & esito.isin(ESITI_IN_PORTA)).sum())
        gol = int(mask_gol(df, lato).sum())

        # Palla persa / recuperata sono taggate solo per noi (Squadra vuota):
        # attribuirle a 'Loro' non avrebbe senso, restano a 0 per l'avversario.
        if lato == 'Noi':
            recuperi = int(mask_evento(df, 'Palla recuperata').sum())
            perse = int(mask_evento(df, 'Palla persa').sum())
        else:
            recuperi = None
            perse = None

        parate = int(mask_parata(df, lato).sum())
        gol_subiti = int(mask_gol(df, 'Loro' if lato == 'Noi' else 'Noi').sum())

        return {
            'gol': gol,
            'assist': int(mask_assist(df, lato).sum()),
            'tiri': tiri,
            'tiri_in_porta': in_porta,
            'efficacia_tiro_pct': _pct(in_porta, tiri),
            'conversione_pct': _pct(gol, in_porta),
            'recuperi': recuperi,
            'perse': perse,
            'falli': int((mask_sq & mask_evento(df, 'Fallo')).sum()),
            'gialli': int((mask_sq & mask_evento(df, 'Ammonizione')).sum()),
            'rossi': int((mask_sq & mask_evento(df, 'Espulsione')).sum()),
            'angoli': int((mask_sq & mask_evento(df, 'Angolo')).sum()),
            'laterali': int((mask_sq & mask_evento(df, 'Laterale')).sum()),
            'punizioni': int((mask_sq & mask_evento(df, 'Punizione')).sum()),
            'parate': parate,
            'perc_parate': _pct(parate, parate + gol_subiti),
        }

    return {
        'Noi': side_stats('Noi'),
        'Loro': side_stats('Loro'),
        'tipologia_gol': calcola_tipologia_gol(df),
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
    report['kpi_executive'] = calcola_kpi_executive(df)
    report['tipologia_gol'] = calcola_tipologia_gol(df)

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

    NON USATA nel formato 2026/27: la colonna Quartetto non viene piu' raccolta,
    quindi la funzione restituirebbe sempre {}. Conservata per riuso futuro.
    """
    # Filtra solo le righe con 4 giocatori di movimento (escludi portiere)
    df_quartetti = df.copy()
    
    # Crea una colonna per identificare i quartetti
    def get_quartetto(row):
        # Prendi i 4 giocatori di movimento (escludi portiere)
        giocatori = []
        player_cols_supabase = ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4']
        player_cols_csv = ['quartetto', 'quartetto.1', 'quartetto.2', 'quartetto.3', 'quartetto.4']

        # Prova prima i nomi delle colonne del database Supabase
        for col in player_cols_supabase:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                giocatori.append(str(row[col]).strip())

        # Se non troviamo giocatori, prova i nomi delle colonne normalizzate dal CSV
        if not giocatori:
            for col in player_cols_csv:
                if col in row and pd.notna(row[col]) and str(row[col]).strip():
                    giocatori.append(str(row[col]).strip())

        giocatori_unici = sorted({g for g in giocatori if g})

        # Se abbiamo esattamente 4 giocatori, crea il quartetto
        if len(giocatori_unici) == 4:
            return ';'.join(giocatori_unici)
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
        stats['tiri_in_porta'] = len(gruppo[mask_tiro & gruppo['esito'].isin(['Parata', 'Gol', 'Palo'])])
        stats['tiri_fuori'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Fuori')])
        stats['tiri_ribattuti'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Ribattuto')])
        stats['palo_traversa'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Palo')])
        stats['angoli'] = len(gruppo[(gruppo['evento'].str.contains('Angolo', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['laterali'] = len(gruppo[(gruppo['evento'].str.contains('Laterale', na=False)) & (gruppo['squadra'] == 'Noi')])
        
        # DIFESA
        mask_tiro_loro = (gruppo['evento'].str.contains('Tiro', na=False)) & (gruppo['squadra'] == 'Loro')
        stats['tiri_subiti'] = len(gruppo[mask_tiro_loro])
        stats['tiri_in_porta_subiti'] = len(gruppo[mask_tiro_loro & gruppo['esito'].isin(['Parata', 'Gol', 'Palo'])])
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
    Raggruppa le statistiche per ciascun quintetto di giocatori di movimento.

    NON USATA nel formato 2026/27 (nessuna colonna Quartetto). Il power play si
    legge dall'evento '5v4'. Conservata per riuso futuro.
    """
    df_quinto = df.copy()

    def get_quintetto(row):
        # Escludi le situazioni con portiere in campo
        portiere = row.get('portiere')
        if pd.notna(portiere) and str(portiere).strip():
            return None

        giocatori = []
        player_cols_supabase = ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4']
        player_cols_csv = ['quartetto', 'quartetto.1', 'quartetto.2', 'quartetto.3', 'quartetto.4']

        for col in player_cols_supabase:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                giocatori.append(str(row[col]).strip())

        if not giocatori:
            for col in player_cols_csv:
                if col in row and pd.notna(row[col]) and str(row[col]).strip():
                    giocatori.append(str(row[col]).strip())

        giocatori_unici = sorted({g for g in giocatori if g})

        if len(giocatori_unici) == 5:
            return ';'.join(giocatori_unici)
        return None

    df_quinto['quintetto_id'] = df_quinto.apply(get_quintetto, axis=1)
    df_quinto = df_quinto[df_quinto['quintetto_id'].notna()]

    if df_quinto.empty:
        return {}

    stats_quintetti = {}

    for quintetto, gruppo in df_quinto.groupby('quintetto_id'):
        stats = {}

        # GOL
        stats['gol_fatti'] = len(gruppo[(gruppo['evento'].str.contains('Gol', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['gol_subiti'] = len(gruppo[(gruppo['evento'].str.contains('Gol', na=False)) & (gruppo['squadra'] == 'Loro')])

        # ATTACCO
        mask_tiro = (gruppo['evento'].str.contains('Tiro', na=False)) & (gruppo['squadra'] == 'Noi')
        stats['tiri_totali'] = len(gruppo[mask_tiro])
        stats['tiri_in_porta'] = len(gruppo[mask_tiro & gruppo['esito'].isin(['Parata', 'Gol', 'Palo'])])
        stats['tiri_fuori'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Fuori')])
        stats['tiri_ribattuti'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Ribattuto')])
        stats['palo_traversa'] = len(gruppo[mask_tiro & (gruppo['esito'] == 'Palo')])
        stats['angoli'] = len(gruppo[(gruppo['evento'].str.contains('Angolo', na=False)) & (gruppo['squadra'] == 'Noi')])
        stats['laterali'] = len(gruppo[(gruppo['evento'].str.contains('Laterale', na=False)) & (gruppo['squadra'] == 'Noi')])

        # DIFESA
        mask_tiro_loro = (gruppo['evento'].str.contains('Tiro', na=False)) & (gruppo['squadra'] == 'Loro')
        stats['tiri_subiti'] = len(gruppo[mask_tiro_loro])
        stats['tiri_in_porta_subiti'] = len(gruppo[mask_tiro_loro & gruppo['esito'].isin(['Parata', 'Gol', 'Palo'])])
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

        stats_quintetti[quintetto] = stats

    return stats_quintetti


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
