# 🇫🇷 Serveur MCP - Données Ouvertes Françaises + IGN

Serveur MCP complet permettant à Claude d'accéder aux données publiques françaises et aux services cartographiques nationaux.

## 📦 Sources de données

### 1. **data.gouv.fr** - Plateforme ouverte des données publiques
- Recherche de jeux de données
- Informations sur les organisations
- Réutilisations de données

### 2. **IGN Géoplateforme** - Services cartographiques nationaux
- **WMTS** : Tuiles de cartes pré-générées (rapide)
- **WMS** : Cartes à la demande (personnalisable)
- **WFS** : Données vectorielles (analyse)

### 3. **API Adresse** - Géocodage national
- Convertir adresses → coordonnées GPS
- Convertir coordonnées → adresses
- Autocomplétion d'adresses

### 4. **API Geo** - Découpage administratif
- 35 000+ communes françaises
- Départements et régions
- Données démographiques

## 🚀 Installation

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Configurer Claude Desktop

**macOS** : `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows** : `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux** : `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "french-opendata": {
      "command": "python",
      "args": [
        "/CHEMIN/ABSOLU/VERS/french_opendata_complete_mcp.py"
      ]
    }
  }
}
```

**⚠️ Important** : Remplacez `/CHEMIN/ABSOLU/VERS/` par le chemin réel où vous avez placé les fichiers.

### 3. Redémarrer Claude Desktop

Fermez complètement Claude Desktop et relancez-le.

## 🛠️ Outils disponibles (24 au total)

### Data.gouv.fr (6 outils)
- `search_datasets` - Rechercher des jeux de données
- `get_dataset` - Détails d'un dataset
- `search_organizations` - Rechercher des organisations
- `get_organization` - Détails d'une organisation
- `search_reuses` - Rechercher des réutilisations
- `get_dataset_resources` - Lister les fichiers d'un dataset

### IGN Géoplateforme (9 outils)
- `list_wmts_layers` - Lister les couches WMTS
- `search_wmts_layers` - Rechercher des couches WMTS
- `get_wmts_tile_url` - URL de tuile WMTS
- `list_wms_layers` - Lister les couches WMS
- `search_wms_layers` - Rechercher des couches WMS
- `get_wms_map_url` - URL de carte WMS
- `list_wfs_features` - Lister les features WFS
- `search_wfs_features` - Rechercher des features WFS
- `get_wfs_features` - Récupérer des données vectorielles

### API Adresse (3 outils)
- `geocode_address` - Adresse → GPS
- `reverse_geocode` - GPS → Adresse
- `search_addresses` - Autocomplétion

### API Geo (6 outils)
- `search_communes` - Rechercher des communes
- `get_commune_info` - Info commune complète
- `get_departement_communes` - Communes d'un département
- `search_departements` - Rechercher des départements
- `search_regions` - Rechercher des régions
- `get_region_info` - Info région

## 💡 Exemples d'utilisation

### Géocodage + Cartographie
```
"Géocode l'adresse '1 Avenue des Champs-Élysées, Paris' puis affiche-la sur une carte IGN"
```

### Recherche territoriale
```
"Quelle est la population de Lyon ? Montre-moi les orthophotos et trouve des données ouvertes"
```

### Analyse géographique
```
"Récupère les limites administratives de la Bretagne en GeoJSON"
```

## 📁 Structure des fichiers

```
mcp-datagouv-ign/
├── french_opendata_complete_mcp.py    # Serveur principal
├── ign_geo_services.py                # Module IGN
├── requirements.txt                   # Dépendances
└── README.md                          # Cette documentation
```

## 🔧 Dépannage

### Le serveur ne démarre pas
1. Vérifiez Python 3.8+ : `python --version`
2. Vérifiez les dépendances : `pip list | grep -E "mcp|httpx"`
3. Vérifiez les chemins absolus dans la config

### Les outils ne s'affichent pas dans Claude
1. Redémarrez complètement Claude Desktop
2. Vérifiez les logs : Menu → Settings → Developer

### Erreurs de connexion
- Vérifiez votre connexion Internet
- Les APIs publiques peuvent avoir des limites de débit

## 📚 Documentation des APIs

- **data.gouv.fr** : https://doc.data.gouv.fr/api/
- **IGN Géoplateforme** : https://geoservices.ign.fr/
- **API Adresse** : https://adresse.data.gouv.fr/api-doc/adresse
- **API Geo** : https://geo.api.gouv.fr/

## 🎨 Couches IGN populaires

### WMTS/WMS
- `ORTHOIMAGERY.ORTHOPHOTOS` - Photos aériennes
- `GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2` - Plan IGN
- `CADASTRALPARCELS.PARCELLAIRE_EXPRESS` - Cadastre
- `TRANSPORTNETWORKS.ROADS` - Réseau routier
- `ADMINISTRATIVEUNITS.BOUNDARIES` - Limites administratives

### WFS (données vectorielles)
- `ADMINEXPRESS-COG-CARTO.LATEST:commune` - Communes
- `ADMINEXPRESS-COG-CARTO.LATEST:departement` - Départements
- `BDTOPO_V3:batiment` - Bâtiments

## 📄 Licence

Ce serveur MCP utilise des APIs publiques françaises. Consultez les conditions d'utilisation de chaque service.

## 🆘 Support

Pour toute question :
1. Consultez la documentation des APIs
2. Vérifiez les logs de Claude Desktop
3. Assurez-vous d'utiliser la dernière version du MCP SDK

---

Créé pour faciliter l'accès aux données ouvertes françaises 🇫🇷
