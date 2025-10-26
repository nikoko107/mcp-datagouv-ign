"""
Catalogue des couches IGN Géoplateforme principales
Mise à jour : 2025-01-26
Source : https://geoservices.ign.fr/documentation/donnees
"""

# Couches WMTS principales (tuiles pré-générées)
WMTS_LAYERS = {
    "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2": {
        "title": "Plan IGN V2",
        "description": "Carte topographique vectorielle multi-échelles, style moderne",
        "category": "Cartes topographiques",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Fond de carte général, navigation, contexte cartographique",
        "update_frequency": "Mensuelle"
    },
    "ORTHOIMAGERY.ORTHOPHOTOS": {
        "title": "Photographies aériennes",
        "description": "Orthophotographies IGN récentes, résolution 20cm à 5m selon zones",
        "category": "Imagerie",
        "formats": ["image/jpeg", "image/png"],
        "min_zoom": 0,
        "max_zoom": 20,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Fond de carte réaliste, reconnaissance terrain, urbanisme",
        "update_frequency": "Annuelle"
    },
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS": {
        "title": "Parcelles cadastrales",
        "description": "Plan cadastral informatisé vecteur (PCI), parcelles et bâtiments",
        "category": "Cadastre",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 20,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Cadastre, urbanisme, foncier, immobilier",
        "update_frequency": "Trimestrielle"
    },
    "GEOGRAPHICALGRIDSYSTEMS.MAPS": {
        "title": "Cartes IGN",
        "description": "Cartes topographiques IGN 1:25000 (scan), style classique",
        "category": "Cartes topographiques",
        "formats": ["image/jpeg", "image/png"],
        "min_zoom": 0,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Randonnée, cartographie traditionnelle, relief",
        "update_frequency": "Annuelle"
    },
    "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR": {
        "title": "Carte IGN Série Bleue (1:25000)",
        "description": "Scan 25 Touristique, cartes détaillées pour randonnée",
        "category": "Cartes topographiques",
        "formats": ["image/jpeg"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Randonnée, trails, sports outdoor",
        "update_frequency": "Annuelle"
    },
    "ELEVATION.ELEVATIONGRIDCOVERAGE": {
        "title": "Altitudes (MNT)",
        "description": "Modèle Numérique de Terrain colorisé par tranches d'altitude",
        "category": "Altimétrie",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Visualisation relief, analyses altimétriques",
        "update_frequency": "Stable"
    },
    "ELEVATION.SLOPES": {
        "title": "Pentes du terrain",
        "description": "Visualisation des pentes en degrés (0-90°)",
        "category": "Altimétrie",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Analyses de pentes, risques naturels, aménagement",
        "update_frequency": "Stable"
    },
    "TRANSPORTNETWORKS.ROADS": {
        "title": "Réseau routier",
        "description": "Graphe routier avec classification (autoroutes, nationales, etc.)",
        "category": "Réseaux",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Navigation, analyses de réseaux, transport",
        "update_frequency": "Trimestrielle"
    },
    "LANDUSE.AGRICULTURE2020": {
        "title": "Occupation du sol agricole",
        "description": "Registre Parcellaire Graphique (RPG), cultures déclarées",
        "category": "Occupation du sol",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Agriculture, environnement, études territoriales",
        "update_frequency": "Annuelle"
    },
    "LANDCOVER.CORINELANDCOVER": {
        "title": "Corine Land Cover",
        "description": "Occupation du sol européenne, nomenclature CLC",
        "category": "Occupation du sol",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, aménagement, études européennes",
        "update_frequency": "Tous les 6 ans"
    }
}

