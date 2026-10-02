# Fuel Price India : prédiction du prix de l'essence

Projet de data science sur les prix quotidiens des carburants dans 695 villes indiennes (mai à juillet 2024).
Objectif : prédire le prix de l'essence d'une ville à partir de son État et de son prix du diesel.

## Démarrage rapide

```bash
git clone <url-du-repo>
cd fuel-price-india
python -m venv .venv
# Windows : .venv\Scripts\activate      macOS / Linux : source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
```

## Structure

```
fuel-price-india/
├── data/raw/fuel_price_india.arff   données d'entrée (seul fichier de données versionné)
├── src/
│   ├── config.py                    chemins et paramètres partagés
│   ├── 01_nettoyage.py              ARFF brut  -> data/processed/fuel_price_clean.csv
│   ├── 02_graphes.py                CSV propre -> figures/01..04_*.png
│   ├── 03_entrainement.py           CSV propre -> models/*.joblib + metriques.json + figures/05..06
│   └── 04_generer_doc.py            metriques.json -> docs/model_cards/*.md + docs/generated/
├── docs/
│   ├── datacards/fuel_price_datacard.md
│   ├── explication_nettoyage.md
│   ├── documentation_technique.docx  architecture, données, modèles, scripts
│   ├── support_onboarding.docx       installation pas à pas + exercice
│   └── modele_documentation.dotx     modèle Word commun aux deux documents
├── run_pipeline.py                  lance les 4 étapes dans l'ordre
├── requirements.txt
└── .gitignore                       exclut tout ce qui est généré
```

Les dossiers `data/processed/`, `figures/`, `models/`, `docs/model_cards/` et `docs/generated/` sont **générés** par le pipeline et ne sont pas versionnés.
