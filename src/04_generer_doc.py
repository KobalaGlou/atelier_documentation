"""
Étape 4 du pipeline : génération automatique de la documentation des modèles.

Entrée  : models/metriques.json (écrit par 03_entrainement.py)
Sorties : docs/model_cards/<nom_du_modele>.md   (une model card par modèle)
          docs/generated/rapport_resultats.md    (synthèse : tableau comparatif + figures)

Les chiffres ne sont jamais recopiés à la main : ils sont lus dans metriques.json.
Ainsi, la documentation reste à jour à chaque réentraînement.

Utilisation (depuis la racine du projet) :
    python src/04_generer_doc.py
"""

import json

from config import FICHIER_METRIQUES, MODEL_CARDS, RAPPORTS, creer_dossiers

DESCRIPTIONS = {
    "baseline_moyenne": "Modèle de référence : prédit toujours le prix moyen de l'essence "
                        "du jeu d'entraînement. Il sert d'étalon : un vrai modèle doit faire mieux.",
    "regression_lineaire": "Régression linéaire : prix = constante propre à chaque État "
                           "+ a × diesel + b × jour + c × jour_semaine.",
    "random_forest": "Forêt aléatoire : moyenne de 100 arbres de décision entraînés sur "
                     "des sous-échantillons des données.",
    "gradient_boosting": "Gradient boosting (HistGradientBoosting) : arbres construits "
                         "les uns après les autres, chacun corrigeant les erreurs des précédents.",
}


def fmt(x, decimales=3):
    return f"{x:.{decimales}f}".replace(".", ",")


def model_card(nom, m, meta):
    cv, test, dec = m["validation_croisee"], m["test"], meta["decoupage"]
    est_meilleur = nom == meta["meilleur_modele"]
    params = "\n".join(f"| `{k}` | `{v}` |" for k, v in sorted(m["parametres"].items()))
    erreurs_etat = ""
    if est_meilleur:
        pires = list(meta["erreur_par_etat_test"].items())[:5]
        lignes = "\n".join(f"| {etat} | {fmt(err)} |" for etat, err in pires)
        erreurs_etat = (
            "\n### États où l'erreur est la plus forte (jeu de test)\n\n"
            "| État | MAE (₹/L) |\n|---|---|\n" + lignes + "\n"
        )

    return f"""# Model card : {nom}

{"**Modèle retenu** (meilleure MAE en validation croisée)." if est_meilleur else "Modèle candidat (non retenu)."}

## 1. Description

| Élément | Valeur |
|---|---|
| Nom | `{nom}` |
| Type | `{m["regresseur"]}` (scikit-learn {meta["versions"]["scikit-learn"]}) |
| Fichier | `{m["fichier"]}` |
| Date d'entraînement | {meta["date_entrainement"]} |
| Description | {DESCRIPTIONS.get(nom, "")} |

## 2. Usage prévu

- **Tâche :** régression. Prédire le prix de l'essence (`{meta["cible"]}`, en ₹ par litre) d'une ville indienne.
- **Variables d'entrée :** {", ".join(f"`{v}`" for v in meta["variables"])}.
- **Cas d'usage :** estimer un prix d'essence manquant quand le prix du diesel de la ville est connu.
- **Hors périmètre :** prévoir les prix futurs (le modèle n'a vu que mai à juillet 2024), les États absents du dataset et les villes hors d'Inde.

## 3. Données

- Source : `data/processed/fuel_price_clean.csv`. Voir la datacard dans `docs/datacards/fuel_price_datacard.md`.
- Découpage : {dec["methode"]}.
- Train : {dec["lignes_train"]} lignes ({dec["villes_train"]} villes). Test : {dec["lignes_test"]} lignes ({dec["villes_test"]} villes).
- Les villes du test n'ont **jamais** été vues pendant l'entraînement.

## 4. Performances

| Métrique | Validation croisée ({dec["nb_folds"]} folds) | Test |
|---|---|---|
| MAE (₹/L) | {fmt(cv["mae"])} (± {fmt(cv["mae_ecart_type"])}) | {fmt(test["mae"])} |
| RMSE (₹/L) | {fmt(cv["rmse"])} | {fmt(test["rmse"])} |
| R² | {fmt(cv["r2"], 4)} | {fmt(test["r2"], 4)} |
{erreurs_etat}
## 5. Hyperparamètres

| Paramètre | Valeur |
|---|---|
{params}

## 6. Limites et précautions

- Le modèle dépend du prix du diesel : sans ce prix, il ne peut rien prédire.
- Les données couvrent environ 2 mois très stables : le modèle ne capte ni les hausses de taxes ni les chocs de prix.
- Un État inconnu est encodé comme « aucun État » (`handle_unknown="ignore"`) : la prédiction est alors peu fiable.
- Le dataset contient des incohérences signalées (Chamoli : `xpremium < petrol`) ; elles n'affectent pas la cible `petrol`.

## 7. Utilisation

```python
import joblib
import pandas as pd

modele = joblib.load("{m["fichier"]}")
exemple = pd.DataFrame([{{"state_name": "Delhi", "diesel": 87.62, "jour": 30, "jour_semaine": 2}}])
print(modele.predict(exemple))
```
"""


def rapport(meta):
    lignes = []
    for nom, m in meta["modeles"].items():
        marque = " **(retenu)**" if nom == meta["meilleur_modele"] else ""
        lignes.append(f"| [{nom}](../model_cards/{nom}.md){marque} | "
                      f"{fmt(m['validation_croisee']['mae'])} | {fmt(m['test']['mae'])} | "
                      f"{fmt(m['test']['rmse'])} | {fmt(m['test']['r2'], 4)} |")
    return f"""# Rapport de résultats

Généré automatiquement par `src/04_generer_doc.py` à partir de `models/metriques.json`
(entraînement du {meta["date_entrainement"]}).

## Comparaison des modèles

| Modèle | MAE CV | MAE test | RMSE test | R² test |
|---|---|---|---|---|
{chr(10).join(lignes)}

Modèle retenu : **{meta["meilleur_modele"]}** (critère : MAE moyenne en validation croisée).

## Figures

![Distribution des prix](../../figures/01_distribution_prix.png)
![Prix moyen par État](../../figures/02_prix_moyen_par_etat.png)
![Essence vs diesel](../../figures/03_essence_vs_diesel.png)
![Évolution des prix](../../figures/04_evolution_prix.png)
![Comparaison des modèles](../../figures/05_comparaison_modeles.png)
![Prédit vs réel](../../figures/06_predictions_vs_reel.png)
"""


def main():
    creer_dossiers()
    if not FICHIER_METRIQUES.exists():
        raise SystemExit("models/metriques.json introuvable : lancez d'abord "
                         "python src/03_entrainement.py")
    meta = json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))

    print("Documentation générée :")
    for nom, m in meta["modeles"].items():
        chemin = MODEL_CARDS / f"{nom}.md"
        chemin.write_text(model_card(nom, m, meta), encoding="utf-8")
        print(f"  - docs/model_cards/{chemin.name}")

    chemin = RAPPORTS / "rapport_resultats.md"
    chemin.write_text(rapport(meta), encoding="utf-8")
    print(f"  - docs/generated/{chemin.name}")


if __name__ == "__main__":
    main()
