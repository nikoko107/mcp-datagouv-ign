# 💡 Exemples d'utilisation avancés

## 🗺️ Cartographie et géolocalisation

### Exemple 1 : Afficher une carte d'une ville
```
Génère une carte IGN de Strasbourg avec les orthophotos
```
Claude utilisera :
1. `geocode_address` pour trouver les coordonnées de Strasbourg
2. `search_wms_layers` pour trouver la couche orthophotos
3. `get_wms_map_url` pour générer l'URL de la carte

### Exemple 2 : Trouver l'adresse la plus proche
```
Quelle est l'adresse correspondant aux coordonnées 48.8566, 2.3522 ?
```
Claude utilisera `reverse_geocode`.

### Exemple 3 : Autocomplétion d'adresse
```
Aide-moi à compléter cette adresse : "10 rue de Riv"
```
Claude utilisera `search_addresses`.

## 📊 Recherche de données publiques

### Exemple 4 : Trouver des datasets thématiques
```
Trouve tous les jeux de données sur la qualité de l'air publiés par le ministère de l'environnement
```
Claude utilisera `search_datasets` avec des filtres.

### Exemple 5 : Analyser un dataset
```
Montre-moi les détails du dataset sur les accidents de la route et liste ses fichiers téléchargeables
```
Claude combinera `get_dataset` et `get_dataset_resources`.

### Exemple 6 : Explorer une organisation
```
Quels sont les principaux datasets publiés par l'INSEE ?
```
Claude utilisera `search_organizations` puis `get_organization`.

## 🏛️ Analyse territoriale

### Exemple 7 : Informations complètes sur une commune
```
Donne-moi toutes les infos sur la commune de Rennes : population, département, région, codes postaux
```
Claude utilisera `search_communes` puis `get_commune_info`.

### Exemple 8 : Comparer plusieurs communes
```
Compare la population des 10 plus grandes villes de France
```
Claude utilisera `search_communes` avec plusieurs requêtes.

### Exemple 9 : Analyser un département
```
Liste toutes les communes du Finistère et leur population
```
Claude utilisera `get_departement_communes`.

## 🎨 Cas d'usage métier

### Exemple 10 : Urbanisme
```
Pour la ville de Lille :
1. Trouve les données cadastrales
2. Affiche une carte avec les limites administratives
3. Récupère les données démographiques
```
Claude combinera :
- `geocode_address`
- `search_wfs_features` (cadastre)
- `get_wms_map_url`
- `get_commune_info`

### Exemple 11 : Transport et logistique
```
Pour un trajet Paris → Lyon :
1. Géocode les deux villes
2. Trouve les données sur les infrastructures de transport
3. Affiche une carte du réseau routier entre les deux villes
```
Claude utilisera :
- `geocode_address` (×2)
- `search_datasets` (transport)
- `search_wms_layers` (réseau routier)
- `get_wms_map_url`

### Exemple 12 : Journalisme de données
```
Je fais un article sur la pollution en Île-de-France. Aide-moi à :
1. Trouver les datasets pertinents
2. Lister les communes de la région
3. Trouver les stations de mesure de la qualité de l'air
```
Claude combinera :
- `search_datasets`
- `search_regions` + `get_region_info`
- `search_wfs_features` ou datasets

### Exemple 13 : Application citoyenne
```
Je développe une app pour aider les citoyens à trouver les services publics. Pour une adresse donnée :
1. Géocode l'adresse
2. Trouve la commune correspondante
3. Récupère les infos de la mairie
4. Affiche une carte avec les bâtiments publics à proximité
```
Claude enchaînera :
- `geocode_address`
- `get_commune_info`
- `get_wfs_features` (bâtiments)
- `get_wms_map_url`

## 🔬 Analyses avancées

### Exemple 14 : Analyse multi-sources
```
Analyse comparative : trouve les données sur les énergies renouvelables pour la région Bretagne, affiche une carte des installations éoliennes, et donne-moi les statistiques par département
```
Claude combinera :
- `search_datasets` (énergies renouvelables)
- `search_regions` (Bretagne)
- `search_wfs_features` ou `get_wfs_features` (installations)
- `get_region_info`
- Multiples `search_departements`

### Exemple 15 : Visualisation cartographique avancée
```
Crée une visualisation multi-couches pour Toulouse :
1. Fond de carte : orthophotos
2. Superposition : limites administratives
3. Points d'intérêt : bâtiments remarquables
```
Claude utilisera plusieurs appels `get_wms_map_url` avec différentes couches.

## 📍 Géocodage avancé

### Exemple 16 : Validation d'adresses en masse
```
Voici une liste d'adresses. Pour chacune, vérifie qu'elle existe et donne-moi les coordonnées GPS :
- 10 rue de Rivoli, Paris
- 1 place Bellecour, Lyon
- 5 cours Mirabeau, Aix-en-Provence
```
Claude fera plusieurs appels à `geocode_address`.

### Exemple 17 : Calcul de distance
```
Quelle est la distance à vol d'oiseau entre Marseille et Nice ?
```
Claude géocodera les deux villes et calculera la distance.

## 🌍 Données vectorielles WFS

### Exemple 18 : Récupérer des limites administratives
```
Récupère les limites géographiques de toutes les communes de Haute-Garonne en GeoJSON
```
Claude utilisera `get_wfs_features` avec le bon typename et bbox.

### Exemple 19 : Analyse du cadastre
```
Récupère les parcelles cadastrales autour de ces coordonnées : 48.8566, 2.3522 (rayon 500m)
```
Claude utilisera `get_wfs_features` avec une bbox calculée.

## 🎯 Combinaisons puissantes

### Exemple 20 : Pipeline complet
```
Workflow complet : 
1. Trouve les datasets sur les écoles en Île-de-France
2. Récupère les coordonnées de toutes les communes de la région
3. Pour chaque commune, affiche une carte avec les établissements scolaires
4. Compile les statistiques par département
```

C'est un exemple d'utilisation avancée qui nécessite :
- `search_datasets`
- `get_region_info`
- Multiples `geocode_address` ou `get_commune_info`
- Multiples `get_wms_map_url`
- Analyse et agrégation des données

---

## 💡 Conseils pour de meilleurs résultats

1. **Soyez précis** : Plus votre demande est claire, meilleur sera le résultat
2. **Décomposez** : Pour des tâches complexes, divisez en sous-questions
3. **Explorez** : Utilisez `list_*` et `search_*` pour découvrir ce qui est disponible
4. **Combinez** : Les outils sont conçus pour être utilisés ensemble
5. **Itérez** : Raffinez progressivement votre recherche

## 🚀 Essayez maintenant !

Copiez-collez n'importe lequel de ces exemples dans Claude et observez comment il utilise automatiquement les bons outils pour répondre à votre demande.
