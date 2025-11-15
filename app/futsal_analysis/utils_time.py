import numpy as np
import pandas as pd


def _prepare_single_match(df_single):
    """Restituisce una copia del dataframe con l'indice originale preservato."""
    df_local = df_single.reset_index(drop=False).rename(columns={'index': '__orig_index'})
    return df_local


def _find_event_index(df_local, event_name):
    """Restituisce il primo indice dell'evento specificato, se presente."""
    idx_list = df_local[df_local['evento'] == event_name].index.tolist()
    return idx_list[0] if idx_list else None


def to_seconds(time_str):
    if pd.isna(time_str):
        return np.nan
    t = time_str.split(':')
    return int(t[0]) * 3600 + int(t[1]) * 60 + float(t[2]) if len(t) == 3 else np.nan

def format_mmss(seconds):
    if pd.isna(seconds): return ''
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02}:{s:02}"

def calcola_durate(df):
    idx_fp = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_sp = idx_fp + 1
    idx_end = df[df['evento'] == 'Fine partita'].index[0]

    # Funzione helper per pulire i valori di tempo
    def clean_time_value(time_val):
        if pd.isna(time_val) or time_val == '' or time_val is None:
            return "00:00"
        time_str = str(time_val).strip()
        if not time_str or ':' not in time_str:
            return "00:00"
        return time_str

    # Pulisci i valori di tempo prima di usarli
    tempo_start = clean_time_value(df.loc[0, 'tempoReale'])
    tempo_fine_primo = clean_time_value(df.loc[idx_fp, 'tempoReale'])
    tempo_start_secondo = clean_time_value(df.loc[idx_sp, 'tempoReale'])
    tempo_fine_partita = clean_time_value(df.loc[idx_end, 'tempoReale'])

    durata_primo = differenza_tempi(tempo_start, tempo_fine_primo, format='MM:SS')
    durata_secondo = differenza_tempi(tempo_start_secondo, tempo_fine_partita, format='MM:SS')

    try:
        durata_totale = format_mmss(pd.to_timedelta("00:" + durata_primo).total_seconds() + pd.to_timedelta("00:" + durata_secondo).total_seconds())
    except (ValueError, TypeError):
        durata_totale = "00:00"
    
    dati_durate = pd.DataFrame({
        "Periodo": ["1T", "2T", "Totale"],
        "Durata_minuti": [durata_primo, durata_secondo, durata_totale],
    })
    return dati_durate

def differenza_tempi(t1, t2, format=''):
    if format == 'MM:SS':
        t1, t2 = '00:' + t1, '00:' + t2
    td1, td2 = pd.to_timedelta(t1), pd.to_timedelta(t2)
    total = int((td2 - td1).total_seconds())
    return f"{total//60:02}:{total%60:02}"

def _calcola_tempo_effettivo_single(df_single):
    df_local = _prepare_single_match(df_single)

    if df_local.empty:
        return pd.Series([], index=df_local['__orig_index'])

    df_local['Posizione_sec'] = df_local['posizione'].apply(to_seconds)

    idx_fine_primo = _find_event_index(df_local, 'Fine primo tempo')
    if idx_fine_primo is None:
        # Se non troviamo il fine primo tempo, restituiamo valori vuoti per evitare crash
        valori = ['' for _ in range(len(df_local))]
        return pd.Series(valori, index=df_local['__orig_index'])

    idx_start_secondo = _find_event_index(df_local, 'Inizio secondo tempo')
    if idx_start_secondo is None or idx_start_secondo <= idx_fine_primo:
        idx_start_secondo = idx_fine_primo + 1 if idx_fine_primo + 1 < len(df_local) else len(df_local)

    idx_fine_partita = _find_event_index(df_local, 'Fine partita')
    if idx_fine_partita is None:
        idx_fine_partita = len(df_local) - 1

    t_start = df_local.loc[0, 'Posizione_sec']
    t_fine_primo = df_local.loc[idx_fine_primo, 'Posizione_sec']
    t_start_secondo = df_local.loc[idx_start_secondo, 'Posizione_sec'] if idx_start_secondo < len(df_local) else df_local.loc[idx_fine_primo, 'Posizione_sec']
    t_fine_partita = df_local.loc[idx_fine_partita, 'Posizione_sec']

    tempo_effettivo_sec = []
    tempo_effettivo_fmt = []

    for i, row in df_local.iterrows():
        t = row['Posizione_sec']
        if i <= idx_fine_primo:
            denom = t_fine_primo - t_start
            if denom <= 0 or pd.isna(denom):
                eff = 0.0
            else:
                perc = (t - t_start) / denom
                perc = max(0, min(1, perc))
                eff = perc * 20 * 60
        elif idx_start_secondo < len(df_local) and i >= idx_start_secondo:
            denom = t_fine_partita - t_start_secondo
            if denom <= 0 or pd.isna(denom):
                eff = 20 * 60
            else:
                perc = (t - t_start_secondo) / denom
                perc = max(0, min(1, perc))
                eff = 20 * 60 + perc * 20 * 60
        else:
            eff = np.nan

        tempo_effettivo_sec.append(eff)
        tempo_effettivo_fmt.append('' if pd.isna(eff) else format_mmss(eff))

    return pd.Series(tempo_effettivo_fmt, index=df_local['__orig_index'])


