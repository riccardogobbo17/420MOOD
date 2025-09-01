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

    # STATS DI SQUADRA PER ZONA
    report['squadra'] = {
        'attacco': calcola_attacco(df, by_zona=True),
        'difesa': calcola_difesa(df, by_zona=True),
        'palle_recuperate_perse': calcola_palle_recuperate_perse(df, by_zona=True),
        'falli': calcola_falli(df, by_zona=True),
        # Ripartenze: NON ha senso per zona, la lasci fuori
        # Portieri: NON ha senso per zona (a meno che tu non voglia qualcosa di custom)
    }

    # STATS INDIVIDUALI GIOCATORI PER ZONA
    report['individuali'] = calcola_stats_individuali(df, by_zona=True)

    # STATS PORTIERI INDIVIDUALI PER ZONA
    report['portieri_individuali'] = calcola_stats_portieri_individuali(df, by_zona=True)

    return report


def disegna_statistiche_tiro(zone_stats, pitch_drawer):
    fig, ax = pitch_drawer.draw(orientation='vertical', figsize=(6, 12))

    x_div = [0, 6.66, 13.33, 20]
    y_div = [0, 20, 27, 34, 40]

    for x in x_div:
        ax.plot([x, x], [20, 40], color='grey', linestyle='--')
    for y in y_div[1:]:
        ax.plot([0, 20], [y, y], color='grey', linestyle='--')

    zone_number = 1
    for i in range(3):
        for j in range(3):
            x_center = x_div[j] + (x_div[j+1] - x_div[j]) / 2
            y_center = y_div[i+1] + (y_div[i+2] - y_div[i+1]) / 2
            stats = zone_stats.get(zone_number, {"Gol": 0, "Parata": 0, "Ribattuto": 0, "Fuori": 0, "Tot": 0})
            label = f"{stats['Gol']}G / {stats['Parata']}P / {stats['Ribattuto']}R / {stats['Fuori']}F / {stats['Tot']}T"
            ax.text(x_center, y_center, label, fontsize=9, ha='center', va='center')
            zone_number += 1

    stats_0 = zone_stats.get(0, {"Gol": 0, "Parata": 0, "Ribattuto": 0, "Fuori": 0, "Tot": 0})
    label_0 = f"{stats_0['Gol']}G / {stats_0['Parata']}P / {stats_0['Ribattuto']}R / {stats_0['Fuori']}F / {stats_0['Tot']}T"
    ax.text(10, 11, label_0, fontsize=9, ha='center', va='center')
    return fig, ax


import matplotlib.pyplot as plt
from matplotlib import cm

# 1. Funzione base per disegnare la griglia delle zone
def draw_base_zones(ax, x_div, y_div):
    for x in x_div:
        ax.plot([x, x], [y_div[1], y_div[-1]], color='grey', linestyle='--')
    for y in y_div[1:]:
        ax.plot([x_div[0], x_div[-1]], [y, y], color='grey', linestyle='--')


