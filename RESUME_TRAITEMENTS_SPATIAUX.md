# 🗺️ Résumé : Outils de Traitement Spatial GeoPandas

## ✅ Implémentation complète

Vous avez ajouté **8 nouveaux outils de traitement spatial** basés sur GeoPandas au serveur MCP.

---

## 📦 Nouveaux outils (8)

### 1. **reproject_geodata**
Reprojette des données géographiques vers un autre système de coordonnées

**Paramètres :**
- `data`: Données géographiques (string ou base64)
- `input_format`: geojson, kml, gpkg, shapefile
- `target_crs`: CRS cible (ex: "EPSG:3857")
- `source_crs`: CRS source (optionnel)
- `output_format`: Format de sortie (optionnel)

**Exemple :**
```
"Reprojette ce GeoJSON de EPSG:4326 vers EPSG:3857"
```

---

### 2. **buffer_geodata**
Calcule un tampon (buffer) autour des géométries

**Paramètres :**
- `data`: Données géographiques
- `input_format`: Format d'entrée
- `distance`: Distance du buffer (en unités du CRS)
- `buffer_crs`: CRS pour le calcul (métrique recommandé)
- `output_crs`: CRS de sortie (optionnel)
- `cap_style`: round, flat, square (optionnel)
- `join_style`: round, mitre, bevel (optionnel)
- `resolution`: Nombre de segments (défaut: 16)
- `single_sided`: Buffer unilatéral (optionnel)

**Exemple :**
```
"Crée un buffer de 100 mètres autour de ces points en EPSG:3857"
```

---

### 3. **intersect_geodata**
Calcule l'intersection de deux jeux de données géographiques

**Paramètres :**
- `data_a`, `data_b`: Deux jeux de données
- `input_format_a`, `input_format_b`: Formats d'entrée
- `source_crs_a`, `source_crs_b`: CRS sources (optionnels)
- `target_crs`: CRS pour le calcul (optionnel)
- `output_format`: Format de sortie (optionnel)

**Exemple :**
```
"Trouve l'intersection entre ces parcelles cadastrales et cette zone inondable"
```

---

### 4. **clip_geodata**
Découpe un jeu de données avec une zone de découpe (clip)

**Paramètres :**
- `data`: Données à découper
- `input_format`: Format d'entrée
- `clip_data`: Données de découpe
- `clip_format`: Format de la zone de découpe
- `source_crs`, `clip_source_crs`: CRS sources (optionnels)
- `target_crs`: CRS pour le calcul (optionnel)
- `output_format`: Format de sortie (optionnel)

**Exemple :**
```
"Découpe ces bâtiments avec les limites de cette commune"
```

---

### 5. **convert_geodata_format**
Convertit des données entre formats (GeoJSON, KML, GeoPackage, Shapefile)

**Paramètres :**
- `data`: Données géographiques
- `input_format`: Format d'entrée
- `output_format`: Format de sortie
- `source_crs`: CRS source (optionnel)

**Exemple :**
```
"Convertis ce GeoJSON en Shapefile"
```

---

### 6. **get_geodata_bbox**
Calcule la bounding box (enveloppe minimale) d'un jeu de données

**Paramètres :**
- `data`: Données géographiques
- `input_format`: Format d'entrée
- `source_crs`: CRS source (optionnel)
- `target_crs`: CRS pour la bbox (optionnel)

**Résultat :**
```json
{
  "format": "bbox",
  "crs": "EPSG:4326",
  "bounds": {
    "minx": 2.3,
    "miny": 48.8,
    "maxx": 2.4,
    "maxy": 48.9
  }
}
```

**Exemple :**
```
"Donne-moi la bounding box de ces données"
```

---

### 7. **dissolve_geodata**
Regroupe (dissolve) des géométries selon un attribut ou globalement

**Paramètres :**
- `data`: Données géographiques
- `input_format`: Format d'entrée
- `by`: Colonne pour regroupement (optionnel, None = tout fusionner)
- `aggregations`: Fonctions d'agrégation (ex: {"pop": "sum"})
- `source_crs`: CRS source (optionnel)
- `target_crs`: CRS de sortie (optionnel)
- `output_format`: Format de sortie (optionnel)

**Exemple :**
```
"Fusionne toutes ces communes par région"
```

---

### 8. **explode_geodata**
Désassemble les géométries multi-parties en entités simples

**Paramètres :**
- `data`: Données géographiques
- `input_format`: Format d'entrée
- `source_crs`: CRS source (optionnel)
- `keep_index`: Conserver les index multi-parties (défaut: false)
- `output_format`: Format de sortie (optionnel)

**Exemple :**
```
"Sépare ce MultiPolygon en polygones individuels"
```

---

## 🔧 Formats supportés

### Formats texte (UTF-8)
- ✅ **GeoJSON** / JSON
- ✅ **KML** (Keyhole Markup Language)

### Formats binaires (base64)
- ✅ **GeoPackage** (.gpkg)
- ✅ **Shapefile** (.shp + fichiers associés, zippés)

---

## 🏗️ Architecture technique

### Module `spatial_processing.py` (~336 lignes)

**Fonctions principales :**
- `load_geodata()` - Charge les données depuis différents formats
- `dump_geodata()` - Exporte vers différents formats
- `normalize_format()` - Normalise les noms de formats
- `ensure_same_crs()` - Harmonise les CRS entre datasets

