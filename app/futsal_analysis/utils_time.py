import numpy as np
import pandas as pd

def to_seconds(time_str):
    if pd.isna(time_str): return np.nan
    t = time_str.split(':')
    return int(t[0])*3600 + int(t[1])*60 + float(t[2]) if len(t) == 3 else np.nan

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

def calcola_tempo_effettivo(df):
    df = df.copy()
    df['Posizione_sec'] = df['posizione'].apply(to_seconds)
    idx_start = 0
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]

    t_start = df.loc[idx_start, 'Posizione_sec']
    t_fine_primo = df.loc[idx_fine_primo, 'Posizione_sec']
    t_start_secondo = df.loc[idx_start_secondo, 'Posizione_sec']
    t_fine_partita = df.loc[idx_fine_partita, 'Posizione_sec']

    tempo_effettivo = []
    for i, row in df.iterrows():
        t = row['Posizione_sec']
        if i <= idx_fine_primo:
            # Primo tempo: da 0 a 20 minuti
            perc = (t - t_start) / (t_fine_primo - t_start)
            # Limita la percentuale tra 0 e 1 per evitare tempi impossibili
            perc = max(0, min(1, perc))
            eff = perc * 20 * 60
        elif i >= idx_start_secondo:
            # Secondo tempo: da 20 a 40 minuti
            perc = (t - t_start_secondo) / (t_fine_partita - t_start_secondo)
            # Limita la percentuale tra 0 e 1 per evitare tempi impossibili
            perc = max(0, min(1, perc))
            eff = 20 * 60 + perc * 20 * 60
        else:
            # Intervallo
            eff = np.nan
        tempo_effettivo.append(eff)

    df['tempoEffettivo_sec'] = tempo_effettivo
    df['tempoEffettivo'] = df['tempoEffettivo_sec'].apply(format_mmss)
    return df['tempoEffettivo']

def calcola_tempo_reale(df):
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    t_start = df.loc[0, 'posizione']
    t_start_secondo = df.loc[idx_start_secondo, 'posizione']

    tempi_reali = []
    for i, row in df.iterrows():
        if i <= idx_fine_primo:
            tempo = differenza_tempi(t_start, row['posizione'])
        elif i >= idx_start_secondo:
            tempo = differenza_tempi(t_start_secondo, row['posizione'])
        else:
            tempo = ''
        tempi_reali.append(tempo)
    return tempi_reali

def tag_primo_secondo_tempo(df):
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    tempo_periodo = []
    for i in df.index:
        if i <= idx_fine_primo:
            tempo_periodo.append("Primo tempo")
        elif i >= idx_start_secondo:
            tempo_periodo.append("Secondo tempo")
        else:
            tempo_periodo.append("Intervallo")
    return tempo_periodo

def filtra_per_tempo(df, periodo):
    if periodo == 'Primo tempo':
        return df[df['Periodo'] == 'Primo tempo'].reset_index(drop=True)
    elif periodo == 'Secondo tempo':
        return df[df['Periodo'] == 'Secondo tempo'].reset_index(drop=True)
    else:
        raise ValueError("Periodo non valido. Usa 'Primo tempo' o 'Secondo tempo'")