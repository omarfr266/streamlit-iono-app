import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import re

def afficher_carte_TEC_fichier(fichier_ionex, heure_utc=12, epicenter_lat=None, epicenter_lon=None):
    with open(fichier_ionex, "r") as f:
        lines = f.readlines()

    start_indices = [i for i, line in enumerate(lines) if "START OF TEC MAP" in line]
    end_indices = [i for i, line in enumerate(lines) if "END OF TEC MAP" in line]

    heure_maps = []
    lats_total = []
    longitudes = None

    for start, end in zip(start_indices, end_indices):
        # Vérifier l'heure
        date_line = lines[start + 1]
        parts = date_line.strip().split()
        heure_carte = int(parts[3])
        if heure_carte != heure_utc:
            continue

        tec_map = []
        lats = []
        i = start + 2
        while i < end:
            line = lines[i]
            if "LAT/LON1/LON2/DLON/H" in line:
                match = re.findall(r"(-?\d+\.\d+|-?\d+)", line)
                if len(match) < 4:
                    i += 1
                    continue
                lat = float(match[0])
                lon1 = float(match[1])
                lon2 = float(match[2])
                dlon = float(match[3])
                if longitudes is None:
                    longitudes = np.arange(lon1, lon2 + dlon, dlon)

                data_row = []
                j = i + 1
                while j < end and "LAT/LON1/LON2/DLON/H" not in lines[j] and "END OF TEC MAP" not in lines[j]:
                    row_values = [float(val) for val in re.findall(r"-?\d+", lines[j])]
                    data_row.extend(row_values)
                    j += 1

                tec_map.append(data_row[:len(longitudes)])
                lats.append(lat)
                i = j
            else:
                i += 1

        if tec_map:
            heure_maps.append(np.array(tec_map))
            lats_total = lats


    if not heure_maps:
        raise ValueError("Aucune carte TEC trouvée pour l'heure UTC spécifiée.")

    tec_mean = np.nanmean(np.stack(heure_maps), axis=0)
    latitudes = np.array(lats_total)
    longitudes = np.array(longitudes)
    lon_grid, lat_grid = np.meshgrid(longitudes, latitudes)

    # === Affichage avec Cartopy ===
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={"projection": ccrs.PlateCarree()})
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='white')

    contour = ax.contourf(lon_grid, lat_grid, tec_mean, levels=100, cmap="jet", transform=ccrs.PlateCarree())

    if epicenter_lat is not None and epicenter_lon is not None:
        ax.plot(epicenter_lon, epicenter_lat, marker='*', color='black', markersize=12,
                label="Épicentre", transform=ccrs.PlateCarree())
        ax.legend(loc="upper right")

    ax.set_title(f"Carte TEC Globale - Heure UTC {heure_utc}", fontsize=14)
    cbar = fig.colorbar(contour, ax=ax, orientation='horizontal', fraction=0.046, pad=0.04)
    cbar.set_label("TEC (TECU)", fontsize=12)

    return fig
