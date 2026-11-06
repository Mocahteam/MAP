# MAP — Mining Algorithm Patterns

MAP est un algorithme de fouille de données qui tente de **reconstruire la structure algorithmique d'un programme (boucles, éléments optionnels/conditionnels) à partir de sa trace d'exécution**.

À partir d'une trace comme :

```
PYPYPYPYPYPYPYPYPYPYPYPUY
```

MAP cherche à produire un modèle compressé comme :

```
[PU*Y]
```

où `[...]` représente une séquence répétée (une boucle) et `X*` un évènement optionnel (typiquement le contenu d'un `if`).

---

## Sommaire

1. [Installation](#installation)
2. [Principe et hyperparamètres](#principe-et-hyperparamètres)
3. [Organisation du dépôt](#organisation-du-dépôt)
4. [Format d'un dataset](#format-dun-dataset)
5. [Lancer MAP sur une séquence donnée](#lancer-map-sur-une-séquence-donnée)
6. [Explorer les paramètres de tout un dataset](#explorer-les-paramètres-de-tout-un-dataset)
7. [Les notebooks Jupyter](#les-notebooks-jupyter)
8. [Workflow complet](#workflow-complet)
9. [Points d'attention](#points-dattention)

---

## Installation

Python **3.10 ou plus** est requis (le code utilise la syntaxe `X | None`, les génériques `list[...]` et l'opérateur `:=`).

```bash
git clone https://github.com/Mocahteam/MAP.git
cd MAP
pip install numpy matplotlib jupyter
```

Seul `numpy` est nécessaire pour l'algorithme et l'exploration des paramètres ; `matplotlib` et `jupyter` servent aux notebooks d'analyse et de visualisation.

---

## Principe et hyperparamètres

MAP fonctionne de manière itérative :

1. **PTKE** (`PTKE.py`) recherche les *K* meilleurs épisodes (motifs fréquents) de la trace courante (`PTKE.K = 10`).
2. Pour chaque épisode dont le support est supérieur à 1, MAP simule une compression : les occurrences proches de l'épisode sont fusionnées en une séquence `[...]`, et les évènements intercalés sont alignés et marqués optionnels (`*`).
3. Chaque nouvelle trace compressée (si elle contient moins d'appels que la précédente et n'a pas déjà été vue) est à son tour explorée.
4. L'algorithme retourne un **ensemble de compressions candidates** (`CompressionSet`), chacune accompagnée de trois compteurs : nombre d'options (`OptCount`), d'alignements (`AlignCount`) et de fusions (`MergeCount`).

Chaque exploration d'un épisode est limitée à `TIME_LIMIT = 5` secondes (défini dans `MAP.py`).

Trois hyperparamètres pilotent le comportement de l'algorithme :

| Paramètre | Abréviation | Variable dans le code | Plage explorée | Rôle |
|---|---|---|---|---|
| Gap ratio | `gr` | `PTKE.GAP_RATIO` | [0 ; 8] | Détermine la distance maximale tolérée entre deux occurrences consécutives d'un épisode pendant la phase de fusion. Une valeur faible favorise les répétitions compactes et contiguës, tandis qu'une valeur plus élevée permet de regrouper dans un même motif des occurrences séparées par des intervalles plus longs. |
| Weight support | `ws` | `NonOverlappedEpisode. WEIGHT_SUPPORT` | [0 ; 1] | Détermine l'importance de la fréquence des épisodes. Lorsque WS tend vers 1, la sélection des épisodes est principalement guidée par le soutien, ce qui favorise les motifs très fréquents. À l'inverse, des valeurs plus faibles augmentent l'influence des critères structurels et peuvent favoriser des épisodes moins fréquents mais plus cohérents. |
| Proximity balancing | `pb` | `NonOverlappedEpisode. PROXIMITY_BALANCING` | [0 ; 1] | Détermine la manière dont la proximité est interprétée tout au long de l'algorithme. Lors de l'évaluation des épisodes, il équilibre la contribution de la proximité interne (occurrences compactes comportant peu d'événements intercalés) et de la proximité externe (occurrences situées à proximité les unes des autres dans la séquence). Au cours de la phase de fusion, PB influence également la distance admissible entre des occurrences d'épisodes consécutives par le biais du seuil GR |
---

## Organisation du dépôt

| Fichier / dossier | Rôle |
|---|---|
| `MAP.py` | Cœur de l'algorithme : fonction `MAP(event_list)`, classes `CompressionStats` et `CompressionSet`. |
| `runMAP.py` | Lance l'algorithme MAP sur une séquence donnée. |
| `PTKE.py` | Recherche des top-K épisodes fréquents dans une séquence. |
| `Episode.py` | Représentation des épisodes et calcul de leur score (support, proximité). |
| `Event.py` | Représentation des évènements (`Call`, `Sequence`, `Root`…), linéarisation et fusion/alignement de séquences. |
| `exploreParameters.py` | Script d'exploration de l'espace (`gr`, `ws`, `pb`) sur un fichier ou un dataset entier. |
| `MAP_Visualization.ipynb` | Visualisation 3D des résultats de l'exploration des paramètres. |
| `MAP_Analysis.ipynb` | Recherche des poids de la fonction de score qui permettent de choisir la bonne compression parmi les candidates. |
| `dataset1`, `dataset2`, `dataset3`, `datasetXP`, `datasetXP_alter`, `datasetXP_v3` | Jeux de traces et de solutions attendues. |
| `exportResults_MAP_*_{hard,soft}.txt` | Résultats exportés par `MAP_Analysis.ipynb` (nombre de succès par scénario). |
| `convertPP2Tokens.py` | Utilitaire de conversion des traces Prog&Play (appels `PP_*`) en lettres. |
| `CheckResults.py` | Ancien script de lecture des résultats (format JSON antérieur, non compatible avec les sorties actuelles). |
| `deroulementAlgo.txt` | Notes de travail sur le déroulement d'un alignement. |

---

## Format d'un dataset

Un dataset est un dossier qui doit respecter **exactement** cette structure :

```
monDataset/
└── example/
    ├── 1_1_.log              ← trace à compresser
    ├── 1_2_.log
    ├── ...
    └── solutions/
        ├── 1_1_.log          ← solution attendue (même nom de fichier)
        ├── 1_2_.log
        └── ...
```

- **Trace** (`example/<nom>.log`) : seule la **première ligne** est lue. Chaque caractère est un évènement (un appel de fonction), par exemple `PYPYPYPYPYPYPYPYPYPYPYPUY`.
- **Solution** (`example/solutions/<nom>.log`) : la compression attendue, avec la syntaxe `[ ]` pour une boucle et `*` pour un évènement optionnel, par exemple `[PU*Y]`. Les notebooks acceptent plusieurs solutions valides séparées par une tabulation.
- **Nommage** : pour les notebooks, les fichiers doivent suivre la convention `<numéroScénario>_<numéroVariante>_.log` (comme dans `datasetXP`). Le numéro de scénario sert à regrouper les résultats.

À l'issue de l'exploration, deux dossiers sont créés automatiquement à la racine du dataset :

```
monDataset/
├── example/...
├── files_npy/            ← matrices 11×11×11 des résultats (une par trace)
└── solutionsExplored/    ← compressions obtenues pour chaque triplet (gr, ws, pb), en JSON
```

---

## Lancer MAP sur une séquence donnée

Exemple d'exécution :

```bash
python runMAP.py PYPYPYPYPYPYPYPYPYPYPYPUY 1.6 0.5 0.5 "[PU*Y]"
```

Sortie :

```
[PU*Y] 1 24 12
Solution trouvée
```

La compression `[PU*Y]` a été obtenue avec 1 option, 24 alignements et 12 fusions.

Pour un usage en Python (ou dans un notebook), le principe est identique : on fixe les trois variables de classe, puis on appelle `MAP(...)` sur une liste de `Call`.

---

## Explorer les paramètres de tout un dataset

`exploreParameters.py` lance MAP sur chaque trace d'un dataset pour un ensemble de triplets (`gr`, `ws`, `pb`), puis compare les compressions obtenues avec la solution attendue.

### Syntaxe

```
python exploreParameters.py (-f FICHIER -d DOSSIER | -s DATASET) [-m {dichotomous,exhaustive}]
```

| Option | Description |
|---|---|
| `-f`, `--file` | Nom d'une trace (sans `.log`), ou `all` pour toutes les traces de `DOSSIER/example/`. |
| `-d`, `--directory` | Dossier du dataset (obligatoire avec `-f`). |
| `-s`, `--dataset` | Dataset prédéfini dans le script (`dataset1`, `dataset2`, `dataset3`, `datasetXP`, `datasetXPv2`), avec une liste de fichiers codée en dur. Exclusif avec `-f`. |
| `-m`, `--mode` | `dichotomous` (par défaut) ou `exhaustive`. |

### Exemples

```bash
# Explorer TOUTES les traces d'un dataset en mode exhaustif
python exploreParameters.py -f all -d datasetXP_v3 -m exhaustive

# Explorer toutes les traces en mode dichotomique (plus rapide)
python exploreParameters.py -f all -d datasetXP_v3 -m dichotomous

# Explorer une seule trace
python exploreParameters.py -f 5_5_ -d datasetXP_v3 -m exhaustive
```

### Les deux modes d'exploration

L'espace des paramètres est discrétisé en une grille de **11 × 11 × 11 = 1 331 points** (pas de 0,8 pour `gr`, 0,1 pour `ws` et `pb`).

- **`exhaustive`** : MAP est exécuté sur les 1 331 points. C'est le mode le plus long, mais la cartographie est complète. **C'est le mode attendu par les notebooks d'analyse.**
- **`dichotomous`** : l'espace est découpé en 8 cubes ; si les 8 sommets d'un cube donnent le même résultat, le cube est considéré comme homogène et n'est pas exploré davantage. Sinon, il est subdivisé autour des zones de changement. Ce mode évalue typiquement quelques centaines de points au lieu de 1 331 (par exemple 276 pour `datasetXP/12_5_`), mais laisse des « trous » non explorés dans la grille.

### Fichiers produits

Pour chaque trace `<nom>`, le script produit :

**`files_npy/<mode>_<nom>.npy`** : une matrice NumPy `11×11×11` indexée par `[i_gr][j_ws][k_pb]`, dont chaque case vaut :

| Valeur | Signification |
|---|---|
| `1` | La solution attendue fait partie des compressions trouvées. |
| `2` | Des compressions ont été trouvées, mais pas la solution attendue. |
| `-1` | Temps dépassé (« OverTime »). |
| `0` | Point non exploré (mode dichotomique uniquement). |

**`solutionsExplored/<mode>_<nom>.txt`** : un JSON qui associe à chaque triplet la liste des compressions candidates et leurs statistiques :

```json
{
    "4.00gr_0.50ws_0.50pb": [
        {
            "Compression": "[PU*Y]",
            "OptCount": "1",
            "AlignCount": "24",
            "MergeCount": "12"
        }
    ],
    ...
}
```

---

## Les notebooks Jupyter

Les deux notebooks exploitent les fichiers générés par `exploreParameters.py`. Ils se lancent avec :

```bash
jupyter notebook
```

Dans les deux notebooks, **il faut adapter les variables `mainDir` et `version`** en tête des cellules de travail. Elles pointent actuellement vers `./datasetXP_v3`, un dataset absent du dépôt.

```python
mainDir = "./datasetXP"     # dossier du dataset exploré
version = "exhaustive"      # ou "dichotomous", selon le mode utilisé
```

### `MAP_Visualization.ipynb` — Où se trouvent les bons paramètres de MAP ?

Ce notebook répond à la question : **pour quels triplets (`gr`, `ws`, `pb`) MAP parvient-il à reconstruire la solution attendue ?** Il lit les matrices `files_npy/*.npy`.

- **`dessin3D`** affiche, pour chaque trace, un nuage de points 3D dans l'espace (`gr`, `ws`, `pb`). Les points verts sont les triplets qui ont permis de retrouver la solution. Les points rouges (solution non trouvée) et noirs (temps dépassé) sont désactivés par défaut et peuvent être réactivés en décommentant les lignes correspondantes. Chaque figure est sauvegardée en PNG dans `datasetXP_v3_img/` : **créez ce dossier ou modifiez le chemin** de `plt.savefig` avant l'exécution.
- **`dessinPerf`** agrège tout le dataset : pour chaque triplet, il compte le nombre de traces pour lesquelles la solution a été trouvée, et n'affiche que les triplets qui réussissent sur au moins 83 % des traces (seuil codé en dur). La taille d'un point est proportionnelle à sa performance, et les meilleurs triplets sont aussi listés en texte. Cette fonction lit les fichiers `exhaustive_*.npy` uniquement.

C'est ce notebook qui permet de **choisir un bon réglage par défaut de `gr`, `ws` et `pb`**.

### `MAP_Analysis.ipynb` — Comment choisir la bonne compression parmi les candidates ?

Pour un même triplet, et a fortiori sur l'ensemble de l'espace exploré, MAP produit **plusieurs compressions candidates**. Ce notebook répond à la question : **quelle fonction de score permet de désigner automatiquement la bonne ?** Il lit les fichiers `solutionsExplored/*.txt`.

1. **`computeLength`** calcule la longueur effective d'une compression (en tenant compte des options et des crochets).
2. **`computeScore`** calcule un score qui combine quatre critères, chacun pondéré par un poids et un sens (favoriser une valeur faible ou élevée) : la longueur de la compression, son nombre d'options, son nombre d'alignements et son nombre de fusions. Les hyperparamètres de score forment un tuple `(lWeight, lWay, oWeight, oWay, aWeight, aWay, mWeight, mWay)`.
3. **`computePerf`** évalue un jeu de poids sur tout le dataset et retourne, pour chaque scénario, le nombre de traces correctement résolues, selon deux critères :
   - **hard** (`mostRecurrent=True`) : parmi les compressions de meilleur score, la plus récurrente doit être la solution attendue ;
   - **soft** (`mostRecurrent=False`) : il suffit que la solution attendue figure parmi les compressions explorées.
4. Une **recherche en grille** teste toutes les combinaisons de poids dans `{0 ; 0,25 ; 0,5 ; 0,75 ; 1}` et retient le ou les jeux qui maximisent le nombre de succès.
5. Le meilleur jeu est enfin appliqué et les résultats sont **exportés** dans `exportResults_MAP_<suffixe>_hard.txt` et `..._soft.txt` (une liste du nombre de succès par scénario).

Une cellule permet aussi de tester un jeu de poids sur une seule trace, pour le débogage. Le meilleur jeu trouvé lors des expérimentations est `(1, True, 0.25, True, 0, False, 0, False)` : favoriser les compressions courtes, avec un léger bonus pour celles qui comportent peu d'options.

> Ce notebook déduit le nombre de scénarios du préfixe numérique des noms de fichiers (`<scénario>_<variante>_.log`). Il fonctionne donc avec `datasetXP` et `datasetXP_alter`, mais pas avec `dataset1`, `dataset2` ou `dataset3`, dont le nommage est différent.

---

## Workflow complet

```bash
# 1. Explorer exhaustivement l'espace des paramètres sur un dataset
python exploreParameters.py -f all -d datasetXP_v3 -m exhaustive

# 2. Lancer Jupyter
jupyter notebook
```

3. Dans **`MAP_Visualization.ipynb`**, mettre `mainDir = "./datasetXP_v3"`, puis visualiser les zones de réussite et identifier les meilleurs triplets (`gr`, `ws`, `pb`).
4. Dans **`MAP_Analysis.ipynb`**, mettre `mainDir = "./datasetXP_v3"` et `version = "exhaustive"`, puis rechercher les meilleurs poids de la fonction de score et exporter les résultats hard/soft.
5. Utiliser le réglage retenu pour lancer MAP sur de nouvelles traces (voir [Lancer MAP sur une séquence donnée](#lancer-map-sur-une-séquence-donnée)).

---

## Points d'attention

- **Temps de calcul** : le mode exhaustif exécute MAP 1 331 fois par trace. Sur `datasetXP_v3` (100 traces), prévoir un temps conséquent. Le mode dichotomique est utile pour un premier aperçu, mais les notebooks reposent principalement sur des résultats exhaustifs.
- **`-f all` et fichiers sans solution** : toutes les traces de `example/` doivent avoir leur solution dans `example/solutions/`.
- **Solutions multiples** : les notebooks acceptent plusieurs solutions séparées par une tabulation, mais `exploreParameters.py` compare la ligne entière, ce qui revient à n'accepter qu'une seule solution.
- **Affichage console** : MAP affiche sa progression à la colonne 80 au moyen de séquences d'échappement ANSI. Dans un terminal qui ne les interprète pas, la sortie peut paraître bruitée.

---

## Licence

GPL-3.0 — voir le fichier [LICENSE](LICENSE).
