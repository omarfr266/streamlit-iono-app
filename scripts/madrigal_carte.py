import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def lire_tec_ascii(fichier_txt, heure):
    # Lecture du fichier ASCII
    df = pd.read_csv(fichier_txt, delim_whitespace=True)

    # Vérifie que le DataFrame contient des données
    if df.empty:
        raise ValueError("Le fichier ne contient aucune donnée.")

    # Filtrer selon l'heure choisie
    df_filtré = df[df["HOUR"] == heure]

    if df_filtré.empty:
        raise ValueError(f"Aucune donnée pour l'heure {heure} UTC.")

    # Création de la carte avec projection
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Arrière-plan : carte du monde
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

    # Tracé lisse avec tricontourf
    sc = ax.tricontourf(df_filtré["GLON"], df_filtré["GDLAT"], df_filtré["TEC"],
                        levels=30, cmap='jet', transform=ccrs.PlateCarree())

    # Barre de couleur
    cbar = plt.colorbar(sc, orientation='vertical', pad=0.05, shrink=0.8)
    cbar.set_label("TEC (Total Electron Content)")

    # Titre
    plt.title(f"Carte TEC - {heure}h UTC", fontsize=14)

    return fig
