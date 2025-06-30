import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict

def calcola_minutaggi(df, df_1t, df_2t):
    """
    Calcola i minuti giocati suddivisi in categorie:
      ▸ mov4_portieri
      ▸ mov4_singoli
      ▸ mov4_singolo_portiere           (portiere + 1 giocatore di movimento)
      ▸ mov4_coppie                     (2 giocatori movimento)
      ▸ mov4_coppia_portiere            (portiere + 2 giocatori movimento)
      ▸ mov4_quartetto                  (4 giocatori movimento)
      ▸ mov4_quartetto_portiere         (portiere + 4 giocatori movimento)
      ▸ mov3_senza_portiere             (3 giocatori movimento)
      ▸ mov3_con_portiere               (portiere + 3 giocatori movimento, ma la combinazione contiene solo i 3 movimenti)
      ▸ mov5_senza_portiere             (5 giocatori movimento, nessun portiere)
    
    Ritorna un dizionario con chiavi "totale", "primo_tempo", "secondo_tempo",
    ciascuno contenente un dict di DataFrame per categoria.
    """
    # ---------- helper ------------
    def durata_reale_sec(df_local):
        delta = (
            pd.to_timedelta("00:" + df_local['tempoReale'].shift(-1).fillna("00:00")).dt.total_seconds()
            - pd.to_timedelta("00:" + df_local['tempoReale'].fillna("00:00")).dt.total_seconds()
        ).values
        return np.clip(delta, a_min=0, a_max=None).sum()

    def estrai_mov_portiere(row):
        """Restituisce (movimento_list, portiere or None)"""
        mov_cols = ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4']
        movimento = [row.get(c) for c in mov_cols]
        movimento = [str(g).strip() for g in movimento if pd.notna(g) and str(g).strip()]
        movimento = sorted(set(movimento))
        portiere = row.get('portiere')
        portiere = str(portiere).strip() if pd.notna(portiere) and str(portiere).strip() else None
        return movimento, portiere

    # ---------- core processor ------------
    def process_period(df_local):
        acc = defaultdict(float)

        for i in range(len(df_local) - 1):
            t1, t2 = df_local.loc[i, 'tempoReale'], df_local.loc[i + 1, 'tempoReale']
            if pd.isna(t1) or pd.isna(t2):
                continue
            delta = (pd.to_timedelta("00:" + t2) - pd.to_timedelta("00:" + t1)).total_seconds()
            if delta <= 0:
                continue

            movimento, portiere = estrai_mov_portiere(df_local.loc[i + 1])
            mov_len = len(movimento)
            if mov_len < 1:    # Prima era <3, ora basta almeno 1 in campo!
                continue

            # --------- CALCOLO PORTIERI: SEMPRE (se presente) ---------
            if portiere:
                acc[("mov4_portieri", (portiere,))] += delta

            # --------- CALCOLO SINGOLI: SEMPRE (se presenti giocatori movimento) ---------
            for g in movimento:
                acc[("mov4_singoli", (g,))] += delta

            # --------- CALCOLO SINGOLO + PORTIERE: SOLO SE ENTRAMBI PRESENTI ---------
            if portiere:
                for g in movimento:
                    acc[("mov4_singolo_portiere", (portiere, g))] += delta

            # --------- Altre combinazioni come da logica originale ---------
            if mov_len == 4:
                # coppie di movimento
                for c in combinations(movimento, 2):
                    acc[("mov4_coppie", tuple(sorted(c)))] += delta

                # coppia + portiere
                if portiere:
                    for c in combinations(movimento, 2):
                        trio = (portiere, *sorted(c))   
                        acc[("mov4_coppia_portiere", trio)] += delta

                # quartetto (solo mov)
                acc[("mov4_quartetto", tuple(movimento))] += delta

                # quartetto + portiere (portiere separato)
                if portiere:
                    acc[("mov4_quartetto_portiere", (portiere, *movimento))] += delta

            elif mov_len == 3:
                if portiere:
                    acc[("mov3_con_portiere", tuple(movimento))] += delta
                else:
                    acc[("mov3_senza_portiere", tuple(movimento))] += delta

            elif mov_len == 5 and portiere is None:
                acc[("mov5_senza_portiere", tuple(movimento))] += delta

        return acc


    # ---------- convert -------------------
    def dict_to_df(counter, total_sec):
        dfs = {}
        for (cat, key), sec in counter.items():
            minutes = round(sec / 60, 2)
            mmss = f"{int(sec//60):02}:{int(sec%60):02}"
            perc = f"{int(round(100 * sec / total_sec))}%"

            if cat == "mov4_portieri":
                df = dfs.setdefault(cat, [])
                df.append({
                    "Portiere": key[0],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov4_singoli":
                df = dfs.setdefault(cat, [])
                df.append({
                    "Giocatore": key[0],
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov4_singolo_portiere":
                port, g = key
                df = dfs.setdefault(cat, [])
                df.append({
                    "Portiere": port,
                    "Giocatore": g,
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov4_coppie":
                g1, g2 = key
                df = dfs.setdefault(cat, [])
                df.append({
                    "Giocatori": (g1, g2),
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov4_coppia_portiere":
                port, g1, g2 = key
                df = dfs.setdefault(cat, [])
                df.append({
                    "Portiere": port,
                    "Giocatori": (g1, g2),
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov4_quartetto":
                df = dfs.setdefault(cat, [])
                df.append({
                    "Giocatori_movimento": key,
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov4_quartetto_portiere":
                port, *mov = key
                df = dfs.setdefault(cat, [])
                df.append({
                    "Portiere": port,
                    "Giocatori_movimento": tuple(mov),
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat.startswith("mov3"):
                df = dfs.setdefault(cat, [])
                df.append({
                    "Giocatori_movimento": key,
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

            elif cat == "mov5_senza_portiere":
                df = dfs.setdefault(cat, [])
                df.append({
                    "Giocatori_movimento": key,
                    "Minuti_giocati": mmss,
                    "Percentuale": perc
                })

        # Convert lists to DataFrames and sort
        return {k: pd.DataFrame(v).sort_values("Minuti_giocati", ascending=False) for k, v in dfs.items()}

    # ---------- run for each period ----------
    durations = {
        "totale": durata_reale_sec(df),
        "primo_tempo": durata_reale_sec(df_1t),
        "secondo_tempo": durata_reale_sec(df_2t)
    }
    period_dfs = {}
    for label, dframe in [("totale", df), ("primo_tempo", df_1t), ("secondo_tempo", df_2t)]:
        counter = process_period(dframe)
        period_dfs[label] = dict_to_df(counter, durations[label])

    return period_dfs
