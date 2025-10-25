# 🧭 Exemples d'utilisation - Navigation IGN

Ce document présente des exemples concrets d'utilisation des outils de navigation (itinéraires et isochrones) du serveur MCP.

## 📍 Calcul d'itinéraires

### Exemple 1 : Itinéraire simple Paris → Lyon

**Requête Claude :**
```
Calcule l'itinéraire le plus rapide en voiture entre Paris et Lyon
```

**Paramètres utilisés :**
- `start`: "2.3522,48.8566" (Paris)
- `end`: "4.8357,45.7640" (Lyon)
- `resource`: "bdtopo-osrm" (moteur rapide)
- `profile`: "car"
- `optimization`: "fastest"

**Résultat attendu :**
- Distance : ~466 km
- Durée : ~4h45
- Géométrie GeoJSON de l'itinéraire
- Étapes détaillées

### Exemple 2 : Itinéraire le plus court

**Requête Claude :**
```
Calcule l'itinéraire le PLUS COURT (pas le plus rapide) entre Marseille et Nice
```

**Paramètres utilisés :**
- `start`: "5.3698,43.2965" (Marseille)
- `end`: "7.2619,43.7102" (Nice)
- `optimization`: "shortest" (au lieu de "fastest")

### Exemple 3 : Itinéraire avec étapes intermédiaires

**Requête Claude :**
```
Calcule un itinéraire de Paris à Bordeaux en passant par Tours et Poitiers
```

**Paramètres utilisés :**
- `start`: "2.3522,48.8566" (Paris)
- `end`: "-0.5792,44.8378" (Bordeaux)
- `intermediates`: ["0.6833,47.3900", "0.3333,46.5833"] (Tours, Poitiers)

### Exemple 4 : Itinéraire piéton

**Requête Claude :**
```
Calcule un itinéraire à pied entre la Tour Eiffel et le Louvre
```

**Paramètres utilisés :**
- `start`: "2.2945,48.8584" (Tour Eiffel)
- `end`: "2.3364,48.8606" (Louvre)
- `profile`: "pedestrian"
- `resource`: "bdtopo-valhalla" (meilleur pour les piétons)

---

## 🔄 Isochrones et Isodistances

### Exemple 5 : Isochrone 30 minutes en voiture

**Requête Claude :**
```
Montre-moi toutes les zones accessibles en 30 minutes en voiture depuis le centre de Lyon
```

**Paramètres utilisés :**
- `point`: "4.8357,45.7640" (Lyon)
- `cost_value`: 0.5 (30 minutes = 0.5 heures)
- `cost_type`: "time"
- `profile`: "car"
- `time_unit`: "hour"

**Résultat :**
- Polygone GeoJSON représentant la zone accessible
- Peut être affiché sur une carte

### Exemple 6 : Isochrone piéton (15 minutes)

**Requête Claude :**
```
Quelle zone peut-on atteindre à pied en 15 minutes depuis la gare de Toulouse Matabiau ?
```

**Paramètres utilisés :**
- `point`: "1.4541,43.6108"
- `cost_value`: 0.25 (15 minutes)
- `cost_type`: "time"
- `profile`: "pedestrian"

### Exemple 7 : Isodistance (rayon de 10 km)

**Requête Claude :**
```
Quelle est la zone accessible en voiture dans un rayon de 10 km depuis Strasbourg ?
```

**Paramètres utilisés :**
- `point`: "7.7521,48.5734"
- `cost_value`: 10
- `cost_type`: "distance"
- `distance_unit`: "kilometer"

### Exemple 8 : Isochrone "arrivée" (temps pour ATTEINDRE un point)

**Requête Claude :**
```
D'où peut-on arriver à l'aéroport Charles de Gaulle en 45 minutes maximum ?
```

**Paramètres utilisés :**
- `point`: "2.5479,49.0097" (CDG)
- `cost_value`: 0.75
- `cost_type`: "time"
- `direction`: "arrival" (inverse : qui peut atteindre ce point)

---

## 🔧 Ressources de navigation disponibles

### Moteurs de calcul

1. **bdtopo-osrm** (recommandé pour itinéraires voiture)
   - ✅ Très rapide
   - ✅ Performances excellentes
   - ⚠️ Contraintes limitées

2. **bdtopo-valhalla** (recommandé pour isochrones)
   - ✅ Bon équilibre performance/fonctionnalités
   - ✅ Supporte bien les piétons
   - ✅ Contraintes modérées

3. **bdtopo-pgr**
   - ✅ Contraintes avancées
   - ⚠️ Plus lent
   - 💡 Pour cas complexes uniquement

---

## 🎯 Cas d'usage avancés

### Planification de livraisons

**Requête :**
```
Calcule un itinéraire de livraison partant de notre entrepôt à Rungis,
passant par 3 points de livraison dans Paris, puis retour à l'entrepôt
```

### Analyse d'accessibilité transport

**Requête :**
```
Compare les zones accessibles en 1 heure en voiture vs en transports en commun
depuis la gare de Lyon à Paris
```

### Étude d'implantation commerciale

**Requête :**
```
Pour un nouveau magasin à ouvrir à Nantes, montre-moi la zone de chalandise
(clients potentiels dans un rayon de 20 minutes en voiture)
```

### Analyse temps de trajet domicile-travail

**Requête :**
```
Si je travaille à La Défense, quels quartiers de Paris et banlieue
sont accessibles en moins de 45 minutes en transports ?
```

---

## 📊 Limites et bonnes pratiques

### Limites de l'API

- **Débit** : 5 requêtes/seconde maximum
- **Timeout** : 30 secondes recommandé
- **Isochrones** : Contraintes "banned" uniquement (pas preferred/unpreferred)

### Bonnes pratiques

1. **Format des coordonnées** : Toujours "longitude,latitude" (pas l'inverse !)
2. **Unités** : Vérifier les unités (hour vs minute, kilometer vs meter)
3. **Profil** : Choisir "car" ou "pedestrian" selon le besoin
4. **Ressource** :
   - OSRM pour itinéraires voiture rapides
   - Valhalla pour isochrones et piétons
   - PGR uniquement si contraintes avancées nécessaires

---

## 🔗 Ressources complémentaires

- Documentation API : https://geoservices.ign.fr/documentation/services/services-geoplateforme/itineraire
- Spécification Swagger : https://www.geoportail.gouv.fr/depot/swagger/itineraire.html
- Contact support : contact.geoservices@ign.fr
