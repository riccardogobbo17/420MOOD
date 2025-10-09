import pandas as pd

def calcola_statistiche_tiri(df):
    df_tiri = df[(df['squadra'] == 'Noi') & (df['evento'] == 'Tiro')].copy()
    df_tiri['zona'] = pd.to_numeric(df_tiri['dove'], errors='coerce').fillna(-1).astype(int)

    zone_stats = {}
    for zona, gruppo in df_tiri.groupby('zona'):
        esiti = gruppo['esito'].value_counts().to_dict()
        zone_stats[zona] = {
            "Gol": esiti.get("Gol", 0),
            "Parata": esiti.get("Parata", 0),
            "Ribattuto": esiti.get("Ribattuto", 0),
            "Fuori": esiti.get("Fuori", 0),
            "Tot": len(gruppo)
        }
    return zone_stats

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