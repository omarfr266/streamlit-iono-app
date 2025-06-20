import os
import requests
import shutil
import gzip
from datetime import datetime, timedelta
from netrc import netrc

# 📁 Dossier pour enregistrer les fichiers
DEFAULT_OUTPUT_DIR = "ionex_files"

# ✅ Génère le nom de fichier et l'URL IONEX
def build_ionex_filename_and_url(date_obj):
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    elif isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    doy = date_obj.timetuple().tm_yday
    year = date_obj.year

    filename = f"COD0OPSFIN_{year}{doy:03d}0000_01D_01H_GIM.INX.gz"
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{year}/{doy:03d}/{filename}"
    return filename, url

# ✅ Télécharge un fichier IONEX avec authentification
def try_download_ionex_for_day(date_obj, output_folder=DEFAULT_OUTPUT_DIR):
    filename, url = build_ionex_filename_and_url(date_obj)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    # 🔐 Auth via .netrc
    try:
        netrc_path = os.path.expanduser("~/.netrc")
        user, _, password = netrc(netrc_path).authenticators("urs.earthdata.nasa.gov")
    except Exception as e:
        return f"❌ Identifiants Earthdata non trouvés dans .netrc : {e}", None

    try:
        with requests.get(url, auth=(user, password), stream=True, timeout=30) as response:
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return f"✅ Téléchargé : {filename}", output_path
            elif response.status_code == 401:
                return f"❌ Erreur 401 : Identifiants incorrects pour {filename}", None
            else:
                return f"❌ Introuvable (HTTP {response.status_code}) : {filename}", None
    except Exception as e:
        return f"❌ Erreur lors du téléchargement : {filename}\n{e}", None

# ✅ Décompresse un fichier .gz
def decompress_file(file_path):
    try:
        if file_path.endswith(".gz"):
            output_path = file_path[:-3]
            with gzip.open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            if os.path.getsize(output_path) < 100:
                print(f"⚠️ Fichier décompressé trop petit : {os.path.basename(output_path)}")
                return None

            os.remove(file_path)
            return output_path
        else:
            print(f"❌ Format non supporté : {file_path}")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de la décompression de {file_path} : {e}")
        return None

# ✅ Télécharge et décompresse entre 2 dates
def download_and_uncompress_ionex(start_date, end_date, output_folder=DEFAULT_OUTPUT_DIR):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    logs = []
    current_date = start_date

    while current_date <= end_date:
        msg, downloaded_path = try_download_ionex_for_day(current_date, output_folder)
        logs.append(msg)

        # ⚠️ Contenu HTML = erreur déguisée
        if downloaded_path:
            with open(downloaded_path, "rb") as f:
                head = f.read(300)
                if b"<html" in head.lower():
                    logs.append(f"⚠️ HTML détecté dans {os.path.basename(downloaded_path)} — probablement erreur du serveur.")
                    current_date += timedelta(days=1)
                    continue

            # ✅ Décompression
            decompressed_path = decompress_file(downloaded_path)
            if decompressed_path:
                logs.append(f"✅ Décompressé : {os.path.basename(decompressed_path)}")
            else:
                logs.append(f"❌ Échec décompression : {os.path.basename(downloaded_path)}")

        current_date += timedelta(days=1)

    return logs
