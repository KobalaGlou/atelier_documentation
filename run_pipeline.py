"""
Lance tout le pipeline dans l'ordre :
  1. nettoyage des données   2. graphes   3. entraînement des modèles   4. documentation

Utilisation (depuis la racine du projet) :
    python run_pipeline.py
"""

import subprocess
import sys
import time
from pathlib import Path

ETAPES = ["01_nettoyage.py", "02_graphes.py", "03_entrainement.py", "04_generer_doc.py"]
DOSSIER_SRC = Path(__file__).resolve().parent / "src"

debut = time.time()
for script in ETAPES:
    print(f"\n{'#' * 70}\n# {script}\n{'#' * 70}")
    resultat = subprocess.run([sys.executable, str(DOSSIER_SRC / script)])
    if resultat.returncode != 0:
        sys.exit(f"\nÉchec de {script} (code {resultat.returncode}) : pipeline arrêté.")
print(f"\nPipeline terminé en {time.time() - debut:.0f} secondes.")
