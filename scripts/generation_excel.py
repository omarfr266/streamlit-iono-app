import os
import numpy as np
import datetime
import re
import pandas as pd

def find_nearest_index(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def generer_excel_TEC_par_heure(folder, target_lat, target_lon, output_excel_path):
    results = []
    ionex_files = [f for f in os.listdir(folder) if f.lower().endswith((".inx", ".i", ".ionex"))]

    for filename in sorted(ionex_files):
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            tec_data = []
            current_map = []
            current_time = None
            latitudes = np.arange(87.5, -87.6, -2.5)
            longitudes = np.arange(-180, 180.1, 5.0)
            tec_values = []
            in_tec_values = False

            for line in lines:
                if "START OF TEC MAP" in line:
                    current_map = []
                    tec_values = []
                    in_tec_values = False
                elif "END OF TEC MAP" in line:
                    if tec_values and in_tec_values:
                        current_map.append(tec_values)
                    if current_map:
                        tec_data.append((current_time, np.array(current_map)))
                    current_map = []
                    tec_values = []
                    in_tec_values = False
                elif "EPOCH OF CURRENT MAP" in line:
                    year, month, day, hour, minute, second = map(int, line.split()[:6])
                    current_time = datetime.datetime(year, month, day, hour, minute, second)
                elif "LAT/LON1/LON2/DLON/H" in line:
                    if tec_values and in_tec_values:
                        current_map.append(tec_values)
                    tec_values = []
                    in_tec_values = True
                elif in_tec_values:
                    parts = re.split(r'\s+', line.strip())
                    try:
                        values = [float(val) for val in parts if val]
                        tec_values.extend(values)
                    except ValueError:
                        in_tec_values = False
                        continue

            if tec_values and in_tec_values:
                current_map.append(tec_values)

            lat_idx = find_nearest_index(latitudes, target_lat)
            lon_idx = find_nearest_index(longitudes, target_lon)

            for time, tec_map in tec_data:
                try:
                    zone_values = []
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            i = lat_idx + di
                            j = lon_idx + dj
                            if 0 <= i < tec_map.shape[0] and 0 <= j < tec_map.shape[1]:
                                val = tec_map[i, j] * 0.1  # Conversion en TECU
                                zone_values.append(val)
                    if zone_values:
                        tec_avg = np.mean(zone_values)
                        results.append((time, tec_avg))
                except:
                    continue
        except:
            continue

    df = pd.DataFrame(results, columns=["DateTime", f"TEC_zone_{int(target_lat)}N_{int(target_lon)}E"])
    os.makedirs(os.path.dirname(output_excel_path), exist_ok=True)
    df.to_excel(output_excel_path, index=False)
    return output_excel_path
