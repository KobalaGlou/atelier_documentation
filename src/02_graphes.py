"""
Étape 2 du pipeline : génération des graphes d'analyse exploratoire.

Entrée  : data/processed/fuel_price_clean.csv
Sorties : figures/01_distribution_prix.png
          figures/02_prix_moyen_par_etat.png
          figures/03_essence_vs_diesel.png
          figures/04_evolution_prix.png

Utilisation (depuis la racine du projet) :
    python src/02_graphes.py
"""

import matplotlib

matplotlib.use("Agg")  # pas de fenêtre : on écrit directement des fichiers PNG
import matplotlib.pyplot as plt
import pandas as pd

from config import (COLONNES_PRIX, COULEURS, DPI, FICHIER_PROPRE, FIGURES, GRILLE,
                    TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, creer_dossiers)

NOMS = {"petrol": "Essence", "diesel": "Diesel", "xpremium": "Essence premium"}


def style_axes(ax, titre, x_label, y_label):
    """Applique un style sobre : grille discrète, pas de cadre haut/droite."""
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


def enregistrer(fig, nom):
    chemin = FIGURES / nom
    fig.tight_layout()
    fig.savefig(chemin, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"  - {chemin.relative_to(FIGURES.parent)}")


def graphe_distribution(df):
    """Histogramme des trois prix, superposés."""
    fig, ax = plt.subplots(figsize=(9, 5))
    for col in COLONNES_PRIX:
        ax.hist(df[col], bins=40, alpha=0.55, color=COULEURS[col], label=NOMS[col])
    style_axes(ax, "Distribution des prix des carburants (toutes villes, tous jours)",
               "Prix (₹ par litre)", "Nombre de relevés")
    ax.legend(frameon=False)
    enregistrer(fig, "01_distribution_prix.png")


def graphe_par_etat(df):
    """Prix moyen de l'essence par État, trié (moyenne des villes, puis de l'État)."""
    par_ville = df.groupby(["state_name", "city_id"])["petrol"].mean()
    par_etat = par_ville.groupby("state_name").mean().sort_values()
    fig, ax = plt.subplots(figsize=(9, 10))
    ax.barh(par_etat.index, par_etat.values, color=COULEURS["petrol"], height=0.7)
    ax.set_xlim(par_etat.min() - 5, par_etat.max() + 3)
    for y, valeur in enumerate(par_etat.values):
        ax.text(valeur + 0.3, y, f"{valeur:.2f}", va="center", fontsize=8,
                color=TEXTE_SECONDAIRE)
    style_axes(ax, "Prix moyen de l'essence par État", "Prix moyen (₹ par litre)", "")
    ax.grid(axis="y", visible=False)
    enregistrer(fig, "02_prix_moyen_par_etat.png")


def graphe_essence_diesel(df):
    """Nuage de points diesel / essence : une ville = un point (prix moyens)."""
    par_ville = df.groupby("city_id")[["diesel", "petrol"]].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(par_ville["diesel"], par_ville["petrol"], s=18, alpha=0.7,
               color=COULEURS["petrol"], edgecolors="white", linewidths=0.5)
    correlation = par_ville["diesel"].corr(par_ville["petrol"])
    style_axes(ax, f"Essence vs diesel par ville (corrélation = {correlation:.2f})",
               "Prix moyen du diesel (₹ par litre)", "Prix moyen de l'essence (₹ par litre)")
    enregistrer(fig, "03_essence_vs_diesel.png")


def graphe_evolution(df):
    """Évolution des prix dans le temps, corrigée de l'effet de composition.

    Toutes les villes ne sont pas relevées tous les jours : une simple moyenne
    journalière monterait ou baisserait selon les villes présentes ce jour-là.
    On calcule donc, pour chaque relevé, l'écart au prix moyen de SA ville,
    puis on fait la moyenne de ces écarts par jour.
    """
    ecarts = df[COLONNES_PRIX] - df.groupby("city_id")[COLONNES_PRIX].transform("mean")
    ecarts["date"] = df["date"]
    par_jour = ecarts.groupby("date")[COLONNES_PRIX].mean()
    villes_par_jour = df.groupby("date")["city_id"].nunique()

    fig, (ax, ax_villes) = plt.subplots(
        2, 1, figsize=(10, 6.5), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    for col in COLONNES_PRIX:
        ax.plot(par_jour.index, par_jour[col], color=COULEURS[col], linewidth=2,
                label=NOMS[col])
    ax.axhline(0, color=TEXTE_SECONDAIRE, linewidth=0.8)
    style_axes(ax, "Évolution des prix : écart moyen au prix habituel de chaque ville",
               "", "Écart (₹ par litre)")
    ax.legend(frameon=False, loc="upper left")

    ax_villes.bar(villes_par_jour.index, villes_par_jour.values, color=GRILLE, width=0.8)
    style_axes(ax_villes, "Nombre de villes relevées par jour", "Date", "Villes")
    ax_villes.title.set_fontsize(10)
    fig.autofmt_xdate()
    enregistrer(fig, "04_evolution_prix.png")


def main():
    creer_dossiers()
    df = pd.read_csv(FICHIER_PROPRE, parse_dates=["date"])
    print(f"Données chargées : {len(df)} lignes")
    print("Graphes générés :")
    graphe_distribution(df)
    graphe_par_etat(df)
    graphe_essence_diesel(df)
    graphe_evolution(df)


if __name__ == "__main__":
    main()
