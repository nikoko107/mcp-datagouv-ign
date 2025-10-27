# Système de cache pour réponses API volumineuses

## 🎯 Problème résolu

Les réponses API IGN peuvent contenir **des milliers de coordonnées** :
- **Itinéraires** : géométries LineString avec centaines/milliers de points + steps détaillés
- **Isochrones** : polygones avec centaines de points
- **WFS** : centaines de features avec géométries complexes
- **Profils altimétriques** : centaines de points d'élévation

Ces réponses JSON volumineuses (>100KB) **saturent le contexte Claude**, provoquant l'erreur "conversation trop longue".

## ✅ Solution

### Architecture

1. **Cache automatique fichier** :
   - Réponses volumineuses → stockées dans `~/.mcp_cache/french_opendata/`
   - Claude reçoit **seulement des métadonnées légères** (< 2KB)
   - Données complètes récupérables via `cache_id` si nécessaire

2. **Métadonnées intelligentes** :
   - **Itinéraire** : distance, durée, bbox, start/end, nb_points, nb_steps
   - **Isochrone** : point, temps/distance, bbox, nb_points
   - **WFS** : typename, nb_features, exemple_feature
   - **Profil** : nb_points, altitude_min/max, dénivelé

3. **Gestion automatique** :
   - Expiration : 24 heures
   - Nettoyage : automatique des fichiers expirés
   - Cache ID unique : `{tool}_{timestamp}_{hash}`

## 🔧 Outils concernés

### Cache automatique activé

Ces outils cachent **automatiquement** leurs résultats :

- ✅ `calculate_route` → Toujours caché
- ✅ `calculate_isochrone` → Toujours caché
- ✅ `get_elevation_line` → Toujours caché
- ✅ `get_wfs_features` → Caché si >50 features

### Nouveaux outils de gestion

- 📥 `get_cached_data(cache_id, include_full_data=False)` : Récupérer données cachées
- 📋 `list_cached_data()` : Lister tous les items en cache

## 📖 Workflow typique

### Exemple 1 : Distance entre deux points

```python
# 1. L'utilisateur demande : "Quelle est la distance Paris-Lyon en voiture ?"

# 2. Claude appelle :
calculate_route(start="2.3522,48.8566", end="4.8357,45.7640")

# 3. Réponse légère reçue :
{
  "cached": true,
  "cache_id": "calculate_route_1704123456_a1b2c3d4",
  "file_path": "~/.mcp_cache/french_opendata/calculate_route_1704123456_a1b2c3d4.json",
  "file_size_kb": 156.23,
  "expires_at": "2025-01-28T10:30:00",
  "summary": {
    "distance": 465.2,
    "duration": 4.5,
    "bbox": [2.35, 45.76, 4.84, 48.86],
    "start": "2.3522,48.8566",
    "end": "4.8357,45.7640",
    "geometry_points_count": 2847,
    "steps_count": 134
  },
  "usage": "Pour réutiliser ces données, utilisez 'get_cached_data' avec cache_id='calculate_route_1704123456_a1b2c3d4'"
}

# 4. Claude répond à l'utilisateur : "465 km, environ 4h30"
# ✅ Pas besoin des données complètes !
```

### Exemple 2 : Afficher itinéraire sur carte

```python
# 1. L'utilisateur demande : "Affiche l'itinéraire Paris-Lyon sur une carte"

# 2. Claude appelle :
calculate_route(start="2.3522,48.8566", end="4.8357,45.7640")
# → Reçoit métadonnées + cache_id

# 3. Claude a besoin de la géométrie complète :
get_cached_data(cache_id="calculate_route_1704123456_a1b2c3d4", include_full_data=True)

# 4. Réponse complète :
{
  "cache_id": "calculate_route_1704123456_a1b2c3d4",
  "summary": { ... },
  "full_data": {
    "distance": 465.2,
    "duration": 4.5,
    "geometry": {
      "type": "LineString",
      "coordinates": [
        [2.3522, 48.8566],
        [2.3534, 48.8578],
        ... 2847 points ...
        [4.8357, 45.7640]
      ]
    },
    "portions": [ ... steps détaillés ... ]
  }
}

# 5. Claude fournit le GeoJSON complet à l'utilisateur
```

### Exemple 3 : Communes dans isochrone

```python
# 1. L'utilisateur demande : "Quelles communes sont à 30 min de Paris centre ?"

# 2. Claude appelle :
calculate_isochrone(point="2.35,48.85", cost_value=30, cost_type="time")
# → Reçoit métadonnées + bbox + cache_id

# 3. Claude a besoin du polygone complet pour intersect :
get_cached_data(cache_id="calculate_isochrone_1704123456_x9y8z7", include_full_data=True)

# 4. Claude récupère communes WFS :
get_wfs_features(typename="commune", bbox=<bbox_from_isochrone>)

# 5. Claude fait l'intersection :
intersect_geodata(data1=<isochrone_polygon>, data2=<communes_geojson>)

# 6. Claude liste les communes intersectées
```

