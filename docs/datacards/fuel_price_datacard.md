# Datacard : Fuel Price – Prix des carburants en Inde (2024)

## 1. Résumé

| Élément | Valeur |
|---|---|
| **Nom** | Fuel-Price (*Fuel Datasets in India States*) |
| **Description** | Prix quotidiens à la pompe de l'essence, du diesel et de l'essence premium dans les villes indiennes |
| **Format** | ARFF (Attribute-Relation File Format, utilisé par Weka), texte, séparateur virgule |
| **Taille** | 41 406 lignes × 6 colonnes (~2 Mo) |
| **Période couverte** | du 08/05/2024 au 15/07/2024 (69 jours) |
| **Couverture géographique** | 695 villes (692 noms distincts), 32 États et territoires |
| **Granularité** | 1 ligne = 1 ville × 1 jour |
| **Source d'origine** | *Non précisée dans le fichier (à compléter)* |
| **Licence** | *Non précisée (à compléter)* |
| **Auteur de la datacard** | *(à compléter)* |

---

## 2. Motivation et usages

### Pourquoi ce dataset ?
Il permet d'observer les écarts de prix des carburants entre villes et États indiens. En Inde, le prix final dépend fortement de la **TVA fixée par chaque État** et des **coûts de transport** jusqu'aux zones éloignées.

### Usages possibles
- Comparer les prix entre les États et entre les villes
- Visualiser les données (cartes, classements, boxplots par État)
- Étudier l'écart entre les prix de l'essence, du diesel et de l'essence premium
- S'exercer au nettoyage de données, à l'analyse exploratoire et à la régression ou au clustering dans Weka ou Python

### Usages déconseillés
- **Analyse de tendance à long terme ou prévision** : la période ne dure qu'environ 2 mois et les prix y sont très stables.
- **Conclusions au niveau national** sans pondération : le nombre de villes par État est très inégal.
- **Analyses sur les États absents** (voir section 6).

---

## 3. Structure des données

| Colonne | Type ARFF | Type réel | Description | Exemple |
|---|---|---|---|---|
| `city_name` | STRING | Catégoriel | Nom de la ville ou du district | `Nicobar` |
| `state_name` | STRING | Catégoriel | État ou territoire de l'Union | `Andaman and Nicobar Islands` |
| `date` | STRING | Date (`JJ-MM-AA`) | Jour du relevé | `09-07-24` (9 juillet 2024) |
| `petrol` | REAL | Numérique continu | Prix de l'essence ordinaire (probablement en ₹/litre) | `82.42` |
| `diesel` | REAL | Numérique continu | Prix du diesel (probablement en ₹/litre) | `78.01` |
| `xpremium` | REAL | Numérique continu | Prix de l'essence premium, probablement la marque *XP95* d'Indian Oil (₹/litre) | `85.42` |

> **Remarque :** la colonne `date` est déclarée en `STRING` et non en `DATE`. Il faut la convertir avant toute analyse temporelle, par exemple avec `pd.to_datetime(df.date, format="%d-%m-%y")`.

**Clé unique :** (`city_name`, `state_name`, `date`). Le fichier ne contient aucun doublon sur cette clé.

---

## 4. Statistiques descriptives

### Variables de prix (₹/litre, hors valeurs manquantes)

| Statistique | petrol | diesel | xpremium |
|---|---|---|---|
| Nombre de valeurs | 41 398 | 41 398 | 41 398 |
| Moyenne | 101,04 | 90,82 | 104,10 |
| Écart-type | 5,25 | 3,93 | 5,26 |
| Minimum | 82,42 | 78,01 | 85,42 |
| 1er quartile | 96,04 | 88,14 | 99,04 |
| Médiane | 101,17 | 91,41 | 104,26 |
| 3e quartile | 105,98 | 93,65 | 108,95 |
| Maximum | 112,13 | 99,60 | 115,14 |

### Répartition par État (prix moyens)

