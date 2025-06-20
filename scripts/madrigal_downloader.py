import os
import gzip
import shutil
import datetime
import madrigalWeb.madrigalWeb as mw

# =================== CONFIG ===================
madrigal_url     = 'https://cedar.openmadrigal.org'
user_name        = 'Omar'
user_email       = 'omar@email.com'
user_affiliation = 'Algeria University'
# ==============================================

def decompress_gz(file_path):
    """Décompresse un .gz et supprime l’archive compressée."""
    if file_path.endswith(".gz"):
        decompressed_path = file_path[:-3]
        # Sauter si déjà décompressé
        if os.path.exists(decompressed_path):
            print(f"⏩ Déjà décompressé : {os.path.basename(decompressed_path)}")
            return decompressed_path
        try:
            with gzip.open(file_path, 'rb') as f_in, open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(file_path)
            return decompressed_path
        except Exception as e:
            print(f"❌ Erreur de décompression {file_path} : {e}")
            return file_path
    return file_path

def download_hdf5(md, exp_id, out_dir):
    """
    Télécharge le premier fichier HDF5 (ou HDF5.gz) d'une expérience.
    Retourne le chemin local téléchargé (compressé ou non).
    """
    files = md.getExperimentFiles(exp_id)
    for f in files:
        if not (f.name.endswith(".hdf5") or f.name.endswith(".hdf5.gz")):
            continue
        local_path = os.path.join(out_dir, os.path.basename(f.name))
        try:
            md.downloadFile(f.name, local_path, user_name, user_email, user_affiliation)
            return local_path  # Pas de décompression ici
        except Exception as e:
            print(f"❌ Erreur de téléchargement {f.name} : {e}")
            continue
    return None

def traiter_date(date_obj, md, out_dir):
    """
    Recherche les expériences TEC d'une date et télécharge la première valide.
    """
    y, m, d = date_obj.year, date_obj.month, date_obj.day
    exps = md.getExperiments(
        0, y, m, d, 0, 0, 0,
        y, m, d, 23, 59, 59, 0
    )
    tec_exps = [e for e in exps if "TEC" in e.name]
    if not tec_exps:
        return None

    for exp in tec_exps:
        local = download_hdf5(md, exp.id, out_dir)
        if local:
            return local
    return None

def telecharger_donnees_tec(start_date: datetime.date,
                            end_date:   datetime.date,
                            output_dir: str) -> list[str]:
    """
    Télécharge tous les fichiers TEC entre deux dates.
    Puis les décompresse s’ils sont .gz.
    Retourne la liste des fichiers finaux (décompressés).
    """
    os.makedirs(output_dir, exist_ok=True)
    md = mw.MadrigalData(madrigal_url)
    downloaded = []
    cur = start_date

    while cur <= end_date:
        print(f"📅 Traitement du {cur.isoformat()}")
        result = traiter_date(cur, md, output_dir)
        if result:
            print(f"✅ Fichier téléchargé : {os.path.basename(result)}")
            downloaded.append(result)
        else:
            print(f"❌ Aucun fichier TEC pour {cur.isoformat()}")
        cur += datetime.timedelta(days=1)

    # Décompression de tous les fichiers .gz
    decompressed = []
    for f in downloaded:
        final_path = decompress_gz(f)
        print(f"📦 Fichier prêt : {os.path.basename(final_path)}")
        decompressed.append(final_path)

    return decompressed
