# ⛰️ Exemples d'utilisation - Altimétrie IGN

Ce document présente des exemples concrets d'utilisation des outils d'altimétrie du serveur MCP.

## 📏 Récupération d'altitude

### Exemple 1 : Altitude d'un point unique

**Requête Claude :**
```
Quelle est l'altitude du sommet du Mont Blanc ?
```

**Paramètres utilisés :**
- `lon`: "6.8651" (Mont Blanc)
- `lat`: "45.8326"
- `resource`: "ign_rge_alti_wld"

**Résultat attendu :**
```json
{
  "elevations": [
    {
      "lon": 6.8651,
      "lat": 45.8326,
      "z": 4759.2,
      "acc": "Variable suivant la source de mesure"
    }
  ]
}
```

### Exemple 2 : Altitudes de plusieurs villes

**Requête Claude :**
```
Compare les altitudes de Paris, Lyon et Marseille
```

**Paramètres utilisés :**
- `lon`: "2.3522|4.8357|5.3698"
- `lat`: "48.8566|45.7640|43.2965"
- `delimiter`: "|"

**Résultat :**
- Paris : ~35 m
- Lyon : ~168 m
- Marseille : ~1 m

### Exemple 3 : Altitude avec détails de mesure

**Requête Claude :**
```
Donne-moi l'altitude de Grenoble avec les détails de la source de mesure
```

**Paramètres utilisés :**
- `lon`: "5.7243"
- `lat`: "45.1885"
- `measures`: true

---

## 📈 Profils altimétriques

### Exemple 4 : Profil simple entre deux villes

**Requête Claude :**
```
Calcule le profil altimétrique entre Paris et Versailles
```

**Paramètres utilisés :**
- `lon`: "2.3522|2.1242"
- `lat`: "48.8566|48.8049"
- `profile_mode`: "simple"
- `sampling`: 30

**Résultat attendu :**
- Dénivelé positif : ~159 m
- Dénivelé négatif : ~60 m
- 31 points d'échantillonnage

### Exemple 5 : Profil de randonnée en montagne

**Requête Claude :**
```
Calcule le profil altimétrique précis entre Grenoble et l'Alpe d'Huez
avec 100 points pour analyser la montée
```

**Paramètres utilisés :**
- `lon`: "5.7243|6.0709"
- `lat`: "45.1885|45.0904"
- `profile_mode`: "accurate"
- `sampling`: 100