| État / Territoire | Lignes | Villes | Essence moy. | Diesel moy. |
|---|---|---|---|---|
| Andaman and Nicobar Islands | 204 | 3 | 82,42 | 78,01 |
| Daman and Diu | 134 | 2 | 92,86 | 88,36 |
| Arunachal Pradesh | 1 518 | 22 | 93,67 | 82,92 |
| Pondicherry | 252 | 4 | 93,78 | 83,85 |
| Delhi | 638 | 11 | 94,72 | 87,62 |
| Uttarakhand | 715 | 13 | 94,85 | 89,58 |
| Mizoram | 472 | 8 | 95,36 | 81,79 |
| Uttar Pradesh | 3 525 | 75 | 95,45 | 88,60 |
| Himachal Pradesh | 792 | 12 | 95,47 | 87,57 |
| Gujarat | 1 980 | 33 | 95,53 | 91,21 |
| Haryana | 1 320 | 22 | 95,59 | 88,42 |
| Meghalaya | 496 | 8 | 96,00 | 86,88 |
| Goa | 136 | 2 | 96,32 | 88,58 |
| Punjab | 1 276 | 22 | 96,84 | 87,12 |
| Tripura | 520 | 8 | 97,49 | 86,51 |
| Assam | 2 176 | 32 | 97,91 | 90,15 |
| Jammu and Kashmir | 1 160 | 20 | 98,92 | 84,18 |
| Jharkhand | 1 495 | 23 | 99,09 | 93,83 |
| Manipur | 993 | 15 | 99,84 | 85,85 |
| Chhattisgarh | 1 733 | 27 | 102,20 | 95,12 |
| Tamil Nadu | 2 211 | 33 | 102,28 | 93,84 |
| Karnataka | 1 798 | 29 | 102,35 | 88,32 |
| Ladakh | 136 | 2 | 102,52 | 87,66 |
| Odisha | 1 770 | 30 | 103,22 | 94,73 |
| West Bengal | 1 541 | 23 | 105,22 | 91,93 |
| Maharashtra | 2 176 | 34 | 105,54 | 92,12 |
| Rajasthan | 2 079 | 33 | 106,03 | 91,39 |
| Bihar | 1 482 | 38 | 106,61 | 93,37 |
| Kerala | 826 | 14 | 106,91 | 95,82 |
| Madhya Pradesh | 2 856 | 51 | 108,10 | 93,34 |
| Telangana | 2 112 | 33 | 108,58 | 96,74 |
| Andhra Pradesh | 884 | 13 | 110,16 | 97,92 |

**Lecture :** les îles Andaman-et-Nicobar affichent les prix les plus bas (82,42 ₹ l'essence) et l'Andhra Pradesh les plus élevés (110,16 ₹ en moyenne), soit environ 28 ₹ d'écart par litre.

---

## 5. Qualité des données

| Point | Détail |
|---|---|
| **Valeurs manquantes** | 8 lignes (0,02 %) ont `?` sur les **trois** colonnes de prix : Narayanpur (Chhattisgarh) 5 dates, Kamjong (Manipur) 3 dates. |
| **Doublons** | Aucun |
| **Séries incomplètes** | Chaque ville compte entre 39 et 69 jours de relevés (médiane : 62). Toutes les villes n'ont donc **pas** une série complète sur les 69 jours (par exemple, plusieurs districts du Bihar n'en ont que 39). |
| **Noms de villes ambigus** | 3 noms existent dans deux États : *Bilaspur* (Chhattisgarh / Himachal Pradesh), *Hamirpur* (Himachal Pradesh / Uttar Pradesh), *Pratapgarh* (Rajasthan / Uttar Pradesh). Il faut toujours identifier une ville par le couple **ville + État**. |
| **Faible variabilité temporelle** | Le prix de l'essence reste constant sur toute la période dans 513 villes sur 695 (74 %). |
| **Incohérence possible** | À Chamoli (Uttarakhand), le prix `xpremium` est **inférieur** au prix `petrol` sur 41 lignes, alors que l'essence premium est normalement plus chère. Il peut s'agir d'une erreur de collecte. |
| **Type de la date** | Stockée en texte, au format court `JJ-MM-AA` |

---

## 6. Biais et limites

- **Couverture géographique incomplète** : plusieurs territoires sont absents, notamment le **Nagaland**, le **Sikkim**, **Chandigarh**, **Dadra-et-Nagar-Haveli** et **Lakshadweep**.
- **Déséquilibre entre États** : l'Uttar Pradesh représente 8,5 % des lignes (75 villes), contre 2 villes pour Goa, Ladakh ou Daman-et-Diu. Une moyenne nationale calculée ligne par ligne surpondère donc les grands États.
- **Période courte** : environ 2 mois (mai à juillet 2024). Le dataset ne capte ni la saisonnalité ni les grands chocs de prix.
- **Source et méthode de collecte inconnues** : le fichier ne dit pas d'où viennent les prix (compagnies pétrolières, site agrégateur…), ni l'heure du relevé ou le distributeur concerné.
- **Unité implicite** : la roupie par litre est déduite des ordres de grandeur, mais le fichier ne l'indique pas.

---

## 7. Prétraitements recommandés

1. Convertir `date` en type date.
2. Remplacer `?` par une vraie valeur manquante (NaN), puis supprimer ou imputer les 8 lignes concernées.
3. Créer un identifiant unique de ville : `city_name + " - " + state_name`.
4. Vérifier ou corriger les lignes de Chamoli où `xpremium < petrol`.
5. Pour les comparaisons entre États, calculer d'abord une moyenne **par ville**, puis par État.

Exemple de chargement en Python :

```python
import pandas as pd, io

texte = open("data/raw/fuel_price_india.arff", encoding="utf-8").read().split("@DATA")[1]
df = pd.read_csv(io.StringIO(texte), header=None, quotechar="'", na_values="?",
                 names=["city_name", "state_name", "date", "petrol", "diesel", "xpremium"])
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%y")
```

---

## 8. Informations complémentaires

| Élément | Valeur |
|---|---|
| Version | 1.0 |
| Date de rédaction de la datacard | 01/10/2026 |
| Maintenance / mises à jour | *Non prévue (à compléter)* |
| Contact | *(à compléter)* |
| Citation | *(à compléter si la source d'origine est connue)* |