# 2. Funzione generica per plottare una o più metriche per zona
def draw_team_metric_per_zone(
    zone_stats, pitch_drawer, metric_keys,
    team_key='attacco', zone_labels=None, cmap=None, title=None
):
    """
    Plotta una o più metriche per zona per una sezione di stats di squadra.
    zone_stats: dict come report['squadra']
    team_key: sezione da plottare ('attacco', 'difesa', ...)
    metric_keys: lista delle metriche da mostrare nei label
    """
    import matplotlib as mpl

    stats_per_zone = zone_stats['squadra'][team_key]

    fig, ax = pitch_drawer.draw(orientation='vertical', figsize=(6, 12))
    x_div = [0, 6.66, 13.33, 20]
    y_div = [0, 20, 27, 34, 40]
    draw_base_zones(ax, x_div, y_div)

    zone_numbers = sorted(stats_per_zone.keys())

    # Colora le zone (opzionale)
    if cmap:
        max_val = max(stats.get(metric_keys[0], 0) for stats in stats_per_zone.values())
        norm = mpl.colors.Normalize(vmin=0, vmax=max_val)
        for zone_number in zone_numbers:
            if zone_number == 0:
                # Zona 0: posizione personalizzabile!
                ax.fill_between([7, 13], 7, 15, color=cmap(norm(stats_per_zone[0].get(metric_keys[0], 0))), alpha=0.4)
            else:
                i, j = divmod(zone_number-1, 3)
                val = stats_per_zone.get(zone_number, {}).get(metric_keys[0], 0)
                color = cmap(norm(val))
                ax.fill_between([x_div[j], x_div[j+1]], y_div[i+1], y_div[i+2], color=color, alpha=0.4)

    # Plotta i valori nelle zone
    for zone_number in zone_numbers:
        if zone_number == 0:
            x_center, y_center = 10, 11
        else:
            i, j = divmod(zone_number-1, 3)
            x_center = x_div[j] + (x_div[j+1] - x_div[j]) / 2
            y_center = y_div[i+1] + (y_div[i+2] - y_div[i+1]) / 2

        stats = stats_per_zone.get(zone_number, {k: 0 for k in metric_keys})
        label_vals = [str(stats.get(k, 0)) for k in metric_keys]
        label = " / ".join(label_vals)
        if zone_labels and zone_number in zone_labels:
            label = zone_labels[zone_number] + ": " + label
        ax.text(x_center, y_center, label, fontsize=9, ha='center', va='center')

    if title:
        ax.set_title(title)

    return fig, ax


# 2. Funzione generica per plottare una o più metriche per zona per giocatore
def draw_player_metric_per_zone(report, pitch_drawer, metric_keys, chi, zone_labels=None, cmap=None, title=None):
    """
    Plotta una o più metriche per zona per UN giocatore (chi), mostrando zero anche dove non ha fatto nulla.
    report: report['individuali']
    chi: nome giocatore da plottare
    """
    import matplotlib as mpl

    stats_per_zone = {int(k): v for k, v in report.items()}

    # Usa tutte le zone presenti nel report (tipicamente da 0 a 9)
    zone_numbers = sorted(stats_per_zone.keys())

    fig, ax = pitch_drawer.draw(orientation='vertical', figsize=(6, 12))
    x_div = [0, 6.66, 13.33, 20]
    y_div = [0, 20, 27, 34, 40]
    draw_base_zones(ax, x_div, y_div)

    # Colora le zone (opzionale)
    if cmap and len(zone_numbers) > 0:
        max_val = max(
            stats_per_zone[z].get(chi, {}).get(metric_keys[0], 0)
            for z in zone_numbers
        )
        norm = mpl.colors.Normalize(vmin=0, vmax=max_val)
        for zone_number in zone_numbers:
            val = stats_per_zone[zone_number].get(chi, {}).get(metric_keys[0], 0)
            if zone_number == 0:
                ax.fill_between([7, 13], 7, 15, color=cmap(norm(val)), alpha=0.4)
            else:
                i, j = divmod(zone_number-1, 3)
                color = cmap(norm(val))
                ax.fill_between([x_div[j], x_div[j+1]], y_div[i+1], y_div[i+2], color=color, alpha=0.4)

    # Plotta i valori nelle zone (zero dove il giocatore non compare)
    for zone_number in zone_numbers:
        if zone_number == 0:
            x_center, y_center = 10, 11
        else:
            i, j = divmod(zone_number-1, 3)
            x_center = x_div[j] + (x_div[j+1] - x_div[j]) / 2
            y_center = y_div[i+1] + (y_div[i+2] - y_div[i+1]) / 2

        # Stats: o quelle del giocatore o tutti zeri
        stats = stats_per_zone[zone_number].get(chi, {k: 0 for k in metric_keys})
        label_vals = [str(stats.get(k, 0)) for k in metric_keys]
        label = " / ".join(label_vals)
        if zone_labels and zone_number in zone_labels:
            label = zone_labels[zone_number] + ": " + label
        ax.text(x_center, y_center, label, fontsize=9, ha='center', va='center')

    if title:
        ax.set_title(title)

    return fig, ax


