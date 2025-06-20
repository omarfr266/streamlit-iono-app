import datetime
from scripts.madrigal_downloader import telecharger_donnees_tec

# Dates de début et de fin
start = datetime.date(2024, 1, 1)
end = datetime.date(2024, 1, 3)

# Appel du téléchargement
fichiers = telecharger_donnees_tec(start, end)

print("Fichiers téléchargés :", fichiers)
