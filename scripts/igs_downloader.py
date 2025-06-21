import os
import requests
import gzip
import shutil
import streamlit as st

def download_and_decompress_cddis(base_url, filenames, save_dir):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for filename in filenames:
        url = base_url + filename
        gz_path = os.path.join(save_dir, filename)
        decompressed_path = gz_path.replace(".gz", "")

        try:
            st.info(f"⬇️ Téléchargement : {filename}")
            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code != 200:
                st.error(f"❌ HTTP {response.status_code} : {filename}")
                continue

            if b'<!DOCTYPE html>' in response.content[:200]:
                st.error(f"❌ Contenu HTML détecté : {filename}")
                continue

            # Enregistrer le .gz
            with open(gz_path, 'wb') as f:
                f.write(response.content)
            st.success(f"✅ Téléchargé : {filename}")

            # Décompresser
            with gzip.open(gz_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            st.success(f"📂 Décompressé : {os.path.basename(decompressed_path)}")

        except Exception as e:
            st.error(f"⚠️ Erreur : {e}")