## 🗂️ Structure des fichiers

```
~/.mcp_cache/french_opendata/
├── calculate_route_1704123456_a1b2c3d4.json          # Données complètes
├── calculate_route_1704123456_a1b2c3d4_meta.json     # Métadonnées
├── calculate_isochrone_1704123789_x9y8z7.json
├── calculate_isochrone_1704123789_x9y8z7_meta.json
├── get_wfs_features_1704124000_f3g4h5.json
└── get_wfs_features_1704124000_f3g4h5_meta.json
```

## ⚙️ Configuration

### Paramètres par défaut

```python
# response_cache.py
CACHE_DIR = Path.home() / ".mcp_cache" / "french_opendata"
CACHE_TTL_SECONDS = 24 * 3600  # 24 heures
```

### Seuils de cache

```python
def should_cache_response(data, tool_name):
    # Toujours cacher
    if tool_name in ["calculate_route", "calculate_isochrone", "get_elevation_line"]:
        return True

    # WFS : >50 features
    if tool_name == "get_wfs_features":
        if len(data.get("features", [])) > 50:
            return True

    # Taille JSON >10KB
    if len(json.dumps(data)) > 10 * 1024:
        return True

    return False
```

## 📊 Comparaison avant/après

### Avant (sans cache)

```json
// calculate_route() retournait directement 156 KB :
{
  "distance": 465.2,
  "duration": 4.5,
  "geometry": {
    "type": "LineString",
    "coordinates": [[2.35, 48.85], [2.36, 48.86], ... 2847 points ... ]
  },
  "portions": [
    {
      "steps": [
        { "id": 1, "geometry": {...}, "instructions": "..." },
        { "id": 2, "geometry": {...}, "instructions": "..." },
        ... 134 steps ...
      ]
    }
  ]
}
// ❌ Contexte Claude saturé !
```

### Après (avec cache)

```json
// calculate_route() retourne 2 KB :
{
  "cached": true,
  "cache_id": "calculate_route_1704123456_a1b2c3d4",
  "file_size_kb": 156.23,
  "summary": {
    "distance": 465.2,
    "duration": 4.5,
    "bbox": [2.35, 45.76, 4.84, 48.86],
    "geometry_points_count": 2847,
    "steps_count": 134
  }
}
// ✅ Contexte Claude préservé !
```

## 🔍 Bonnes pratiques

### Quand utiliser include_full_data=True ?

✅ **OUI** :
- Afficher géométrie sur carte
- Analyses spatiales (buffer, clip, intersect)
- Export de données (GeoJSON, KML)
- Récupérer instructions navigation détaillées

❌ **NON** :
- Répondre à "Quelle est la distance ?" (summary suffit)
- Répondre à "Combien de communes ?" (summary suffit)
- Répondre à "Quel est le dénivelé ?" (summary suffit)

### Nettoyage manuel

```bash
# Supprimer cache manuellement
rm -rf ~/.mcp_cache/french_opendata/

# Le cache sera recréé automatiquement au prochain appel
```

### Désactiver le cache (pas recommandé)

Si vous voulez vraiment désactiver le cache, modifiez `response_cache.py` :

```python
def should_cache_response(data, tool_name):
    return False  # Désactive complètement le cache
```

## 📈 Statistiques typiques

| Outil | Taille brute | Taille métadonnées | Réduction |
|-------|--------------|-------------------|-----------|
| calculate_route (Paris-Lyon) | 156 KB | 2 KB | **98.7%** |
| calculate_isochrone (30min) | 89 KB | 1.5 KB | **98.3%** |
| get_wfs_features (100 communes) | 423 KB | 2.8 KB | **99.3%** |
| get_elevation_line (200 points) | 45 KB | 1.2 KB | **97.3%** |

**Économie moyenne de contexte : 98%** 🎉

## 🆘 Dépannage

### Erreur "Cache not found"

```json
{
  "error": "Cache not found or expired",
  "message": "Ce cache n'existe pas ou a expiré (durée de vie: 24h). Relancez le calcul original."
}
```

**Solution** : Relancer l'appel API original (calculate_route, etc.)

### Cache corrompu

Si fichiers cache corrompus :

```bash
rm -rf ~/.mcp_cache/french_opendata/
```

Le système recréera automatiquement le dossier.

## 🔄 Version

- **Version** : 1.5.0
- **Date** : 2025-01-27
- **Outils avec cache** : 4 (calculate_route, calculate_isochrone, get_wfs_features, get_elevation_line)
- **Outils de gestion** : 2 (get_cached_data, list_cached_data)
