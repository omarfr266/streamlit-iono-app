import os
import requests
import shutil
import gzip
from datetime import datetime, timedelta

# Identifiants Earthdata (hardcodés pour tests, non recommandé pour production)
EARTHDATA_USER = "omargravimetrie"
EARTHDATA_PASS = "Gravimetrie-donnees222"

DEFAULT_OUTPUT_DIR = "ionex_data"  # Dossier de sortie harmonisé avec l'interface

def build_ionex_filename_and_url(date_obj):
    """Construit le nom de fichier et l'URL pour un fichier IONEX."""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    elif isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    doy = date_obj.timetuple().tm_yday
    year = date_obj.year
    # Format standard pour les fichiers IGS IONEX
    filename = f"igs{year}{doy:03d}0.ionex.gz"
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{year}/{doy:03d}/{filename}"
    return filename, url

def try_download_ionex_for_day(date_obj, output_folder=DEFAULT_OUTPUT_DIR):
    """Tente de télécharger un fichier IONEX pour une date donnée."""
    filename, url = build_ionex_filename_and_url(date_obj)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    if not EARTHDATA_USER or not EARTHDATA_PASS:
        return "❌ Identifiants Earthdata non fournis.", None

    try:
        with requests.get(url, auth=(EARTHDATA_USER, EARTHDATA_PASS), stream=True, timeout=30) as response:
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return f"✅ Téléchargé : {filename}", output_path
            elif response.status_code == 401:
                return f"❌ Erreur 401 : Identifiants Earthdata incorrects pour {filename}", None
            elif response.status_code == 404:
                return f"❌ Fichier introuvable (HTTP 404) : {filename}", None
            else:
                return f"❌ Erreur HTTP {response.status_code} : {filename}", None
    except requests.exceptions.RequestException as e:
        return f"❌ Erreur réseau lors du téléchargement de {filename} : {str(e)}", None

def decompress_file(file_path):
    """Décompresse un fichier .gz et supprime l'original si valide."""
    try:
        if file_path.endswith(".gz"):
            output_path = file_path[:-3]  # Enlève .gz
            with gzip.open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Vérifie que le fichier décompressé n'est pas vide ou corrompu
            if os.path.getsize(output_path) < 100:
                os.remove(output_path)
                return None

            # Vérifie si le fichier contient du HTML (signe d'erreur)
            with open(output_path, "rb") as f:
                head = f.read(300)
                if b"<html" in head.lower():
                    os.remove(output_path)
                    return None

            os.remove(file_path)  # Supprime le .gz après décompression
            return output_path
        return None
    except Exception as e:
        return None

def download_and_uncompress_ionex(start_date, end_date, output_folder=DEFAULT_OUTPUT_DIR):
    """Télécharge et décompresse les fichiers IONEX pour une plage de dates."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    logs = []
    current_date = start_date

    while current_date <= end_date:
        msg, downloaded_path = try_download_ionex_for_day(current_date, output_folder)
        logs.append(msg)

        if downloaded_path:
            decompressed_path = decompress_file(downloaded_path)
            if decompressed_path:
                logs.append(f"✅ Décompressé : {os.path.basename(decompressed_path)}")
            else:
                logs.append(f"❌ Échec décompression : {os.path.basename(downloaded_path)}")

        current_date += timedelta(days=1)

    return logs
