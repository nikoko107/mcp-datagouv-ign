# Changelog

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