**Résultat :**
- Altitude min : ~212 m (Grenoble)
- Altitude max : ~2420 m (Alpe d'Huez)
- Dénivelé positif : ~4944 m (cumul des montées)
- Dénivelé négatif : ~3348 m (cumul des descentes)

### Exemple 6 : Profil le long d'un itinéraire

**Requête Claude :**
```
Je veux faire une randonnée qui passe par ces 5 points de passage.
Calcule le profil altimétrique complet.
```

**Paramètres utilisés :**
- `lon`: "6.8|6.9|7.0|7.1|7.2" (5 points)
- `lat`: "45.8|45.85|45.9|45.95|46.0"
- `sampling`: 200 (pour avoir beaucoup de détails)

### Exemple 7 : Profil simple sans coordonnées détaillées

**Requête Claude :**
```
Donne-moi juste les altitudes le long du chemin, sans les coordonnées
```

**Paramètres utilisés :**
- `lon`: "2.3|2.4|2.5"
- `lat`: "48.8|48.85|48.9"
- `zonly`: true

**Résultat :**
Tableau simple d'altitudes : `[35.2, 78.5, 112.3, ...]`

---

## 🏔️ Cas d'usage avancés

### Analyse de col de montagne

**Requête :**
```
Analyse le profil altimétrique du Col du Galibier depuis les deux versants
(Valloire et Le Lautaret) pour comparer la difficulté
```

**Méthode :**
1. Profil Valloire → Col (versant nord)
2. Profil Lautaret → Col (versant sud)
3. Comparaison des dénivelés et pentes

### Planification de parcours vélo

**Requête :**
```
Pour mon parcours vélo de 50km, calcule le profil altimétrique détaillé
avec échantillonnage tous les 250 mètres
```

**Paramètres :**
- Points GPS du parcours
- `sampling`: 200 (50km / 250m = 200 points)
- `profile_mode`: "accurate"

### Étude d'inondation

**Requête :**
```
Récupère les altitudes de ces 1000 points pour modéliser
la zone inondable d'une rivière
```

**Paramètres :**
- Liste de 1000 coordonnées (max 5000)
- `zonly`: true (uniquement altitudes)

### Visualisation de relief

**Requête :**
```
Pour créer une carte 3D, récupère une grille d'altitudes
sur cette zone de 10x10 km
```

**Méthode :**
Générer une grille de points et récupérer leurs altitudes

---

## 🔧 Ressources altimétriques

### Ressource principale : `ign_rge_alti_wld`

Cette ressource mondiale fournit :
- Couverture : France et DOM-TOM
- Précision : Variable selon la source
- MNT (Modèle Numérique de Terrain)

### Obtenir la liste des ressources

**Requête :**
```
Quelles sont les ressources altimétriques disponibles ?
```

Utilise `get_altimetry_resources` pour voir :
- Les différents MNT disponibles
- Les zones de couverture
- Les résolutions
- Les sources de données

---

## 📊 Limites et bonnes pratiques

### Limites de l'API

- **Maximum** : 5000 points par requête
- **Débit** : 5 requêtes/seconde
- **Valeur non-data** : -99999 pour zones non couvertes
- **Précision** : Altitudes arrondies à 2 décimales

### Bonnes pratiques

1. **Format des coordonnées**
   - Toujours décimal (pas de degrés/minutes/secondes)
   - Longitude en premier, latitude en second
   - Séparateur cohérent (| par défaut)

2. **Échantillonnage de profils**
   - `sampling`: 2-50 pour aperçu rapide
   - `sampling`: 50-200 pour analyse détaillée
   - `sampling`: 200-5000 pour études précises

3. **Mode de profil**
   - `simple` : Rapide, bon pour visualisation
   - `accurate` : Précis, recommandé pour calculs d'itinéraires

4. **Performance**
   - Utiliser `zonly=true` si coordonnées non nécessaires
   - Grouper les requêtes pour points multiples
   - Éviter `measures=true` si non nécessaire

---

## 🎯 Formules utiles

### Calculer la pente moyenne

```
Pente (%) = (Dénivelé / Distance horizontale) × 100
```

### Estimer la difficulté d'un parcours

- **Facile** : < 200m de dénivelé positif
- **Moyen** : 200-500m
- **Difficile** : 500-1000m
- **Très difficile** : > 1000m

### Dénivelé cumulé vs dénivelé net

- **Dénivelé net** : Altitude finale - Altitude initiale
- **Dénivelé positif cumulé** : Somme de toutes les montées
- **Dénivelé négatif cumulé** : Somme de toutes les descentes

---

## 🔗 Ressources complémentaires

- Documentation API : https://geoservices.ign.fr/documentation/services/services-geoplateforme/altimetrie
- Swagger UI : https://data.geopf.fr/altimetrie/swagger-ui/index.html
- Contact : contact.geoservices@ign.fr

---

## 💡 Combinaison avec d'autres outils

### Altitude + Géocodage

```
"Quelle est l'altitude du centre-ville de Chamonix ?"
```
1. Géocoder "Chamonix" → coordonnées
2. Récupérer altitude des coordonnées

### Profil + Itinéraire

```
"Calcule l'itinéraire de Grenoble à l'Alpe d'Huez
et montre-moi le profil altimétrique"
```
1. Calculer itinéraire → liste de points GPS
2. Extraire coordonnées de la géométrie
3. Calculer profil altimétrique

### Altitude + Carte

```
"Affiche sur une carte IGN les points au-dessus de 2000m d'altitude
dans cette zone"
```
1. Récupérer altitudes d'une grille de points
2. Filtrer > 2000m
3. Afficher sur carte WMS/WMTS
