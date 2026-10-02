# Explication du script de nettoyage : `src/01_nettoyage.py`

## Objectif

Le script prend le fichier brut **Fuel-Price** (format ARFF, prix des carburants en Inde de mai à juillet 2024) et produit un fichier **CSV propre**, prêt pour l'analyse :

- les colonnes ont le bon type (nombres pour les prix, vraies dates pour `date`) ;
- il ne reste aucune valeur manquante ni aucun doublon ;
- les prix ont été contrôlés et les incohérences sont signalées ;
- chaque ville a un identifiant unique, même quand deux villes portent le même nom.

## Utilisation

```bash
python src/01_nettoyage.py      # depuis la racine du projet
```

Le script lit `data/raw/fuel_price_india.arff` et écrit `data/processed/fuel_price_clean.csv`. Les chemins sont définis dans `src/config.py`. Pendant l'exécution, le script affiche un **rapport** qui détaille ce qu'il fait à chaque étape.

## Résultat sur le dataset fourni

| | Avant | Après |
|---|---|---|
| Lignes | 41 406 | 41 398 |
| Colonnes | 6 | 8 |
| Valeurs manquantes | 24 (8 lignes × 3 prix) | 0 |
| Doublons | 0 | 0 |
| Villes uniques | 692 noms (ambigus) | 695 `city_id` |

---

## Paramètres (fichier `src/config.py`)

```python
FICHIER_BRUT   = DATA_RAW / "fuel_price_india.arff"
FICHIER_PROPRE = DATA_PROCESSED / "fuel_price_clean.csv"
COLONNES_TEXTE = ["city_name", "state_name"]
COLONNES_PRIX  = ["petrol", "diesel", "xpremium"]
FORMAT_DATE    = "%d-%m-%y"
PRIX_MIN, PRIX_MAX = 50.0, 200.0
```

Tous les réglages sont regroupés dans `src/config.py`, que tous les scripts du projet partagent. On peut donc les modifier sans toucher au reste du code :
- les chemins sont calculés à partir de l'emplacement du fichier, donc les scripts fonctionnent quel que soit le dossier depuis lequel on les lance ;
- `FORMAT_DATE` décrit le format des dates du fichier : `09-07-24` signifie jour-mois-année sur deux chiffres ;
- `PRIX_MIN` et `PRIX_MAX` sont les bornes de plausibilité utilisées à l'étape 6.

La petite fonction `afficher()` sert uniquement à aligner les lignes du rapport affiché à l'écran.

---

## Étape 1 : Lecture du fichier ARFF

**Le problème :** le fichier n'est pas un CSV classique. C'est un fichier **ARFF**, le format de Weka, qui a :
- un **en-tête** avec un commentaire (`%`), le nom de la relation (`@RELATION`) et la liste des colonnes (`@ATTRIBUTE nom type`) ;
- une section **`@DATA`**, suivie des données au format CSV.

**Ce que fait la fonction `lire_arff()` :**
1. Elle parcourt le fichier ligne par ligne et ignore les lignes vides et les commentaires (`%`).
2. Pour chaque ligne `@ATTRIBUTE`, elle récupère le **nom de la colonne** (2e mot de la ligne).
3. Quand elle rencontre `@DATA`, elle enregistre toutes les lignes suivantes comme des données.
4. Elle passe ces lignes à `pd.read_csv()` avec ces options :
   - `quotechar="'"` : les noms d'État qui contiennent des espaces sont entourés d'apostrophes (`'Andaman and Nicobar Islands'`). Cette option retire les apostrophes.
   - `dtype=str` : tout est lu en texte, pour que la conversion des types se fasse de façon contrôlée à l'étape 3.
   - `keep_default_na=False` : pandas ne doit rien deviner tout seul. Les valeurs manquantes sont traitées explicitement plus loin.

**Pourquoi lire les noms de colonnes dans l'en-tête ?** Le script ne dépend pas de noms écrits en dur. Il reste correct si l'ordre des colonnes change.

**Résultat :** 41 406 lignes × 6 colonnes.

---

## Étape 2 : Nettoyage des colonnes texte

```python
df[col] = df[col].str.strip()
df[col] = df[col].str.replace(r"\s+", " ", regex=True)
```

