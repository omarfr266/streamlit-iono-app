import os
import requests
import shutil
import gzip
from datetime import datetime, timedelta, date
import subprocess
import zipfile

def build_ionex_filename_and_url(date_obj):
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    elif isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    doy = date_obj.timetuple().tm_yday
    year = date_obj.year
    year_short = year % 100


    
        
    filename = f"COD0OPSFIN_{year}{doy:03d}0000_01D_01H_GIM.INX.gz"
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{year}/{doy:03d}/{filename}"
    return filename, url

def try_download_ionex_for_day(date_obj, output_folder):
    filename, url = build_ionex_filename_and_url(date_obj)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return f"✅ Téléchargé : {filename}", output_path
        else:
            return f"❌ Introuvable : {filename}", None
    except Exception as e:
        return f"❌ Erreur lors du téléchargement : {filename}\n{e}", None

def decompress_file(file_path):
    path_to_7z = r"C:\Program Files\7-Zip\7z.exe"

    if not os.path.isfile(file_path):
        return None

    try:
        if file_path.endswith(".Z"):
            output_dir = os.path.dirname(file_path)
            result = subprocess.run([path_to_7z, "e", f"-o{output_dir}", "-y", file_path], capture_output=True, text=True)


            if result.returncode == 0:
                decompressed_path = os.path.join(output_dir, os.path.basename(file_path)[:-2])
                os.remove(file_path)
                return decompressed_path
            else:
                print(f"❌ Erreur 7z : {result.stderr}")
                return None

        elif file_path.endswith(".gz"):
            output_path = file_path[:-3]
            with gzip.open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(file_path)
            return output_path

        elif file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(file_path))
            os.remove(file_path)
            return os.path.dirname(file_path)

        else:
            return None

    except Exception as e:
        print(f"❌ Erreur décompression {file_path} : {e}")
        return None

def download_and_uncompress_ionex(start_date, end_date, output_folder="ionex_files"):
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
