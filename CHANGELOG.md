# Changelog

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
