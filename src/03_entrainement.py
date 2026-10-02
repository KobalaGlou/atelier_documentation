"""
Étape 3 du pipeline : entraînement, comparaison et export des modèles.

Problème : prédire le prix de l'essence (petrol) d'une ville à partir de son État,
de son prix du diesel et de la date. Cas d'usage : estimer un prix d'essence
manquant quand le prix du diesel est connu.

Entrée  : data/processed/fuel_price_clean.csv
Sorties : models/<nom_du_modele>.joblib   (un fichier par modèle)
          models/metriques.json           (scores, paramètres, meilleur modèle)
          figures/05_comparaison_modeles.png
          figures/06_predictions_vs_reel.png

Utilisation (depuis la racine du projet) :
    python src/03_entrainement.py
"""

import json
from datetime import datetime

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from config import (CIBLE, COULEURS, DPI, FICHIER_METRIQUES, FICHIER_PROPRE, FIGURES,
                    GRAINE, GRILLE, GROUPE, MODELES, NB_FOLDS, TAILLE_TEST,
                    TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VARIABLES_CATEGORIELLES,
                    VARIABLES_NUMERIQUES, creer_dossiers)

VARIABLES = VARIABLES_CATEGORIELLES + VARIABLES_NUMERIQUES


# ---------------------------------------------------------------------------
# 1. Préparation des variables
# ---------------------------------------------------------------------------
def preparer_variables(df):
    """Ajoute les variables temporelles dérivées de la date."""
    df = df.copy()
    df["jour"] = (df["date"] - df["date"].min()).dt.days   # 0 = premier jour du dataset
    df["jour_semaine"] = df["date"].dt.dayofweek            # 0 = lundi ... 6 = dimanche
    return df


# ---------------------------------------------------------------------------
# 2. Définition des modèles candidats
# ---------------------------------------------------------------------------
def creer_modeles():
    """Chaque modèle est un Pipeline : encodage de l'État puis régresseur."""
    def pipeline(regresseur):
        pretraitement = ColumnTransformer(
            [("etat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
              VARIABLES_CATEGORIELLES)],
            remainder="passthrough",  # les variables numériques passent telles quelles
        )
        return Pipeline([("pretraitement", pretraitement), ("modele", regresseur)])

    return {
        "baseline_moyenne": pipeline(DummyRegressor(strategy="mean")),
        "regression_lineaire": pipeline(LinearRegression()),
        "random_forest": pipeline(RandomForestRegressor(
            n_estimators=100, min_samples_leaf=5, n_jobs=-1, random_state=GRAINE)),
        "gradient_boosting": pipeline(HistGradientBoostingRegressor(random_state=GRAINE)),
    }


def scores(y_vrai, y_pred):
    return {
        "mae": float(mean_absolute_error(y_vrai, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_vrai, y_pred))),
        "r2": float(r2_score(y_vrai, y_pred)),
    }


# ---------------------------------------------------------------------------
# 3. Graphes de résultats
# ---------------------------------------------------------------------------
def style_axes(ax, titre, x_label, y_label):
    ax.set_title(titre, loc="left", fontsize=13, color=TEXTE_PRINCIPAL, pad=12)
    ax.set_xlabel(x_label, color=TEXTE_SECONDAIRE)
    ax.set_ylabel(y_label, color=TEXTE_SECONDAIRE)
    ax.tick_params(colors=TEXTE_SECONDAIRE)
    ax.grid(color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)


def graphe_comparaison(resultats):
    noms = list(resultats)
    mae = [resultats[n]["validation_croisee"]["mae"] for n in noms]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(noms, mae, color=COULEURS["petrol"], height=0.6)
    for y, valeur in enumerate(mae):
        ax.text(valeur, y, f"  {valeur:.3f}", va="center", fontsize=9, color=TEXTE_SECONDAIRE)
    ax.set_xscale("log")
    style_axes(ax, "Erreur moyenne absolue en validation croisée (plus bas = meilleur)",
               "MAE (₹ par litre, échelle logarithmique)", "")
    ax.grid(axis="y", visible=False)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIGURES / "05_comparaison_modeles.png", dpi=DPI, facecolor="white")
    plt.close(fig)


