import pandas as pd
from futsal_analysis.utils_eventi import *

def calcola_report_zona(df):
    """
    Restituisce tutte le statistiche aggregate PER ZONA in un unico dizionario strutturato:
      - report['squadra']           : stats di squadra PER ZONA (tutte le sezioni)
      - report['individuali']       : stats individuali giocatori PER ZONA
      - report['portieri_individuali'] : stats individuali portieri PER ZONA
    """

    report = {}

    # Helper: conteggio per zona (1..3) e lato ('Sx'/'Dx') con split 50/50 se lato mancante
    def count_by_zone_side(df_sub):
        result = {z: {'Sx': 0.0, 'Dx': 0.0, 'Tot': 0} for z in [1, 2, 3]}
        df_sub = df_sub.copy()
        df_sub['zona'] = pd.to_numeric(df_sub['dove'], errors='coerce').astype('Int64')
        for z in [1, 2, 3]:
            blocco = df_sub[df_sub['zona'] == z]
            if blocco.empty:
                continue
            tot = len(blocco)
            # lato può essere 'Sx' o 'Dx'
            sx = len(blocco[(blocco['lato'].str.contains('Sx', na=False))])
            dx = len(blocco[(blocco['lato'].str.contains('Dx', na=False))])
            missing = len(blocco[(blocco['lato'].isna()) | (blocco['lato'].astype(str).str.strip() == '')])
            result[z]['Sx'] += sx + 0.5 * missing
            result[z]['Dx'] += dx + 0.5 * missing
            result[z]['Tot'] += tot
        return result

    # Definisci maschere metriche per sezioni squadra
    def build_metrics_attacco(df):
        mask_tiro_noi = (df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Noi')
        mask_gol_noi = (df['evento'].str.contains('Gol', na=False)) & (df['squadra'] == 'Noi')
        return {
            'gol_fatti': df[mask_gol_noi],
            'tiri_totali': df[mask_tiro_noi],
            'tiri_in_porta_totali': df[mask_tiro_noi & df['esito'].isin(['Parata', 'Gol', 'Palo'])],
            'tiri_ribattuti': df[mask_tiro_noi & (df['esito'] == 'Ribattuto')],
            'tiri_fuori': df[mask_tiro_noi & (df['esito'] == 'Fuori')],
            'palo_traversa': df[mask_tiro_noi & (df['esito'] == 'Palo')],
            'angoli': df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Noi')],
            'laterali': df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Noi')],
            'rigori': df[(df['evento'].str.contains('Rigore', na=False)) & (df['squadra'] == 'Noi')],
            'tiri_liberi': df[(df['evento'].str.contains('Tiro libero', na=False)) & (df['squadra'] == 'Noi')],
            'palle_perse': df[(df['evento'].str.contains('Palla persa', na=False))],
        }

    def build_metrics_difesa(df):
        mask_tiro_loro = (df['evento'].str.contains('Tiro', na=False)) & (df['squadra'] == 'Loro')
        mask_gol_loro = (df['evento'].str.contains('Gol', na=False)) & (df['squadra'] == 'Loro')
        return {
            'gol_subiti': df[mask_gol_loro],
            'tiri_totali_subiti': df[mask_tiro_loro],
            'tiri_in_porta_totali_subiti': df[mask_tiro_loro & df['esito'].isin(['Parata', 'Gol', 'Palo'])],
            'tiri_ribattuti_da_noi': df[mask_tiro_loro & (df['esito'] == 'Ribattuto')],
            'tiri_fuori_loro': df[mask_tiro_loro & (df['esito'] == 'Fuori')],
            'palo_traversa_loro': df[mask_tiro_loro & (df['esito'] == 'Palo')],
            'angoli_loro': df[(df['evento'].str.contains('Angolo', na=False)) & (df['squadra'] == 'Loro')],
            'laterale_loro': df[(df['evento'].str.contains('Laterale', na=False)) & (df['squadra'] == 'Loro')],
            'tiri_liberi_subiti': df[(df['evento'].str.contains('Tiro libero', na=False)) & (df['squadra'] == 'Loro')],
            'palle_recuperate': df[(df['evento'].str.contains('Palla recuperata', na=False))],
        }

    def build_metrics_falli(df):
        return {
            'falli_fatti': df[(df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Noi')],
            'falli_subiti': df[(df['evento'].str.contains('Fallo', na=False)) & (df['squadra'] == 'Loro')],
        }

    def compute_section(df, build_fn):
        frames = build_fn(df)
        section = {z: {} for z in [1, 2, 3]}
        for metric, dframe in frames.items():
            counts = count_by_zone_side(dframe)
            for z in [1, 2, 3]:
                section[z][metric] = counts[z]
        return section

    report['squadra'] = {
        'attacco': compute_section(df, build_metrics_attacco),
        'difesa': compute_section(df, build_metrics_difesa),
        'falli': compute_section(df, build_metrics_falli),
    }

    # STATS INDIVIDUALI GIOCATORI PER ZONA E LATO
    def stat_keys_individuali():
        return {
            # ATTACCO
            'gol_fatti': lambda d: d['evento'].str.contains('Gol', na=False) & (d['squadra'] == 'Noi'),
            'tiri_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi'),
            'tiri_in_porta_totali': lambda d: d['evento'].str.contains('Tiro', na=False) & (d['squadra'] == 'Noi') & d['esito'].isin(['Parata', 'Gol', 'Palo']),
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
        }

    def count_by_zone_side_grouped(df_sub, group_col='chi'):
        df_sub = df_sub.copy()
        df_sub['zona'] = pd.to_numeric(df_sub['dove'], errors='coerce').astype('Int64')
        gruppi = {}
        for name, g in df_sub.groupby(group_col):
            if not isinstance(name, str) or name.strip() == '':
                continue
            gruppi[name] = {z: {'Sx': 0.0, 'Dx': 0.0, 'Tot': 0} for z in [1, 2, 3]}
            for z in [1, 2, 3]:
                blocco = g[g['zona'] == z]
                if blocco.empty:
                    continue
                tot = len(blocco)
                sx = len(blocco[(blocco['lato'].str.contains('Sx', na=False))])
                dx = len(blocco[(blocco['lato'].str.contains('Dx', na=False))])
                missing = len(blocco[(blocco['lato'].isna()) | (blocco['lato'].astype(str).str.strip() == '')])
                gruppi[name][z]['Sx'] += sx + 0.5 * missing
                gruppi[name][z]['Dx'] += dx + 0.5 * missing
                gruppi[name][z]['Tot'] += tot
        return gruppi

    # Costruisci sezioni per-individuale: zona -> giocatore -> metrica -> {Sx, Dx, Tot}
    individuali_report = {z: {} for z in [1, 2, 3]}
    for metric_key, predicate in stat_keys_individuali().items():
        dframe = df[predicate(df)]
        counts = count_by_zone_side_grouped(dframe, group_col='chi')
        for giocatore, per_zona in counts.items():
            for z in [1, 2, 3]:
                if giocatore not in individuali_report[z]:
                    individuali_report[z][giocatore] = {}
                individuali_report[z][giocatore][metric_key] = per_zona[z]
    report['individuali'] = individuali_report

    # STATS PORTIERI INDIVIDUALI PER ZONA
    report['portieri_individuali'] = calcola_stats_portieri_individuali(df, by_zona=True)

    return report


def disegna_statistiche_tiro(zone_stats, pitch_drawer):
    fig, ax = pitch_drawer.draw(orientation='vertical', figsize=(5, 7))

    # 3 fasce orizzontali tra y=0 e y=30 e split verticale a x=10
    x_min, x_max = 0, 20
    x_mid = 10
    y_bands = [0, 10, 20, 30]  # 1=0-10 (basso), 2=10-20 (centro), 3=20-30 (alto)

    # Griglia: linee orizzontali e verticale centrale
    for y in y_bands:
        ax.plot([x_min, x_max], [y, y], color='grey', linestyle='--')
    ax.plot([x_mid, x_mid], [y_bands[0], y_bands[-1]], color='grey', linestyle='--')

    # Etichette totali per fascia (opzionale): centrato
    for zone_number in [1, 2, 3]:
        y_center = y_bands[zone_number - 1] + (y_bands[zone_number] - y_bands[zone_number - 1]) / 2
        x_center = (x_min + x_max) / 2
        stats = zone_stats.get(zone_number, {"Tot": 0})
        tot = int(round(stats.get('Tot', 0)))
        ax.text(x_center, y_center, str(tot), fontsize=10, ha='center', va='center', weight='bold')

    return fig, ax


import matplotlib.pyplot as plt
from matplotlib import cm

def get_event_initials(metric_keys):
    """Genera le iniziali degli eventi selezionati"""
    initials_map = {
        'gol_fatti': 'G',
        'gol_subiti': 'G',
        'tiri_totali': 'TT',
        'tiri_in_porta': 'TP',
        'tiri_in_porta_totali': 'TP',
        'tiri_ribattuti': 'TR',
        'tiri_fuori': 'TF',
        'palo_traversa': 'PT',
        'angoli': 'AG',
        'laterali': 'LT',
        'rigori': 'RG',
        'tiri_liberi': 'TL',
        'tiri_subiti': 'TP',
        'tiri_totali_subiti': 'TP',
        'tiri_in_porta_subiti': 'TP',
        'tiri_in_porta_totali_subiti': 'TP',
        'tiri_loro_ribattuti_da_noi': 'TR',
        'tiri_ribattuti_da_noi': 'TR',
        'tiri_fuori_subiti': 'TF',
        'tiri_fuori_loro': 'TF',
        'tiri_loro_palo_traversa': 'PT',
        'palo_traversa_loro': 'PT',
        'angoli_subiti': 'AG',
        'laterali_subiti': 'LT',
        'laterale_loro': 'LT',
        'rigori_subiti': 'RG',
        'tiri_liberi_subiti': 'TL',
        'palle_recuperate': 'PR',
        'palla_recuperata_totali': 'PR',
        'palle_perse': 'PP',
        'palla_persa_totali': 'PP',
        'falli_commessi': 'FC',
        'falli_subiti': 'FS',
        'tiri_parati_da_noi': 'TP'
    }
    
    initials = []
    for key in metric_keys:
        initials.append(initials_map.get(key, key[:2].upper()))
    
    return " / ".join(initials)

# 1. Funzione base per disegnare la griglia delle zone
def draw_base_zones(ax, y_bands, x_min=0, x_max=20, x_mid=10):
    # Linee orizzontali e verticale a metà campo
    for y in y_bands:
        ax.plot([x_min, x_max], [y, y], color='red', linestyle='--', alpha=0.5)
    ax.plot([x_mid, x_mid], [y_bands[0], y_bands[-1]], color='red', linestyle='--', alpha=0.5)


# 2. Funzione generica per plottare una o più metriche per zona
def draw_team_metric_per_zone(
    zone_stats, pitch_drawer, metric_keys,
    team_key='attacco', zone_labels=None, cmap=None, title=None,
    per_side=True
):
    """
    Plotta una o più metriche per zona per una sezione di stats di squadra.
    zone_stats: dict come report['squadra']
    team_key: sezione da plottare ('attacco', 'difesa', ...)
    metric_keys: lista delle metriche da mostrare nei label
    """
    import matplotlib as mpl

    stats_per_zone = zone_stats['squadra'][team_key]

    fig, ax = pitch_drawer.draw(orientation='vertical', figsize=(5, 7))
    x_min, x_max, x_mid = 0, 20, 10
    y_bands = [0, 10, 20, 30]
    draw_base_zones(ax, y_bands, x_min, x_max, x_mid)

    zone_numbers = [1, 2, 3]

    # Colora e label: per lato o aggregato
    if per_side:
        if cmap:
            def get_val(z, side):
                first_key = metric_keys[0]
                v = stats_per_zone.get(z, {}).get(first_key, {})
                if isinstance(v, dict):
                    return v.get(side, 0)
                return v
            max_val = max(max(get_val(z, s) for s in ['Sx', 'Dx']) for z in zone_numbers)
            norm = mpl.colors.Normalize(vmin=0, vmax=max_val if max_val > 0 else 1)
            for z in zone_numbers:
                y0, y1 = y_bands[z - 1], y_bands[z]
                for side, x0, x1 in [('Sx', x_min, x_mid), ('Dx', x_mid, x_max)]:
                    val = get_val(z, side)
                    color = cmap(norm(val))
                    ax.fill_between([x0, x1], y0, y1, color=color, alpha=0.35)

        for z in zone_numbers:
            # Sposta la zona 1 ancora più in alto (2/3 invece di 1/2)
            if z == 1:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) * 2/3
            else:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) / 3
            for side, x_center in [('Sx', (x_min + x_mid) / 2), ('Dx', (x_mid + x_max) / 2)]:
                stats = stats_per_zone.get(z, {})
                label_vals = []
                for k in metric_keys:
                    v = stats.get(k, 0)
                    if isinstance(v, dict):
                        v = v.get(side, 0)
                    label_vals.append(str(int(round(v))))
                
                # Aggiungi le iniziali degli eventi
                initials = get_event_initials(metric_keys)
                label = " / ".join(label_vals) + f"\n({initials})"
                ax.text(x_center, y_center, label, fontsize=10, ha='center', va='center', weight='bold')
    else:
        if cmap:
            def get_val_sum(z):
                first_key = metric_keys[0]
                v = stats_per_zone.get(z, {}).get(first_key, {})
                if isinstance(v, dict):
                    return v.get('Sx', 0) + v.get('Dx', 0)
                return v
            max_val = max(get_val_sum(z) for z in zone_numbers)
            norm = mpl.colors.Normalize(vmin=0, vmax=max_val if max_val > 0 else 1)
            for z in zone_numbers:
                y0, y1 = y_bands[z - 1], y_bands[z]
                val = get_val_sum(z)
                color = cmap(norm(val))
                ax.fill_between([x_min, x_max], y0, y1, color=color, alpha=0.35)

        for z in zone_numbers:
            x_center = (x_min + x_max) / 2
            # Sposta la zona 1 ancora più in alto (2/3 invece di 1/2)
            if z == 1:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) * 2/3
            else:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) / 3
            stats = stats_per_zone.get(z, {})
            label_vals = []
            for k in metric_keys:
                v = stats.get(k, 0)
                if isinstance(v, dict):
                    v = v.get('Sx', 0) + v.get('Dx', 0)
                label_vals.append(str(int(round(v))))
            
            # Aggiungi le iniziali degli eventi
            initials = get_event_initials(metric_keys)
            label = " / ".join(label_vals) + f"\n({initials})"
            ax.text(x_center, y_center, label, fontsize=8, ha='center', va='center', weight='bold')

    if title:
        ax.set_title(title)

    return fig, ax


