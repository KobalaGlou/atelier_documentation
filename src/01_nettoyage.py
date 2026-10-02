"""
Étape 1 du pipeline : nettoyage du dataset « Fuel-Price » (prix des carburants en Inde, 2024).

Entrée  : data/raw/fuel_price_india.arff
Sortie  : data/processed/fuel_price_clean.csv

Utilisation (depuis la racine du projet) :
    python src/01_nettoyage.py
"""

import csv
import io

import pandas as pd

from config import (COLONNES_PRIX, COLONNES_TEXTE, FICHIER_BRUT, FICHIER_PROPRE,
                    FORMAT_DATE, PRIX_MAX, PRIX_MIN, creer_dossiers)

# ---------------------------------------------------------------------------
# Paramètres (définis dans src/config.py)
# ---------------------------------------------------------------------------
FICHIER_ENTREE = FICHIER_BRUT
FICHIER_SORTIE = FICHIER_PROPRE


def afficher(titre, valeur=""):
    """Affiche une ligne du rapport de nettoyage."""
    print(f"  - {titre:<45} {valeur}")


# ---------------------------------------------------------------------------
# Étape 1 : lecture du fichier ARFF
# ---------------------------------------------------------------------------
def lire_arff(chemin):
    """Lit un fichier ARFF : noms de colonnes depuis l'en-tête, données après @DATA."""
    colonnes = []
    lignes_donnees = []
    dans_donnees = False

    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne_nette = ligne.strip()
            if not ligne_nette or ligne_nette.startswith("%"):
                continue  # ligne vide ou commentaire
            if dans_donnees:
                lignes_donnees.append(ligne_nette)
            elif ligne_nette.upper().startswith("@ATTRIBUTE"):
                colonnes.append(ligne_nette.split()[1])
            elif ligne_nette.upper().startswith("@DATA"):
                dans_donnees = True

    df = pd.read_csv(
        io.StringIO("\n".join(lignes_donnees)),
        header=None,
        names=colonnes,
        quotechar="'",   # les noms d'État contenant des espaces sont entre apostrophes
        dtype=str,       # tout en texte : on convertit nous-mêmes à l'étape 3
        keep_default_na=False,
    )
    return df


print("=" * 70)
print("NETTOYAGE DU DATASET FUEL-PRICE")
print("=" * 70)

print("\n[1] Lecture du fichier")
df = lire_arff(FICHIER_ENTREE)
nb_lignes_initial = len(df)
afficher("Fichier lu", FICHIER_ENTREE)
afficher("Dimensions initiales", f"{df.shape[0]} lignes x {df.shape[1]} colonnes")
afficher("Colonnes", ", ".join(df.columns))

# ---------------------------------------------------------------------------
# Étape 2 : nettoyage des colonnes texte
# ---------------------------------------------------------------------------
print("\n[2] Nettoyage des colonnes texte")
for col in COLONNES_TEXTE + ["date"]:
    df[col] = df[col].str.strip()                            # espaces en début et fin
for col in COLONNES_TEXTE:
    df[col] = df[col].str.replace(r"\s+", " ", regex=True)  # espaces multiples
afficher("Villes distinctes (noms)", df["city_name"].nunique())
afficher("États distincts", df["state_name"].nunique())

# ---------------------------------------------------------------------------
# Étape 3 : conversion des types
# ---------------------------------------------------------------------------
print("\n[3] Conversion des types")

# « ? » est le code ARFF des valeurs manquantes : on le remplace par NaN
for col in COLONNES_PRIX:
    df[col] = df[col].replace("?", pd.NA)
    df[col] = pd.to_numeric(df[col], errors="coerce")
    afficher(f"{col} converti en nombre", f"{df[col].isna().sum()} valeur(s) manquante(s)")

df["date"] = pd.to_datetime(df["date"], format=FORMAT_DATE, errors="coerce")
afficher("date convertie en datetime", f"{df['date'].isna().sum()} date(s) invalide(s)")

# ---------------------------------------------------------------------------
# Étape 4 : suppression des doublons
# ---------------------------------------------------------------------------
print("\n[4] Suppression des doublons")
avant = len(df)
df = df.drop_duplicates()
afficher("Doublons exacts supprimés", avant - len(df))