def graphe_predictions(y_vrai, y_pred, nom):
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(y_vrai, y_pred, s=8, alpha=0.4, color=COULEURS["petrol"])
    bornes = [min(y_vrai.min(), y_pred.min()), max(y_vrai.max(), y_pred.max())]
    ax.plot(bornes, bornes, color=TEXTE_SECONDAIRE, linewidth=1, linestyle="--",
            label="Prédiction parfaite")
    style_axes(ax, f"Prédit vs réel sur le jeu de test ({nom})",
               "Prix réel de l'essence (₹/L)", "Prix prédit (₹/L)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES / "06_predictions_vs_reel.png", dpi=DPI, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------
def main():
    creer_dossiers()
    df = preparer_variables(pd.read_csv(FICHIER_PROPRE, parse_dates=["date"]))
    X, y, groupes = df[VARIABLES], df[CIBLE], df[GROUPE]

    # Découpage train / test PAR VILLE : les villes du test ne sont jamais vues
    # pendant l'entraînement (sinon le modèle "connaîtrait" déjà leurs prix).
    decoupage = GroupShuffleSplit(n_splits=1, test_size=TAILLE_TEST, random_state=GRAINE)
    idx_train, idx_test = next(decoupage.split(X, y, groupes))
    X_train, X_test = X.iloc[idx_train], X.iloc[idx_test]
    y_train, y_test = y.iloc[idx_train], y.iloc[idx_test]
    print(f"Train : {len(X_train)} lignes ({groupes.iloc[idx_train].nunique()} villes)")
    print(f"Test  : {len(X_test)} lignes ({groupes.iloc[idx_test].nunique()} villes)\n")

    resultats = {}
    for nom, modele in creer_modeles().items():
        # Validation croisée sur le train, elle aussi groupée par ville
        cv = cross_validate(
            modele, X_train, y_train, groups=groupes.iloc[idx_train],
            cv=GroupKFold(n_splits=NB_FOLDS),
            scoring=("neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"),
        )
        # Réentraînement sur tout le train, puis évaluation sur le test
        modele.fit(X_train, y_train)
        joblib.dump(modele, MODELES / f"{nom}.joblib")

        resultats[nom] = {
            "validation_croisee": {
                "mae": float(-cv["test_neg_mean_absolute_error"].mean()),
                "rmse": float(-cv["test_neg_root_mean_squared_error"].mean()),
                "r2": float(cv["test_r2"].mean()),
                "mae_ecart_type": float(cv["test_neg_mean_absolute_error"].std()),
            },
            "test": scores(y_test, modele.predict(X_test)),
            "regresseur": type(modele.named_steps["modele"]).__name__,
            "parametres": {k: v for k, v in modele.named_steps["modele"].get_params().items()
                           if isinstance(v, (int, float, str, bool, type(None)))},
            "fichier": f"models/{nom}.joblib",
        }
        r = resultats[nom]
        print(f"{nom:<22} CV MAE = {r['validation_croisee']['mae']:.3f}   "
              f"Test MAE = {r['test']['mae']:.3f}   Test R² = {r['test']['r2']:.4f}")

    # Choix du meilleur modèle sur la validation croisée (jamais sur le test)
    meilleur = min(resultats, key=lambda n: resultats[n]["validation_croisee"]["mae"])
    print(f"\nMeilleur modèle (MAE en validation croisée) : {meilleur}")

    meilleur_modele = joblib.load(MODELES / f"{meilleur}.joblib")
    y_pred = meilleur_modele.predict(X_test)
    graphe_comparaison(resultats)
    graphe_predictions(y_test, y_pred, meilleur)

    # Erreur par État sur le test, pour la model card
    erreurs = pd.DataFrame({"etat": X_test["state_name"],
                            "erreur": np.abs(y_test.values - y_pred)})
    erreur_par_etat = erreurs.groupby("etat")["erreur"].mean().sort_values(ascending=False)

    metriques = {
        "date_entrainement": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "versions": {"scikit-learn": sklearn.__version__, "pandas": pd.__version__},
        "cible": CIBLE,
        "variables": VARIABLES,
        "decoupage": {
            "methode": "GroupShuffleSplit par city_id + GroupKFold sur le train",
            "taille_test": TAILLE_TEST, "nb_folds": NB_FOLDS, "graine": GRAINE,
            "lignes_train": int(len(X_train)), "lignes_test": int(len(X_test)),
            "villes_train": int(groupes.iloc[idx_train].nunique()),
            "villes_test": int(groupes.iloc[idx_test].nunique()),
        },
        "meilleur_modele": meilleur,
        "erreur_par_etat_test": {k: float(v) for k, v in erreur_par_etat.items()},
        "modeles": resultats,
    }
    FICHIER_METRIQUES.write_text(json.dumps(metriques, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    print(f"Métriques enregistrées dans {FICHIER_METRIQUES.relative_to(MODELES.parent)}")


if __name__ == "__main__":
    main()
