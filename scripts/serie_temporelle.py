# scripts/serie_temporelle.py

import pandas as pd
import matplotlib.pyplot as plt

def afficher_serie_temporelle_tec(excel_file, seisme_str, k=2):
    """
    Affiche la série temporelle du TEC avec la date du séisme,
    les limites de contrôle (UCL/LCL) et les anomalies détectées.

    Args:
        excel_file (str): Chemin vers le fichier Excel contenant les données TEC.
        seisme_str (str): Date et heure du séisme (format: "YYYY-MM-DD HH:MM:SS").
        k (int): Facteur pour les limites de contrôle (par défaut k=2 pour Mw >= 6.0).

    Returns:
        fig (matplotlib.figure.Figure): Figure contenant le graphique.
    """
    df = pd.read_excel(excel_file)
    df["Date"] = pd.to_datetime(df.iloc[:, 0])
    df["TEC"] = df.iloc[:, 1]

    # Statistiques
    mean_tec = df["TEC"].mean()
    std_tec = df["TEC"].std()
    UCL = mean_tec + k * std_tec
    LCL = mean_tec - k * std_tec

    # Z-score et détection d'anomalies
    df["Z-score"] = (df["TEC"] - mean_tec) / std_tec
    df["Anomalie"] = (df["TEC"] > UCL) | (df["TEC"] < LCL)

    # Graphique
    seisme_date = pd.to_datetime(seisme_str)
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df["Date"], df["TEC"], label="TEC", color="blue")
    ax.axvline(x=seisme_date, color='red', linestyle='--', linewidth=2, label="Séisme")
    ax.axhline(UCL, color='green', linestyle='--', linewidth=1.5, label=f'UCL (+{k}σ)')
    ax.axhline(LCL, color='green', linestyle='--', linewidth=1.5, label=f'LCL (-{k}σ)')

    # Anomalies en orange
    anomalies = df[df["Anomalie"]]
    ax.scatter(anomalies["Date"], anomalies["TEC"], color='orange', label="Anomalies", zorder=5)

    ax.set_xlabel("Date et heure")
    ax.set_ylabel("TEC (TECU)")
    ax.set_title("Série temporelle du TEC avec limites de contrôle et anomalies")
    ax.legend()
    ax.grid(True)
    return fig