# Couches WFS principales (données vectorielles)
WFS_LAYERS = {
    "ADMINEXPRESS-COG-CARTO.LATEST:commune": {
        "title": "Communes",
        "description": "Limites communales françaises (Code Officiel Géographique)",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "~36000",
        "attributes": ["nom", "code_insee", "population", "superficie", "code_postal"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Analyses territoriales, statistiques, cartographie administrative",
        "bbox_recommended": True,
        "update_frequency": "Annuelle"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:departement": {
        "title": "Départements",
        "description": "Limites départementales françaises",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "101",
        "attributes": ["nom", "code_insee", "nom_region", "superficie"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cartographie départementale, analyses régionales",
        "bbox_recommended": False,
        "update_frequency": "Annuelle"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:region": {
        "title": "Régions",
        "description": "Limites régionales françaises (nouvelles régions)",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "18",
        "attributes": ["nom", "code_insee", "chef_lieu", "superficie"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cartographie nationale, analyses macro-régionales",
        "bbox_recommended": False,
        "update_frequency": "Stable"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:epci": {
        "title": "EPCI (Intercommunalités)",
        "description": "Établissements Publics de Coopération Intercommunale",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "~1260",
        "attributes": ["nom", "code_siren", "nature", "population"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Gouvernance locale, intercommunalité",
        "bbox_recommended": True,
        "update_frequency": "Annuelle"
    },
    "BDTOPO_V3:batiment": {
        "title": "Bâtiments",
        "description": "Emprises bâties BD TOPO, bâtiments remarquables identifiés",
        "category": "Bâti",
        "geometry_type": "Polygon",
        "feature_count": "~50 millions",
        "attributes": ["nature", "usage_1", "usage_2", "hauteur", "nombre_etages", "etat"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Urbanisme, 3D, analyses urbaines, accessibilité",
        "bbox_recommended": True,
        "max_features_recommended": 5000,
        "update_frequency": "Continue (mise à jour glissante)"
    },
    "BDTOPO_V3:troncon_de_route": {
        "title": "Tronçons de route",
        "description": "Réseau routier BD TOPO avec attributs (importance, largeur, nom)",
        "category": "Réseaux",
        "geometry_type": "LineString",
        "feature_count": "~3 millions",
        "attributes": ["importance", "nature", "nom_voie", "largeur", "nb_voies", "sens"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Analyses de réseaux, navigation, accessibilité routière",
        "bbox_recommended": True,
        "max_features_recommended": 1000,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:surface_hydrographique": {
        "title": "Plans d'eau",
        "description": "Surfaces en eau (lacs, étangs, bassins)",
        "category": "Hydrographie",
        "geometry_type": "Polygon",
        "feature_count": "~150000",
        "attributes": ["nature", "nom", "superficie"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Hydrologie, environnement, risques inondation",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:troncon_de_cours_d_eau": {
        "title": "Cours d'eau",
        "description": "Réseau hydrographique linéaire (rivières, fleuves)",
        "category": "Hydrographie",
        "geometry_type": "LineString",
        "feature_count": "~500000",
        "attributes": ["nom", "classe", "largeur", "position_par_rapport_au_sol"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Bassins versants, hydrologie, environnement",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:zone_de_vegetation": {
        "title": "Zones de végétation",
        "description": "Zones arborées, forêts, haies",
        "category": "Végétation",
        "geometry_type": "Polygon",
        "feature_count": "~2 millions",
        "attributes": ["nature"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Environnement, biodiversité, foresterie",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle": {
        "title": "Parcelles cadastrales",
        "description": "Parcelles cadastrales Plan Cadastral Informatisé (PCI)",
        "category": "Cadastre",
        "geometry_type": "Polygon",
        "feature_count": "~100 millions",
        "attributes": ["numero", "section", "prefixe", "commune", "contenance"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Foncier, urbanisme, immobilier, fiscalité",
        "bbox_recommended": True,
        "max_features_recommended": 500,
        "update_frequency": "Trimestrielle"
    }
}

# Couches WMS principales (images à la demande) - mêmes que WMTS mais avec plus de flexibilité
WMS_LAYERS = WMTS_LAYERS.copy()

# Catégories pour filtrage
CATEGORIES = {
    "Cartes topographiques": ["GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "GEOGRAPHICALGRIDSYSTEMS.MAPS", "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR"],
    "Imagerie": ["ORTHOIMAGERY.ORTHOPHOTOS"],
    "Cadastre": ["CADASTRALPARCELS.PARCELLAIRE_EXPRESS"],
    "Altimétrie": ["ELEVATION.ELEVATIONGRIDCOVERAGE", "ELEVATION.SLOPES"],
    "Réseaux": ["TRANSPORTNETWORKS.ROADS"],
    "Occupation du sol": ["LANDUSE.AGRICULTURE2020", "LANDCOVER.CORINELANDCOVER"],
    "Découpage administratif": ["ADMINEXPRESS-COG-CARTO.LATEST:commune", "ADMINEXPRESS-COG-CARTO.LATEST:departement", "ADMINEXPRESS-COG-CARTO.LATEST:region", "ADMINEXPRESS-COG-CARTO.LATEST:epci"],
    "Bâti": ["BDTOPO_V3:batiment"],
    "Hydrographie": ["BDTOPO_V3:surface_hydrographique", "BDTOPO_V3:troncon_de_cours_d_eau"],
    "Végétation": ["BDTOPO_V3:zone_de_vegetation"]
}


def get_wmts_layer(layer_id: str) -> dict:
    """Récupérer les métadonnées d'une couche WMTS"""
    return WMTS_LAYERS.get(layer_id)


def get_wfs_layer(layer_id: str) -> dict:
    """Récupérer les métadonnées d'une couche WFS"""
    return WFS_LAYERS.get(layer_id)


def get_wms_layer(layer_id: str) -> dict:
    """Récupérer les métadonnées d'une couche WMS"""
    return WMS_LAYERS.get(layer_id)


def search_layers(query: str, service_type: str = "all") -> list:
    """
    Rechercher des couches par mots-clés
    service_type: "wmts", "wfs", "wms", "all"
    """
    query_lower = query.lower()
    results = []

    layers_to_search = []
    if service_type in ["wmts", "all"]:
        layers_to_search.extend([(k, v, "WMTS") for k, v in WMTS_LAYERS.items()])
    if service_type in ["wfs", "all"]:
        layers_to_search.extend([(k, v, "WFS") for k, v in WFS_LAYERS.items()])
    if service_type in ["wms", "all"]:
        layers_to_search.extend([(k, v, "WMS") for k, v in WMS_LAYERS.items()])

    for layer_id, metadata, svc in layers_to_search:
        # Recherche dans ID, title, description, category
        searchable = f"{layer_id} {metadata.get('title', '')} {metadata.get('description', '')} {metadata.get('category', '')}".lower()
        if query_lower in searchable:
            results.append({
                "service": svc,
                "id": layer_id,
                **metadata
            })

    return results


def get_layers_by_category(category: str, service_type: str = "all") -> list:
    """Récupérer toutes les couches d'une catégorie"""
    layer_ids = CATEGORIES.get(category, [])
    results = []

    for layer_id in layer_ids:
        if service_type in ["wmts", "all"] and layer_id in WMTS_LAYERS:
            results.append({"service": "WMTS", "id": layer_id, **WMTS_LAYERS[layer_id]})
        if service_type in ["wfs", "all"] and layer_id in WFS_LAYERS:
            results.append({"service": "WFS", "id": layer_id, **WFS_LAYERS[layer_id]})
        if service_type in ["wms", "all"] and layer_id in WMS_LAYERS:
            results.append({"service": "WMS", "id": layer_id, **WMS_LAYERS[layer_id]})

    return results


def get_all_categories() -> list:
    """Lister toutes les catégories disponibles"""
    return list(CATEGORIES.keys())