**Opérations géométriques :**
- `reproject_geodata()` - Reprojection
- `buffer_geodata()` - Buffer avec options avancées
- `intersect_geodata()` - Intersection (overlay)
- `clip_geodata()` - Découpage
- `convert_geodata_format()` - Conversion
- `get_geodata_bbox()` - Bounding box
- `dissolve_geodata()` - Fusion/agrégation
- `explode_geodata()` - Explosion multi-parties

**Gestion des erreurs :**
- `GeoProcessingError` - Exception personnalisée

---

## 🧪 Tests (test_spatial_processing.py)

### Tests implémentés (8)

1. ✅ `test_reproject` - Reprojection EPSG:4326 → EPSG:3857
2. ✅ `test_buffer` - Buffer de 500m en EPSG:3857
3. ✅ `test_intersection` - Intersection de deux polygones
4. ✅ `test_get_bbox` - Calcul de bounding box
5. ✅ `test_dissolve` - Fusion par attribut
6. ✅ `test_explode` - Explosion de MultiPolygon
7. ✅ `test_convert_to_shapefile` - Conversion vers Shapefile
8. ✅ `test_invalid_format_raises` - Gestion d'erreur

---

## 📊 Statistiques

| Métrique | Valeur |
|----------|--------|
| **Outils ajoutés** | +8 |
| **Total outils MCP** | 30 → **38** |
| **Lignes code Python** | +336 (spatial_processing.py) |
| **Lignes tests** | +138 (test_spatial_processing.py) |
| **Formats supportés** | 4 (GeoJSON, KML, GPKG, Shapefile) |
| **Dépendances** | geopandas, shapely, fiona |

---

## 💡 Cas d'usage

### Analyse territoriale
```
"Récupère les communes d'Île-de-France avec WFS,
crée un buffer de 5km autour, puis découpe avec les limites régionales"
```

**Outils combinés :**
1. `get_wfs_features` → communes
2. `buffer_geodata` → buffer 5km
3. `clip_geodata` → découpage

---

### Conversion et export
```
"Télécharge ce dataset GeoJSON de data.gouv.fr
et convertis-le en Shapefile pour QGIS"
```

**Outils combinés :**
1. `get_dataset_resources` → URL du GeoJSON
2. `convert_geodata_format` → Shapefile

---

### Fusion administrative
```
"Récupère toutes les communes de Bretagne,
fusionne-les par département,
calcule les populations totales"
```

**Outils combinés :**
1. `get_wfs_features` → communes Bretagne
2. `dissolve_geodata` (by="departement", aggregations={"pop": "sum"})

---

### Analyse spatiale multi-critères
```
"Trouve les bâtiments à moins de 100m d'une rivière
et dans une zone inondable"
```

**Workflow :**
1. `get_wfs_features` → bâtiments
2. `get_wfs_features` → rivières
3. `buffer_geodata` → buffer 100m autour des rivières
4. `get_wfs_features` → zones inondables
5. `intersect_geodata` → bâtiments ∩ buffer rivières
6. `intersect_geodata` → résultat ∩ zones inondables

---

## 🔐 Sécurité et limites

### Gestion des fichiers temporaires
- ✅ Utilisation de `tempfile.TemporaryDirectory()`
- ✅ Nettoyage automatique après traitement
- ✅ Isolation des processus

### Limites
- Pas de limite de taille imposée (dépend de la mémoire)
- Formats binaires encodés en base64 (augmente la taille de ~33%)
- Nécessite GeoPandas, Fiona, Shapely installés

### Erreurs gérées
- ✅ Formats non supportés
- ✅ Données vides ou invalides
- ✅ CRS incompatibles ou manquants
- ✅ Géométries nulles

---

## 🚀 Performance

### Asynchrone via `asyncio.to_thread`
```python
async def run_geoprocessing(func, **kwargs):
    return await asyncio.to_thread(partial(func, **kwargs))
```

**Avantages :**
- Ne bloque pas le serveur MCP
- Permet de traiter plusieurs requêtes en parallèle
- Utilise le ThreadPoolExecutor par défaut

---

## 📚 Dépendances requises

Ajout au `requirements.txt` :
```
geopandas>=0.14.0
shapely>=2.0.0
fiona>=1.9.0
pyproj>=3.6.0
```

---

## 🎯 Compatibilité

### Systèmes de coordonnées
- ✅ EPSG:4326 (WGS84 - GPS)
- ✅ EPSG:3857 (Web Mercator)
- ✅ EPSG:2154 (Lambert 93 - France)
- ✅ Tous les CRS supportés par PROJ

### Géométries
- ✅ Point, MultiPoint
- ✅ LineString, MultiLineString
- ✅ Polygon, MultiPolygon
- ✅ GeometryCollection

---

## 🏆 Résultat final

**38 outils MCP opérationnels** couvrant :
- ✅ Données publiques (6)
- ✅ Cartographie IGN (9)
- ✅ Navigation IGN (3)
- ✅ Altimétrie IGN (3)
- ✅ Géocodage (3)
- ✅ Territoire (6)
- ✅ **Traitement spatial (8)** ⭐ NOUVEAU

**Le serveur MCP est maintenant un SIG complet !** 🗺️
