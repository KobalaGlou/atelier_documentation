"""
Configuration centrale du projet : tous les chemins et paramètres partagés.

Les chemins sont calculés à partir de l'emplacement de ce fichier : les scripts
fonctionnent quel que soit le dossier depuis lequel on les lance.
"""

from pathlib import Path

# --- Dossiers ---------------------------------------------------------------
RACINE = Path(__file__).resolve().parent.parent

DATA_RAW = RACINE / "data" / "raw"              # données d'entrée (versionnées)
DATA_PROCESSED = RACINE / "data" / "processed"  # généré par 01_nettoyage.py
FIGURES = RACINE / "figures"                    # généré par 02 et 03
MODELES = RACINE / "models"                     # généré par 03_entrainement.py
DOCS = RACINE / "docs"
MODEL_CARDS = DOCS / "model_cards"              # généré par 04_generer_doc.py
RAPPORTS = DOCS / "generated"                   # généré par 04_generer_doc.py

# --- Fichiers ---------------------------------------------------------------
FICHIER_BRUT = DATA_RAW / "fuel_price_india.arff"
FICHIER_PROPRE = DATA_PROCESSED / "fuel_price_clean.csv"
FICHIER_METRIQUES = MODELES / "metriques.json"

# --- Données ----------------------------------------------------------------
COLONNES_TEXTE = ["city_name", "state_name"]
COLONNES_PRIX = ["petrol", "diesel", "xpremium"]
FORMAT_DATE = "%d-%m-%y"          # ex. 09-07-24 = 9 juillet 2024
PRIX_MIN, PRIX_MAX = 50.0, 200.0  # bornes de plausibilité (roupies par litre)

# --- Modélisation -----------------------------------------------------------
CIBLE = "petrol"
VARIABLES_CATEGORIELLES = ["state_name"]
VARIABLES_NUMERIQUES = ["diesel", "jour", "jour_semaine"]
GROUPE = "city_id"       # découpage par ville : une ville est soit en train, soit en test
TAILLE_TEST = 0.2
NB_FOLDS = 5
GRAINE = 42              # graine aléatoire : résultats reproductibles

# --- Graphes (palette validée pour les daltonismes, 3 premières couleurs) ---
COULEURS = {"petrol": "#2a78d6", "diesel": "#eb6834", "xpremium": "#1baf7a"}
TEXTE_PRINCIPAL = "#0b0b0b"
TEXTE_SECONDAIRE = "#52514e"
GRILLE = "#e4e3df"
DPI = 150


def creer_dossiers():
    """Crée les dossiers de sortie s'ils n'existent pas encore."""
    for dossier in (DATA_PROCESSED, FIGURES, MODELES, MODEL_CARDS, RAPPORTS):
        dossier.mkdir(parents=True, exist_ok=True)
