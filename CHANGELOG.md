# Changelog

## [1.3.0] - 2025-10-25

### Ajouts majeurs

#### 🗺️ Nouveaux outils de Traitement Spatial (GeoPandas)

Ajout de 8 outils de traitement spatial basés sur GeoPandas pour manipuler et analyser des données géographiques :

1. **reproject_geodata**
   - Reprojection vers n'importe quel CRS (EPSG:4326, EPSG:3857, etc.)
   - Support de tous les systèmes de coordonnées PROJ

2. **buffer_geodata**
   - Création de tampons avec distance personnalisable
   - Options avancées : cap_style, join_style, single_sided
   - Résolution configurable

3. **intersect_geodata**
   - Calcul d'intersection entre deux jeux de données
   - Préserve les attributs des deux sources
   - Gestion automatique des CRS

4. **clip_geodata**
   - Découpage spatial avec géométrie de clip
   - Équivalent de "clip" dans les SIG

5. **convert_geodata_format**
   - Conversion entre GeoJSON, KML, GeoPackage, Shapefile
   - Formats binaires encodés en base64
   - Préservation des attributs

6. **get_geodata_bbox**
   - Calcul de bounding box (minx, miny, maxx, maxy)
   - Reprojection de la bbox possible

7. **dissolve_geodata**
   - Fusion de géométries par attribut
   - Agrégations personnalisables (sum, mean, etc.)
   - Fusion globale possible

8. **explode_geodata**
   - Séparation des multi-géométries en simples
   - Préservation ou réindexation des entités

#### 📚 Documentation

- Nouveau fichier `RESUME_TRAITEMENTS_SPATIAUX.md` détaillé
- Module `spatial_processing.py` (~336 lignes)
- Tests complets `test_spatial_processing.py` (8 tests)

#### 🔧 Technique

- **Module spatial_processing.py** :
  - Gestion multi-formats (GeoJSON, KML, GPKG, Shapefile)
  - Encodage base64 pour formats binaires
  - Fichiers temporaires auto-nettoyés
  - Gestion d'erreurs robuste (GeoProcessingError)

- **Intégration async** :
  - Utilisation de `asyncio.to_thread` pour ne pas bloquer
  - Fonction helper `run_geoprocessing()`

- **Nouvelles dépendances** :
  - geopandas >= 0.14
  - shapely >= 2.0
  - fiona >= 1.9
  - pyproj >= 3.6

### Tests validés

- ✅ Reprojection EPSG:4326 → EPSG:3857
- ✅ Buffer 500m en coordonnées métriques
- ✅ Intersection de polygones
- ✅ Calcul de bounding box
- ✅ Dissolution par attribut
- ✅ Explosion de MultiPolygon en Polygons
- ✅ Conversion vers Shapefile (zippé, base64)
- ✅ Gestion d'erreurs pour formats invalides

### Formats supportés

**Texte (UTF-8)** :
- GeoJSON / JSON
- KML

**Binaire (base64)** :
- GeoPackage (.gpkg)
- Shapefile (.shp + fichiers associés, zippés)

### Statistiques

- **Nombre total d'outils** : 30 → **38** (+8)
- **Lignes de code** : +336 (spatial_processing.py)
- **Lignes de tests** : +138 (test_spatial_processing.py)
- **Formats géographiques** : 4

### Compatibilité

- Python 3.8+
- Requiert installation de GDAL/GEOS (via geopandas)
- Compatible avec tous les CRS supportés par PROJ
- Toutes géométries : Point, Line, Polygon, Multi*

---

## [1.2.0] - 2025-10-25

### Ajouts majeurs

#### ⛰️ Nouvelles fonctionnalités d'Altimétrie IGN

Ajout de 3 nouveaux outils pour le calcul d'altitudes et de profils altimétriques :

1. **get_altimetry_resources**
   - Liste les ressources altimétriques disponibles
   - Affiche les MNT (Modèles Numériques de Terrain) accessibles
   - Détails sur zones de couverture et précision

2. **get_elevation**
   - Récupère l'altitude d'un ou plusieurs points (max 5000)
   - Support multi-points avec délimiteur personnalisable
   - Option pour détails de mesure multi-sources
   - Précision à 2 décimales

