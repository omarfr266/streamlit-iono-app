import streamlit as st
from datetime import datetime
import os
import re
from scripts.igs_downloader import download_and_uncompress_ionex as download_ionex_range
from scripts.generation_excel import generer_excel_TEC_par_heure
from scripts.plot_ionex_map import afficher_carte_TEC_fichier
from scripts.madrigal_downloader import telecharger_donnees_tec
from scripts.madrigal_carte import lire_tec_ascii





st.set_page_config(page_title="IONEX App", layout="centered")
st.title("📡 Application IONEX - Traitement GNSS")

choix = st.selectbox("🧭 Choisis une action :", [
    "Télécharger fichiers IONEX",
    "Téléchargement via Madrigal",  
    "Correction fichiers IONEX",
    "Générer Excel TEC (zone précise)",
    "Affichage série temporelle TEC",
    "Afficher carte TEC globale",
    "Animation carte TEC",
     "Afficher carte TEC depuis HDF5.gz"
])



# === Option 1 : Télécharger fichiers IONEX ===
if choix == "Télécharger fichiers IONEX":
    st.markdown("### 📥 Téléchargement IONEX")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date de début", datetime(2024, 1, 1))
    with col2:
        end_date = st.date_input("Date de fin", datetime(2024, 1, 3))

    # 📁 Spécifier le dossier de destination
    dossier = st.text_input("📁 Dossier de téléchargement (ex: ./ionex_data)", value="./ionex_data")

    if st.button("📥 Télécharger"):
        if start_date > end_date:
            st.error("⚠️ Date de début > date de fin.")
        else:
            # Créer le dossier s'il n'existe pas
            os.makedirs(dossier, exist_ok=True)

            with st.spinner("Téléchargement en cours..."):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d") if isinstance(start_date, str) else start_date
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") if isinstance(end_date, str) else end_date

                logs = download_ionex_range(start_dt, end_dt, dossier)  # 👈 passe le chemin ici

            if not logs:
                st.warning("⚠️ Aucun fichier traité ou erreur durant le téléchargement.")
            else:
                st.success("✅ Fichiers téléchargés :")
                for log in logs:
                    st.write(log)


# === Option  : madrigal ===
elif choix == "Téléchargement via Madrigal":
    st.markdown("### 🌐 Téléchargement des fichiers IONEX via Madrigal")

    col1, col2 = st.columns(2)
    with col1:
        date_debut = st.date_input("📅 Date de début", datetime(2024, 1, 1))
    with col2:
        date_fin = st.date_input("📅 Date de fin", datetime(2024, 1, 3))

    dossier_sortie = st.text_input("📁 Dossier de sortie", "./ionex_madrigal")

    if st.button("🌐 Télécharger depuis Madrigal"):
        try:
            os.makedirs(dossier_sortie, exist_ok=True)
            with st.spinner("Téléchargement depuis Madrigal en cours..."):
                logs = telecharger_donnees_tec(date_debut, date_fin, dossier_sortie)  # ✅ Appelle la bonne fonction

            if logs:
                st.success("✅ Téléchargement terminé :")
                for log in logs:
                    st.write(log)
            else:
                st.warning("⚠️ Aucun fichier téléchargé.")

        except Exception as e:
            st.error(f"❌ Erreur lors du téléchargement : {e}")



# === Option 2 : Correction fichiers IONEX ===
elif choix == "Correction fichiers IONEX":
    st.markdown("### 🧹 Correction des fichiers IONEX")

    folder = st.text_input("📁 Dossier source des fichiers IONEX :", "ionex_files")
    output_folder = st.text_input("📁 Dossier de sortie (corrigé) :", "ionex_files/corrected")

    if st.button("🔧 Lancer la correction"):
        try:
            os.makedirs(output_folder, exist_ok=True)

            # Extensions des fichiers à corriger (ancien + nouveau format)
            valid_ext = (".inx", ".i", ".ionex", "")
            ionex_files = [
                f for f in os.listdir(folder)
                if f.lower().endswith(valid_ext) and os.path.isfile(os.path.join(folder, f))
            ]

            if not ionex_files:
                st.warning("⚠️ Aucun fichier IONEX trouvé dans le dossier spécifié.")
            else:
                for filename in ionex_files:
                    filepath = os.path.join(folder, filename)
                    output_filepath = os.path.join(output_folder, filename)

                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()

                        corrected_lines = []
                        for line in lines:
                            if "LAT/LON1/LON2/DLON/H" in line:
                                # Correction d’un format erroné par exemple : 60.0-5.0 devient 60.0 -5.0
                                line = re.sub(r'(\d+\.\d+)-(\d+\.\d+)', r'\1 -\2', line)
                            corrected_lines.append(line)

                        with open(output_filepath, 'w', encoding='utf-8') as f:
                            f.writelines(corrected_lines)

                        st.success(f"✅ Corrigé : {filename}")
                    except Exception as e:
                        st.error(f"❌ Erreur avec {filename} : {e}")

        except Exception as e:
            st.error(f"❌ Erreur globale : {e}")