# 2. Funzione generica per plottare una o più metriche per zona per giocatore
def draw_player_metric_per_zone(report, pitch_drawer, metric_keys, chi, zone_labels=None, cmap=None, title=None, per_side=True):
    """
    Plotta una o più metriche per zona per UN giocatore (chi), mostrando zero anche dove non ha fatto nulla.
    report: report['individuali']
    chi: nome giocatore da plottare
    """
    import matplotlib as mpl

    stats_per_zone = {int(k): v for k, v in report.items()}

    # Zone 1..3 con split per lato Sx/Dx
    zone_numbers = [z for z in [1, 2, 3] if z in stats_per_zone]

    fig, ax = pitch_drawer.draw(orientation='vertical', figsize=(5, 7))
    x_min, x_max, x_mid = 0, 20, 10
    y_bands = [0, 10, 20, 30]
    draw_base_zones(ax, y_bands, x_min, x_max, x_mid)

    if per_side:
        # Colora per lato usando la prima metrica
        if cmap and len(zone_numbers) > 0:
            def get_val(z, side):
                v = stats_per_zone[z].get(chi, {}).get(metric_keys[0], 0)
                if isinstance(v, dict):
                    return v.get(side, 0)
                return v
            max_val = max(max(get_val(z, s) for s in ['Sx', 'Dx']) for z in zone_numbers)
            norm = mpl.colors.Normalize(vmin=0, vmax=max_val if max_val > 0 else 1)
            for z in zone_numbers:
                y0, y1 = y_bands[z - 1], y_bands[z]
                for side, x0, x1 in [('Sx', x_min, x_mid), ('Dx', x_mid, x_max)]:
                    val = get_val(z, side)
                    color = cmap(norm(val))
                    ax.fill_between([x0, x1], y0, y1, color=color, alpha=0.35)

        # Label per lato
        for z in zone_numbers:
            # Sposta la zona 1 ancora più in alto (2/3 invece di 1/2)
            if z == 1:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) * 2/3
            else:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) / 3
            for side, x_center in [('Sx', (x_min + x_mid) / 2), ('Dx', (x_mid + x_max) / 2)]:
                stats = stats_per_zone[z].get(chi, {k: 0 for k in metric_keys})
                label_vals = []
                for k in metric_keys:
                    v = stats.get(k, 0)
                    if isinstance(v, dict):
                        v = v.get(side, 0)
                    label_vals.append(str(int(round(v))))
                # Aggiungi le iniziali degli eventi
                initials = get_event_initials(metric_keys)
                label = " / ".join(label_vals) + f"\n({initials})"
                if zone_labels and z in zone_labels:
                    label = zone_labels[z] + ": " + label
                ax.text(x_center, y_center, label, fontsize=10, ha='center', va='center', weight='bold')
    else:
        # Colora aggregato per fascia
        if cmap and len(zone_numbers) > 0:
            def get_val_sum(z):
                v = stats_per_zone[z].get(chi, {}).get(metric_keys[0], 0)
                if isinstance(v, dict):
                    return v.get('Sx', 0) + v.get('Dx', 0)
                return v
            max_val = max(get_val_sum(z) for z in zone_numbers)
            norm = mpl.colors.Normalize(vmin=0, vmax=max_val if max_val > 0 else 1)
            for z in zone_numbers:
                y0, y1 = y_bands[z - 1], y_bands[z]
                val = get_val_sum(z)
                color = cmap(norm(val))
                ax.fill_between([x_min, x_max], y0, y1, color=color, alpha=0.35)

        # Label unica centrata per fascia
        for z in zone_numbers:
            x_center = (x_min + x_max) / 2
            # Sposta la zona 1 ancora più in alto (2/3 invece di 1/2)
            if z == 1:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) * 2/3
            else:
                y_center = y_bands[z - 1] + (y_bands[z] - y_bands[z - 1]) / 3
            stats = stats_per_zone[z].get(chi, {k: 0 for k in metric_keys})
            label_vals = []
            for k in metric_keys:
                v = stats.get(k, 0)
                if isinstance(v, dict):
                    v = v.get('Sx', 0) + v.get('Dx', 0)
                label_vals.append(str(int(round(v))))
            # Aggiungi le iniziali degli eventi
            initials = get_event_initials(metric_keys)
            label = " / ".join(label_vals) + f"\n({initials})"
            if zone_labels and z in zone_labels:
                label = zone_labels[z] + ": " + label
            ax.text(x_center, y_center, label, fontsize=8, ha='center', va='center', weight='bold')

    if title:
        ax.set_title(title)

    return fig, ax