def calcola_tempo_effettivo(df):
    if df.empty:
        return pd.Series([], index=df.index)

    if 'partita_id' not in df.columns or df['partita_id'].nunique() <= 1:
        result = _calcola_tempo_effettivo_single(df)
        return result.reindex(df.index)

    series_parts = []
    for _, gruppo in df.groupby('partita_id', sort=False):
        series_parts.append(_calcola_tempo_effettivo_single(gruppo))

    combined = pd.concat(series_parts).sort_index()
    return combined.reindex(df.index)


def _calcola_tempo_reale_single(df_single):
    df_local = _prepare_single_match(df_single)

    if df_local.empty:
        return pd.Series([], index=df_local['__orig_index'])

    idx_fine_primo = _find_event_index(df_local, 'Fine primo tempo')
    if idx_fine_primo is None:
        t_start = df_local.loc[0, 'posizione']
        tempi = [differenza_tempi(t_start, row['posizione']) for _, row in df_local.iterrows()]
        return pd.Series(tempi, index=df_local['__orig_index'])

    idx_start_secondo = _find_event_index(df_local, 'Inizio secondo tempo')
    if idx_start_secondo is None or idx_start_secondo <= idx_fine_primo:
        idx_start_secondo = idx_fine_primo + 1 if idx_fine_primo + 1 < len(df_local) else len(df_local)

    t_start = df_local.loc[0, 'posizione']
    t_start_secondo = df_local.loc[idx_start_secondo, 'posizione'] if idx_start_secondo < len(df_local) else df_local.loc[idx_fine_primo, 'posizione']

    tempi_reali = []
    for i, row in df_local.iterrows():
        if i <= idx_fine_primo:
            tempo = differenza_tempi(t_start, row['posizione'])
        elif idx_start_secondo < len(df_local) and i >= idx_start_secondo:
            tempo = differenza_tempi(t_start_secondo, row['posizione'])
        else:
            tempo = ''
        tempi_reali.append(tempo)

    return pd.Series(tempi_reali, index=df_local['__orig_index'])


def calcola_tempo_reale(df):
    if df.empty:
        return pd.Series([], index=df.index)

    if 'partita_id' not in df.columns or df['partita_id'].nunique() <= 1:
        result = _calcola_tempo_reale_single(df)
        return result.reindex(df.index).tolist()

    series_parts = []
    for _, gruppo in df.groupby('partita_id', sort=False):
        series_parts.append(_calcola_tempo_reale_single(gruppo))

    combined = pd.concat(series_parts).sort_index()
    return combined.reindex(df.index).tolist()


def _tag_primo_secondo_single(df_single):
    df_local = _prepare_single_match(df_single)

    if df_local.empty:
        return pd.Series([], index=df_local['__orig_index'])

    idx_fine_primo = _find_event_index(df_local, 'Fine primo tempo')
    if idx_fine_primo is None:
        valori = ['Primo tempo' for _ in range(len(df_local))]
        return pd.Series(valori, index=df_local['__orig_index'])

    idx_start_secondo = _find_event_index(df_local, 'Inizio secondo tempo')
    if idx_start_secondo is None or idx_start_secondo <= idx_fine_primo:
        idx_start_secondo = idx_fine_primo + 1 if idx_fine_primo + 1 < len(df_local) else len(df_local)

    periodo = []
    for i in range(len(df_local)):
        if i <= idx_fine_primo:
            periodo.append("Primo tempo")
        elif idx_start_secondo < len(df_local) and i >= idx_start_secondo:
            periodo.append("Secondo tempo")
        else:
            periodo.append("Intervallo")

    return pd.Series(periodo, index=df_local['__orig_index'])


def tag_primo_secondo_tempo(df):
    if len(df) == 0:
        return []

    if 'partita_id' not in df.columns or df['partita_id'].nunique() <= 1:
        serie = _tag_primo_secondo_single(df)
        return serie.reindex(df.index).tolist()

    series_parts = []
    for _, gruppo in df.groupby('partita_id', sort=False):
        series_parts.append(_tag_primo_secondo_single(gruppo))

    combined = pd.concat(series_parts).sort_index()
    return combined.reindex(df.index).tolist()

def filtra_per_tempo(df, periodo):
    if periodo == 'Primo tempo':
        return df[df['Periodo'] == 'Primo tempo'].reset_index(drop=True)
    elif periodo == 'Secondo tempo':
        return df[df['Periodo'] == 'Secondo tempo'].reset_index(drop=True)
    else:
        raise ValueError("Periodo non valido. Usa 'Primo tempo' o 'Secondo tempo'")