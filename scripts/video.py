import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import re
import matplotlib.animation as animation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image
from io import BytesIO
import tempfile
import os
from PIL import Image

def generer_animation_tec(filepath, seisme_lat, seisme_lon):
    """
    Génère une animation GIF des cartes TEC à partir d'un fichier IONEX.

    Args:
        filepath (str): chemin vers le fichier IONEX (.INX)
        seisme_lat (float): latitude de l'épicentre
        seisme_lon (float): longitude de l'épicentre

    Returns:
        PIL.Image.Image: animation au format GIF
    """
    # Lecture du fichier
    with open(filepath, "r") as f:
        lines = f.readlines()

    start_indices = [i for i, line in enumerate(lines) if "START OF TEC MAP" in line]
    end_indices = [i for i, line in enumerate(lines) if "END OF TEC MAP" in line]

    frames = []
    times = []
    longitudes, latitudes = None, None

    for idx, (start, end) in enumerate(zip(start_indices, end_indices)):
        tec_maps = []
        lats = []
        longs = None

        i = start + 1
        while i < end:
            line = lines[i]
            if "LAT/LON1/LON2/DLON/H" in line:
                meta = list(map(float, re.findall(r"-?\d+\.\d+|-?\d+", line)))
                lat = meta[0]
                lon1, lon2, dlon = meta[1], meta[2], meta[3]

                if longs is None:
                    longs = np.arange(lon1, lon2 + dlon, dlon)

                data_row = []
                j = i + 1
                while j < end and "LAT/LON1/LON2/DLON/H" not in lines[j] and "END OF TEC MAP" not in lines[j]:
                    row_values = [float(x) for x in re.findall(r"-?\d+", lines[j])]
                    data_row.extend(row_values)
                    j += 1

                row_padded = np.pad(data_row, (0, len(longs) - len(data_row)), constant_values=np.nan)
                tec_maps.append(row_padded)
                lats.append(lat)
                i = j
            else:
                i += 1

        if not tec_maps:
            continue

        lats = np.array(lats)
        tec_map = np.array(tec_maps)

        lon_grid, lat_grid = np.meshgrid(longs, lats)
        lon_fine = np.linspace(longs.min(), longs.max(), 300)
        lat_fine = np.linspace(lats.min(), lats.max(), 300)
        lon_fine_grid, lat_fine_grid = np.meshgrid(lon_fine, lat_fine)

        points = np.array([lon_grid.flatten(), lat_grid.flatten()]).T
        values = tec_map.flatten()
        tec_interp = griddata(points, values, (lon_fine_grid, lat_fine_grid), method='linear')

        frames.append(tec_interp)
        times.append(f"{idx:02d}:00")

        if longitudes is None:
            longitudes, latitudes = longs, lats

    if not frames:
        raise ValueError("Aucune donnée TEC trouvée dans le fichier.")

    # Création de l'animation
    fig = plt.figure(figsize=(12, 6))
    proj = ccrs.PlateCarree()
    ax = plt.axes(projection=proj)

    ax.set_global()
    ax.coastlines(resolution='110m')
    ax.add_feature(cfeature.BORDERS, edgecolor='gray')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)

    img = ax.imshow(frames[0], extent=[longitudes.min(), longitudes.max(), latitudes.min(), latitudes.max()],
                    origin='lower', transform=proj, cmap='jet', aspect='auto')

    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=13, color='white',
                        bbox=dict(facecolor='black', alpha=0.5))

    epicentre_marker, = ax.plot([seisme_lon], [seisme_lat], marker='*', color='black', markersize=15, transform=proj)

    plt.title("Animation des Cartes TEC avec Épicentre et Carte du Monde 🌍")
    plt.tight_layout()

    def update(frame_idx):
        img.set_array(frames[frame_idx])
        time_text.set_text(f"Heure UTC : {times[frame_idx]}")
        return img, time_text, epicentre_marker

    ani = animation.FuncAnimation(fig, update, frames=len(frames), interval=400)

    # Création d'un fichier temporaire pour sauvegarder le GIF
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmpfile:
        ani.save(tmpfile.name, writer='pillow', dpi=80)
        tmpfile_path = tmpfile.name



    plt.close(fig)
    return tmpfile_path