# === Option 3 : Générer série temporelle ===
elif choix == "Générer Excel TEC (zone précise)":
    st.markdown("### 📄 Générer un fichier Excel TEC à partir des fichiers IONEX corrigés")

    folder = st.text_input("📂 Dossier des fichiers IONEX", "ionex_files/corrected")
    target_lat = st.number_input("Latitude de l'épicentre (°N)", value=21.0)
    target_lon = st.number_input("Longitude de l'épicentre (°E)", value=96.0)
    output_path = st.text_input("📁 Chemin de sauvegarde Excel", "outputs/tec_par_heure.xlsx")

    if st.button("📊 Lancer l’analyse"):
        try:
            from scripts.generation_excel import generer_excel_TEC_par_heure
            chemin = generer_excel_TEC_par_heure(folder, target_lat, target_lon, output_path)
            st.success(f"✅ Fichier Excel généré : {chemin}")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
# === Option 4 : afficher série temporelle ===
elif choix == "Affichage série temporelle TEC":
    st.markdown("### 📈 Affichage de la série temporelle du TEC")

    excel_file = st.text_input("📂 Chemin du fichier Excel TEC", "outputs/tec_par_heure.xlsx")
    seisme_str = st.text_input("📅 Date/heure du séisme (ex: 2025-03-28 03:00:00)", "2025-03-28 03:00:00")
    k = st.number_input("⚖️ Facteur k pour limites de contrôle (ex: 2 pour Mw >= 6.0)", min_value=0.1, max_value=5.0, value=2.0, step=0.1)

    if st.button("📊 Afficher la série temporelle"):
        try:
            from scripts.serie_temporelle import afficher_serie_temporelle_tec
            fig = afficher_serie_temporelle_tec(excel_file, seisme_str, k=k)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"❌ Erreur lors de l'affichage : {e}")

# === Option 5 =========================================================
elif choix == "Afficher carte TEC globale":
    st.markdown("### 🌍 Affichage d'une carte TEC globale à partir d'un fichier IONEX")

    fichier_ionex = st.file_uploader("📂 Sélectionner un fichier IONEX corrigé")

    heure = st.number_input("🕒 Heure UTC à afficher (0 à 23)", min_value=0, max_value=23, value=12)

    col1, col2 = st.columns(2)
    with col1:
        lat_epi = st.number_input("🧭 Latitude de l'épicentre", min_value=-90.0, max_value=90.0, value=23.0)
    with col2:
        lon_epi = st.number_input("🧭 Longitude de l'épicentre", min_value=-180.0, max_value=180.0, value=96.0)

    if fichier_ionex is not None and st.button("🌍 Afficher la carte TEC"):
        try:
            temp_path = "temp_ionex.ionex"
            with open(temp_path, "wb") as f:
                f.write(fichier_ionex.read())

            fig = afficher_carte_TEC_fichier(temp_path, heure_utc=heure,
                                             epicenter_lat=lat_epi, epicenter_lon=lon_epi)

            st.pyplot(fig)
        except Exception as e:
            st.error(f"❌ Erreur lors de l'affichage : {e}")

# === Option 6 =========================================================

elif choix == "Animation carte TEC":
    st.markdown("### 🎥 Animation carte TEC")

    fichier = st.file_uploader("📂 Sélectionne un fichier IONEX corrigé ou TEC", type=["ionex", "inx", "txt", "gz", "xlsx"])

    seisme_lat = st.number_input("Latitude de l'épicentre", format="%.1f")
    seisme_lon = st.number_input("Longitude de l'épicentre", format="%.1f")

    if fichier is not None:
        if st.button("▶️ Afficher l'animation TEC"):
            with st.spinner("Génération de l'animation en cours... ⏳"):
                try:
                    from scripts.video import generer_animation_tec  # adapte le chemin si besoin

                    # Sauvegarde temporaire du fichier uploadé
                    temp_path = "temp_uploaded_file"
                    with open(temp_path, "wb") as f:
                        f.write(fichier.read())

                    # Appel de la fonction pour générer l'animation et récupérer le chemin du fichier GIF
                    animation_path = generer_animation_tec(temp_path, seisme_lat, seisme_lon)

                    # Affichage dans Streamlit
                    with open(animation_path, "rb") as gif_file:
                        gif_bytes = gif_file.read()
                    st.image(gif_bytes)

                except Exception as e:
                    st.error(f"❌ Erreur durant la génération de l'animation : {e}")

                finally:
                    # Nettoyage des fichiers temporaires si présents
                    import os
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    if 'animation_path' in locals() and os.path.exists(animation_path):
                        os.remove(animation_path)



# === Option 7 : Afficher carte TEC depuis HDF5.gz ===
elif choix == "Afficher carte TEC depuis HDF5.gz":
    st.markdown("### 🗺️ Affichage carte TEC depuis fichier .HDF5.gz ou .txt")

    fichier = st.file_uploader("📂 Sélectionne un fichier .HDF5.gz ou .txt", type=["txt", "gz"])

    heure_choisie = st.number_input("🕒 Heure UTC à afficher", min_value=0, max_value=23, value=12)

    if fichier is not None and st.button("🗺️ Afficher carte TEC"):
        try:
            import tempfile
            import gzip
            import os

            suffix = ".gz" if fichier.name.endswith(".gz") else ".txt"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(fichier.read())
                tmp_path = tmp_file.name

            # Si c’est un fichier .gz, on le décompresse en .txt
            if suffix == ".gz":
                with gzip.open(tmp_path, 'rb') as f_in:
                    txt_path = tmp_path.replace(".gz", ".txt")
                    with open(txt_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                os.remove(tmp_path)  # supprime le .gz temporaire
            else:
                txt_path = tmp_path  # c’est déjà un .txt

            fig = lire_tec_ascii(txt_path, heure_choisie)

            st.pyplot(fig)

        except Exception as e:
            st.error(f"❌ Erreur lors de l'affichage : {e}")