avant = len(df)
df = df.drop_duplicates(subset=["city_name", "state_name", "date"], keep="first")
afficher("Doublons (ville, État, date) supprimés", avant - len(df))

# ---------------------------------------------------------------------------
# Étape 5 : traitement des valeurs manquantes
# ---------------------------------------------------------------------------
print("\n[5] Traitement des valeurs manquantes")
masque_manquant = df[COLONNES_PRIX + ["date"]].isna().any(axis=1)
lignes_manquantes = df[masque_manquant]
if not lignes_manquantes.empty:
    resume = lignes_manquantes.groupby(["city_name", "state_name"]).size()
    for (ville, etat), n in resume.items():
        afficher(f"{ville} ({etat})", f"{n} ligne(s)")
df = df[~masque_manquant]
afficher("Lignes supprimées (prix ou date manquants)", int(masque_manquant.sum()))

# ---------------------------------------------------------------------------
# Étape 6 : contrôle de plausibilité des prix
# ---------------------------------------------------------------------------
print("\n[6] Contrôle de plausibilité des prix")
masque_aberrant = pd.Series(False, index=df.index)
for col in COLONNES_PRIX:
    hors_bornes = (df[col] < PRIX_MIN) | (df[col] > PRIX_MAX)
    afficher(f"{col} hors [{PRIX_MIN:.0f} ; {PRIX_MAX:.0f}]", int(hors_bornes.sum()))
    masque_aberrant |= hors_bornes
df = df[~masque_aberrant]
afficher("Lignes supprimées (prix aberrants)", int(masque_aberrant.sum()))

# ---------------------------------------------------------------------------
# Étape 7 : signalement des incohérences (sans suppression)
# ---------------------------------------------------------------------------
print("\n[7] Signalement des incohérences")
# L'essence premium est normalement plus chère que l'essence ordinaire.
df["flag_xpremium_incoherent"] = df["xpremium"] < df["petrol"]
incoherents = df[df["flag_xpremium_incoherent"]]
afficher("Lignes où xpremium < petrol", len(incoherents))
for (ville, etat), n in incoherents.groupby(["city_name", "state_name"]).size().items():
    afficher(f"   dont {ville} ({etat})", n)

# ---------------------------------------------------------------------------
# Étape 8 : identifiant unique de ville
# ---------------------------------------------------------------------------
print("\n[8] Création d'un identifiant unique de ville")
df["city_id"] = df["city_name"] + " - " + df["state_name"]
homonymes = df.groupby("city_name")["state_name"].nunique()
homonymes = homonymes[homonymes > 1].index.tolist()
afficher("Noms de villes présents dans plusieurs États", ", ".join(homonymes) or "aucun")
afficher("Villes uniques (city_id)", df["city_id"].nunique())

# ---------------------------------------------------------------------------
# Étape 9 : tri, réorganisation et export
# ---------------------------------------------------------------------------
print("\n[9] Tri et export")
df = df.sort_values(["state_name", "city_name", "date"]).reset_index(drop=True)
df = df[["city_id", "city_name", "state_name", "date"] + COLONNES_PRIX
        + ["flag_xpremium_incoherent"]]

creer_dossiers()
df.to_csv(FICHIER_SORTIE, index=False, encoding="utf-8",
          date_format="%Y-%m-%d", quoting=csv.QUOTE_MINIMAL)
afficher("Fichier écrit", FICHIER_SORTIE)

# ---------------------------------------------------------------------------
# Bilan
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("BILAN")
print("=" * 70)
afficher("Lignes avant nettoyage", nb_lignes_initial)
afficher("Lignes après nettoyage", len(df))
afficher("Lignes supprimées", nb_lignes_initial - len(df))
afficher("Période", f"{df['date'].min():%d/%m/%Y} -> {df['date'].max():%d/%m/%Y}")
afficher("Valeurs manquantes restantes", int(df.isna().sum().sum()))
print("\nStatistiques des prix après nettoyage (roupies par litre) :")
print(df[COLONNES_PRIX].describe().round(2).to_string())