- `str.strip()` supprime les espaces au début et à la fin de chaque valeur.
- `str.replace(r"\s+", " ")` remplace plusieurs espaces consécutifs par un seul.

**Pourquoi ?** Pour l'ordinateur, `"Delhi"`, `" Delhi"` et `"Delhi "` sont trois valeurs différentes. Sans ce nettoyage, une même ville pourrait être comptée plusieurs fois. Sur ce dataset, l'étape ne change rien (692 villes et 32 États avant comme après), mais c'est une **mesure de sécurité** standard.

---

## Étape 3 : Conversion des types

### Prix → nombres
```python
df[col] = df[col].replace("?", pd.NA)
df[col] = pd.to_numeric(df[col], errors="coerce")
```
- Dans le format ARFF, **`?` signifie « valeur manquante »**. On le remplace par `pd.NA`, la valeur manquante de pandas.
- `pd.to_numeric()` transforme le texte `"82.42"` en nombre `82.42`. Avec `errors="coerce"`, une valeur non convertible devient manquante au lieu de faire planter le script.

**Résultat :** 8 valeurs manquantes dans chacune des trois colonnes de prix.

### Date → datetime
```python
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%y", errors="coerce")
```
- La date était stockée en texte (`"09-07-24"`). Elle devient une vraie date (`2024-07-09`).
- Préciser le format évite toute confusion entre jour et mois : `05-07-24` est bien le **5 juillet**, pas le 7 mai.
- Avec une vraie date, on peut trier chronologiquement, filtrer une période ou calculer des écarts en jours.

**Résultat :** 0 date invalide.

---

## Étape 4 : Suppression des doublons

```python
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["city_name", "state_name", "date"], keep="first")
```

Le script fait deux vérifications :
1. **Doublons exacts** : deux lignes identiques sur toutes les colonnes.
2. **Doublons de clé** : une même ville, dans le même État, à la même date. Il ne doit y avoir **qu'un seul prix par ville et par jour**. Si deux lignes existent, le script garde la première.

**Résultat :** 0 doublon. Les données sont déjà propres sur ce point, mais le contrôle protège contre une future version du fichier.

---

## Étape 5 : Traitement des valeurs manquantes

```python
masque_manquant = df[COLONNES_PRIX + ["date"]].isna().any(axis=1)
df = df[~masque_manquant]
```

- `isna().any(axis=1)` repère chaque ligne où **au moins une** valeur est manquante (prix ou date).
- `~` inverse ce masque, donc on garde les lignes **complètes**.

**Lignes concernées (8, soit 0,02 % du dataset) :**

| Ville | État | Lignes |
|---|---|---|
| Kamjong | Manipur | 3 |
| Narayanpur | Chhattisgarh | 5 |

**Pourquoi supprimer plutôt que remplacer (imputer) ?**
- Sur ces 8 lignes, les **trois prix** manquent en même temps : il n'y a aucune information exploitable.
- Elles représentent 0,02 % des données, donc les supprimer ne change pas les statistiques.
- Imputer reviendrait à **inventer** des prix. La suppression est le choix le plus prudent et le plus transparent.

---

## Étape 6 : Contrôle de plausibilité des prix

```python
hors_bornes = (df[col] < PRIX_MIN) | (df[col] > PRIX_MAX)
```

Le script supprime tout prix inférieur à 50 ₹ ou supérieur à 200 ₹ par litre. Ces bornes sont volontairement larges : en 2024, les prix indiens se situent autour de 80 à 115 ₹. Une valeur hors de cet intervalle serait donc forcément une erreur de saisie, par exemple `1012.5` au lieu de `101.25`, ou `0`.

**Résultat :** 0 ligne supprimée, toutes les valeurs sont plausibles (de 78,01 à 115,14 ₹).

---

## Étape 7 : Signalement des incohérences (sans suppression)

```python
df["flag_xpremium_incoherent"] = df["xpremium"] < df["petrol"]
```

**Règle métier :** l'essence premium (`xpremium`) devrait toujours coûter **plus cher** que l'essence ordinaire (`petrol`).

**Résultat :** 41 lignes ne respectent pas cette règle, toutes à **Chamoli (Uttarakhand)**. Par exemple, le 30/06/2024 : essence 99,50 ₹, premium 99,03 ₹.

