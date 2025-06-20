import os
import re

folder = r"D:\python\data"
output_folder = r"D:\python\data\corrected"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

ionex_files = [f for f in os.listdir(folder) if f.lower().endswith((".inx", ".i", ".ionex"))]

for filename in ionex_files:
    filepath = os.path.join(folder, filename)
    output_filepath = os.path.join(output_folder, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        corrected_lines = []
        for line in lines:
            if "LAT/LON1/LON2/DLON/H" in line:
                # Remplacer les champs collés comme '87.5-180.0' par '87.5 -180.0'
                line = re.sub(r'(\d+\.\d+)-(\d+\.\d+)', r'\1 -\2', line)
            corrected_lines.append(line)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.writelines(corrected_lines)
        print(f"✅ Fichier corrigé : {output_filepath}")
    except Exception as e:
        print(f"❌ Erreur lors de la correction de {filename} : {e}")