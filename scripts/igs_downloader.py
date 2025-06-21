import os
import requests
import shutil
import gzip
import zipfile
from datetime import datetime, timedelta, date

# Identifiants Earthdata
try:
    import streamlit as st
    EARTHDATA_USER = st.secrets["earthdata"]["username"]
    EARTHDATA_PASS = st.secrets["earthdata"]["password"]
except Exception:
    EARTHDATA_USER = "omargravimetrie"
    EARTHDATA_PASS = "Gravimetrie-donnees222"

DEFAULT_OUTPUT_DIR = "ionex_data"

def build_ionex_filename_and_url(date_obj):
    """Construit le nom de fichier et l'URL pour un fichier IONEX."""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    elif isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    doy = date_obj.timetuple().tm_yday
    year = date_obj.year
    filename = f"COD0OPSFIN_{year}{doy:03d}0000_01D_01H_GIM.INX.gz"
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{year}/{doy:03d}/{filename}"
    return filename, url

def try_download_ionex_for_day(date_obj, output_folder=DEFAULT_OUTPUT_DIR):
    """Tente de télécharger un fichier IONEX pour une date donnée."""
    filename, url = build_ionex_filename_and_url(date_obj)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    if not EARTHDATA_USER or not EARTHDATA_PASS:
        return "❌ Identifiants Earthdata non fournis. Veuillez configurer les secrets dans Streamlit Cloud.", None

    try:
        with requests.get(url, auth=(EARTHDATA_USER, EARTHDATA_PASS), stream=True, timeout=30) as response:
            if response.status_code == 200:
                # Vérifie si le contenu est HTML
                first_bytes = next(response.iter_content(300), b"")
                if b"<html" in first_bytes.lower():
                    try:
                        st.error(f"❌ Téléchargement invalide (HTML détecté) : {filename}. Code HTTP: {response.status_code}. Contenu: {first_bytes.decode('utf-8', errors='ignore')[:100]}")
                    except NameError:
                        print(f"❌ Téléchargement invalide (HTML détecté) : {filename}. Code HTTP: {response.status_code}. Contenu: {first_bytes.decode('utf-8', errors='ignore')[:100]}")
                    return f"❌ Téléchargement invalide (HTML détecté) : {filename}", None
                with open(output_path, "wb") as f:
                    f.write(first_bytes)
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
    """Décompresse un fichier .gz ou .zip et supprime l'original si valide."""
    try:
        if file_path.endswith(".gz"):
            output_path = file_path[:-3]
            with gzip.open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            if os.path.getsize(output_path) < 100:
                os.remove(output_path)
                return None

            with open(output_path, "rb") as f:
                head = f.read(300)
                if b"<html" in head.lower():
                    os.remove(output_path)
                    return None

            os.remove(file_path)
            return output_path

        elif file_path.endswith(".zip"):
            output_dir = os.path.dirname(file_path)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            os.remove(file_path)
            extracted_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
            return extracted_files[0] if extracted_files else None

        else:
            return None

    except Exception as e:
        try:
            st.error(f"❌ Erreur décompression {file_path} : {str(e)}")
        except NameError:
            print(f"❌ Erreur décompression {file_path} : {str(e)}")
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
        message, downloaded_path = try_download_ionex_for_day(current_date, output_folder)
        logs.append(message)

        if downloaded_path:
            decompressed_path = decompress_file(downloaded_path)
            if decompressed_path:
                logs.append(f"✅ Décompressé : {os.path.basename(decompressed_path)}")
            else:
                logs.append(f"❌ Échec décompression : {os.path.basename(downloaded_path)}")

        current_date += timedelta(days=1)

    return logs