**Pourquoi signaler sans supprimer ?** L'écart est faible et il est possible qu'il soit réel, par exemple si les deux prix n'ont pas été mis à jour le même jour. Rien ne prouve qu'il s'agit d'une erreur. Le script ajoute donc une colonne **`flag_xpremium_incoherent`** (`True` ou `False`), et l'utilisateur décide :

```python
df_sans_anomalies = df[~df["flag_xpremium_incoherent"]]
```

---

## Étape 8 : Création d'un identifiant unique de ville

```python
df["city_id"] = df["city_name"] + " - " + df["state_name"]
```

**Le problème :** trois noms de villes existent dans deux États différents.

| Nom | États |
|---|---|
| Bilaspur | Chhattisgarh / Himachal Pradesh |
| Hamirpur | Himachal Pradesh / Uttar Pradesh |
| Pratapgarh | Rajasthan / Uttar Pradesh |

Si on regroupe uniquement par `city_name`, les prix de deux villes différentes sont mélangés. Par exemple, « Bilaspur » compterait 130 jours de relevés sur une période de 69 jours.

**La solution :** la colonne `city_id` combine la ville et l'État (par exemple `Bilaspur - Chhattisgarh`). Elle identifie chaque ville sans ambiguïté.

**Résultat :** 695 villes uniques, au lieu de 692 noms.

---

## Étape 9 : Tri, réorganisation et export

```python
df = df.sort_values(["state_name", "city_name", "date"]).reset_index(drop=True)
creer_dossiers()   # crée data/processed/ s'il n'existe pas
df.to_csv(FICHIER_SORTIE, index=False, encoding="utf-8", date_format="%Y-%m-%d")
```

- **Tri** par État, puis par ville, puis par date : chaque ville forme une série chronologique lisible.
- `reset_index(drop=True)` renumérote les lignes de 0 à n−1 après les suppressions.
- **Ordre des colonnes** : l'identifiant, puis la localisation, la date, les prix et enfin le flag.
- **Export en CSV** : ce format standard est lisible par Excel, Python, R ou Weka. Les dates sont écrites au format international `AAAA-MM-JJ`, qui ne laisse aucun doute sur l'ordre du jour et du mois.

### Structure du fichier final `data/processed/fuel_price_clean.csv`

| Colonne | Type | Exemple |
|---|---|---|
| `city_id` | texte | `Nicobar - Andaman and Nicobar Islands` |
| `city_name` | texte | `Nicobar` |
| `state_name` | texte | `Andaman and Nicobar Islands` |
| `date` | date (AAAA-MM-JJ) | `2024-05-08` |
| `petrol` | décimal (₹/L) | `82.42` |
| `diesel` | décimal (₹/L) | `78.01` |
| `xpremium` | décimal (₹/L) | `85.42` |
| `flag_xpremium_incoherent` | booléen | `False` |

> Pour recharger le fichier avec les bons types en Python :
> `pd.read_csv("fuel_price_clean.csv", parse_dates=["date"])`

---

## Bilan affiché en fin de script

Le script se termine par un bilan qui permet de vérifier le travail :
- le nombre de lignes avant et après nettoyage (41 406 → 41 398) ;
- la période couverte (08/05/2024 → 15/07/2024) ;
- le nombre de valeurs manquantes restantes (0) ;
- les statistiques descriptives des trois prix (moyenne, écart-type, minimum, quartiles, maximum).

## Récapitulatif

| # | Étape | Action | Lignes supprimées |
|---|---|---|---|
| 1 | Lecture ARFF | Analyse de l'en-tête et des données | — |
| 2 | Colonnes texte | Suppression des espaces superflus | 0 |
| 3 | Types | `?` → manquant, prix → nombres, date → datetime | — |
| 4 | Doublons | Doublons exacts et doublons (ville, État, date) | 0 |
| 5 | Valeurs manquantes | Suppression des lignes incomplètes | **8** |
| 6 | Plausibilité | Prix hors [50 ; 200] ₹ | 0 |
| 7 | Incohérences | Flag `xpremium < petrol` (Chamoli) | 0 (41 lignes signalées) |
| 8 | Identifiant | Création de `city_id` | — |
| 9 | Export | Tri et écriture du CSV | — |
| | **Total** | | **8 lignes (0,02 %)** |