3. **get_elevation_line**
   - Calcule un profil altimétrique le long d'une ligne
   - Dénivelés positif et négatif cumulés
   - Modes : simple (rapide) ou accurate (précis)
   - Échantillonnage configurable (2-5000 points)

#### 📚 Documentation

- Nouveau fichier `EXEMPLES_ALTIMETRIE.md` avec 7+ exemples détaillés
- Mise à jour du README (30 outils au total)
- Script de test `test_altimetrie.py` avec 5 tests validés

#### 🔧 Technique

- Ajout de 3 nouvelles méthodes dans `ign_geo_services.py` :
  - `get_altimetry_resources()`
  - `get_elevation()`
  - `get_elevation_line()`
- Support des paramètres : delimiter, zonly, measures, profile_mode, sampling
- Gestion des erreurs et valeurs non-data (-99999)

### Tests validés

- ✅ Altitude du Mont Blanc : 4759.2 m
- ✅ Multi-points : Paris (35m), Lyon (168m), Marseille (1m)
- ✅ Profil Paris-Versailles : +159m / -60m
- ✅ Profil montagnard Grenoble-Alpe d'Huez : +4944m / -3348m

### Statistiques

- **Nombre total d'outils** : 27 → **30** (+3)
- **APIs IGN** : 4 (Navigation) → **5** (+Altimétrie)
- **Nouveaux endpoints** : 3

### Ressources disponibles

- **ign_rge_alti_wld** : Ressource mondiale (France + DOM-TOM)
- 9 ressources altimétriques au total

### Compatibilité

- Python 3.8+
- Aucune nouvelle dépendance requise
- Compatible avec toutes les versions existantes

---

## [1.1.0] - 2025-10-25

### Ajouts majeurs

#### 🧭 Nouvelles fonctionnalités de Navigation IGN

Ajout de 3 nouveaux outils pour le calcul d'itinéraires et d'isochrones :

1. **get_route_capabilities**
   - Récupère les capacités du service de navigation
   - Liste les ressources disponibles (bdtopo-osrm, bdtopo-valhalla, bdtopo-pgr)
   - Affiche les profils et optimisations supportés

2. **calculate_route**
   - Calcule un itinéraire entre deux points
   - Supporte plusieurs modes : voiture, piéton
   - Optimisation : plus rapide ou plus court
   - Points intermédiaires optionnels
   - Contraintes de routage (routes interdites, préférées, etc.)
   - Retourne : distance, durée, géométrie GeoJSON, étapes détaillées

3. **calculate_isochrone**
   - Calcule une isochrone (zone accessible en temps donné)
   - Calcule une isodistance (zone accessible en distance donnée)
   - Direction : départ ou arrivée
   - Retourne : polygone GeoJSON de la zone accessible

#### 📚 Documentation

- Nouveau fichier `EXEMPLES_NAVIGATION.md` avec 8 exemples détaillés
- Mise à jour du README avec les nouveaux outils
- Script de test `test_navigation.py` pour validation

#### 🔧 Technique

- Ajout de 3 nouvelles méthodes dans `ign_geo_services.py` :
  - `get_route_capabilities()`
  - `calculate_route()`
  - `calculate_isochrone()`
- Ajout des constantes d'URL pour les endpoints de navigation
- Gestion complète des paramètres et erreurs HTTP

### Statistiques

- **Nombre total d'outils** : 24 → **27** (+3)
- **APIs supportées** : 4 (inchangé)
- **Nouveaux endpoints IGN** : 3

### Ressources de navigation disponibles

- **bdtopo-osrm** : Moteur rapide pour itinéraires voiture
- **bdtopo-valhalla** : Équilibré, recommandé pour isochrones et piétons
- **bdtopo-pgr** : Contraintes avancées, calcul plus lent

### Compatibilité

- Python 3.8+
- Aucune nouvelle dépendance requise
- Compatible avec toutes les versions existantes du serveur MCP

---

## [1.0.0] - Date initiale

### Fonctionnalités initiales

- Support de data.gouv.fr (6 outils)
- Support IGN Cartographie : WMTS, WMS, WFS (9 outils)
- Support API Adresse (3 outils)
- Support API Geo (6 outils)
- Total : 24 outils
