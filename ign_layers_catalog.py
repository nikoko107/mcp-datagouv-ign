"""
Catalogue enrichi des couches IGN Géoplateforme
Mise à jour : 2025-01-26
Source : https://geoservices.ign.fr/documentation/donnees

Ce catalogue contient 40+ couches WMTS/WMS et 20+ couches WFS les plus utilisées
"""

# Couches WMTS principales (tuiles pré-générées) - 40+ couches
WMTS_LAYERS = {
    # === CARTES TOPOGRAPHIQUES ===
    "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2": {
        "title": "Plan IGN V2",
        "description": "Carte topographique vectorielle multi-échelles, style moderne, couleurs actuelles",
        "category": "Cartes topographiques",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Fond de carte général, navigation, contexte cartographique",
        "update_frequency": "Mensuelle"
    },
    "GEOGRAPHICALGRIDSYSTEMS.MAPS": {
        "title": "Cartes IGN",
        "description": "Cartes topographiques IGN multi-échelles (scan 25, 50, 100, 250)",
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
    "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-EXPRESS.STANDARD": {
        "title": "Scan Express Standard",
        "description": "Carte topographique simplifiée, style cartographique classique",
        "category": "Cartes topographiques",
        "formats": ["image/jpeg"],
        "min_zoom": 0,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Cartographie générale, consultation rapide",
        "update_frequency": "Annuelle"
    },
    "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-EXPRESS.CLASSIQUE": {
        "title": "Scan Express Classique",
        "description": "Style cartographique classique IGN, couleurs traditionnelles",
        "category": "Cartes topographiques",
        "formats": ["image/jpeg"],
        "min_zoom": 0,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Cartographie traditionnelle, nostalgie",
        "update_frequency": "Stable"
    },

    # === IMAGERIE ===
    "ORTHOIMAGERY.ORTHOPHOTOS": {
        "title": "Photographies aériennes",
        "description": "Orthophotographies IGN les plus récentes, résolution 20cm à 5m selon zones",
        "category": "Imagerie",
        "formats": ["image/jpeg", "image/png"],
        "min_zoom": 0,
        "max_zoom": 20,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Fond de carte réaliste, reconnaissance terrain, urbanisme, immobilier",
        "update_frequency": "Annuelle"
    },
    "ORTHOIMAGERY.ORTHOPHOTOS.IRC": {
        "title": "Orthophotos Infra-Rouge Couleur (IRC)",
        "description": "Photos aériennes en fausses couleurs (proche infra-rouge), végétation en rouge",
        "category": "Imagerie",
        "formats": ["image/jpeg"],
        "min_zoom": 13,
        "max_zoom": 19,
        "crs": ["PM", "LAMB93"],
        "usage": "Analyse végétation, agriculture, environnement, santé forêts",
        "update_frequency": "Variable"
    },
    "ORTHOIMAGERY.ORTHOPHOTOS.COAST2000": {
        "title": "Ortholittorale 2000",
        "description": "Orthophotographies du littoral français année 2000",
        "category": "Imagerie",
        "formats": ["image/jpeg"],
        "min_zoom": 13,
        "max_zoom": 19,
        "crs": ["PM"],
        "usage": "Évolution du littoral, études historiques, érosion côtière",
        "update_frequency": "Historique (2000)"
    },

    # === CADASTRE ===
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS": {
        "title": "Parcelles cadastrales (PCI)",
        "description": "Plan cadastral informatisé vecteur, parcelles et bâtiments cadastraux",
        "category": "Cadastre",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 20,
        "crs": ["PM", "LAMB93", "WGS84"],
        "usage": "Cadastre, urbanisme, foncier, immobilier, fiscalité",
        "update_frequency": "Trimestrielle"
    },

    # === ALTIMÉTRIE & RELIEF ===
    "ELEVATION.ELEVATIONGRIDCOVERAGE": {
        "title": "Altitudes (MNT colorisé)",
        "description": "Modèle Numérique de Terrain colorisé par tranches d'altitude (hypsométrie)",
        "category": "Altimétrie",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Visualisation relief, analyses altimétriques, cartes thématiques",
        "update_frequency": "Stable"
    },
    "ELEVATION.SLOPES": {
        "title": "Pentes du terrain",
        "description": "Visualisation des pentes en degrés (0-90°), gradient de couleur",
        "category": "Altimétrie",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Analyses de pentes, risques naturels, aménagement, ski",
        "update_frequency": "Stable"
    },
    "ELEVATION.LEVEL0": {
        "title": "Courbes de niveau (niveau 0)",
        "description": "Courbes de niveau principales, équidistance variable selon échelle",
        "category": "Altimétrie",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 17,
        "crs": ["PM", "LAMB93"],
        "usage": "Cartographie topographique, analyse relief, randonnée",
        "update_frequency": "Stable"
    },

    # === RÉSEAUX DE TRANSPORT ===
    "TRANSPORTNETWORKS.ROADS": {
        "title": "Réseau routier",
        "description": "Graphe routier avec classification (autoroutes, nationales, départementales)",
        "category": "Réseaux",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Navigation, analyses de réseaux, transport, logistique",
        "update_frequency": "Trimestrielle"
    },
    "TRANSPORTNETWORKS.RAILWAYS": {
        "title": "Réseau ferroviaire",
        "description": "Lignes ferroviaires (trains, tramways, métros)",
        "category": "Réseaux",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Transport ferroviaire, analyses de réseaux, aménagement",
        "update_frequency": "Annuelle"
    },
    "TRANSPORTNETWORKS.RUNWAYS": {
        "title": "Pistes aéroportuaires",
        "description": "Infrastructures aéroportuaires (pistes, aires de stationnement)",
        "category": "Réseaux",
        "formats": ["image/png"],
        "min_zoom": 10,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Aviation, aménagement aéroportuaire",
        "update_frequency": "Annuelle"
    },

    # === HYDROGRAPHIE ===
    "HYDROGRAPHY.HYDROGRAPHY": {
        "title": "Hydrographie",
        "description": "Réseau hydrographique complet (cours d'eau, plans d'eau, canaux)",
        "category": "Hydrographie",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Hydrologie, environnement, risques inondation, navigation fluviale",
        "update_frequency": "Continue"
    },

    # === OCCUPATION DU SOL ===
    "LANDUSE.AGRICULTURE2020": {
        "title": "Occupation du sol agricole 2020",
        "description": "Registre Parcellaire Graphique (RPG), cultures déclarées PAC",
        "category": "Occupation du sol",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Agriculture, environnement, études territoriales, PAC",
        "update_frequency": "Annuelle"
    },
    "LANDUSE.AGRICULTURE2021": {
        "title": "Occupation du sol agricole 2021",
        "description": "RPG 2021, évolution des cultures",
        "category": "Occupation du sol",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Agriculture, suivi temporel cultures",
        "update_frequency": "Annuelle"
    },
    "LANDCOVER.CORINELANDCOVER": {
        "title": "Corine Land Cover",
        "description": "Occupation du sol européenne, nomenclature CLC44 postes",
        "category": "Occupation du sol",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, aménagement, études européennes, changement climatique",
        "update_frequency": "Tous les 6 ans"
    },
    "LANDCOVER.FORESTINVENTORY.V2": {
        "title": "Inventaire forestier V2",
        "description": "Couverture forestière, types de peuplements",
        "category": "Occupation du sol",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Foresterie, biodiversité, gestion forestière",
        "update_frequency": "Tous les 5 ans"
    },

    # === ADMINISTRATIF ===
    "ADMINISTRATIVEUNITS.BOUNDARIES": {
        "title": "Limites administratives",
        "description": "Limites des unités administratives (communes, départements, régions)",
        "category": "Administratif",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Cartographie administrative, statistiques territoriales",
        "update_frequency": "Annuelle"
    },

    # === BÂTI ===
    "BUILDINGS.BUILDINGS": {
        "title": "Bâtiments",
        "description": "Emprises bâties simplifiées",
        "category": "Bâti",
        "formats": ["image/png"],
        "min_zoom": 14,
        "max_zoom": 18,
        "crs": ["PM", "LAMB93"],
        "usage": "Urbanisme, densité bâtie, 3D",
        "update_frequency": "Continue"
    },

    # === ZONES PROTÉGÉES & ENVIRONNEMENT ===
    "PROTECTEDAREAS.SIC": {
        "title": "Sites d'Importance Communautaire (Natura 2000)",
        "description": "Zones SIC Natura 2000, protection habitats naturels",
        "category": "Environnement",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, biodiversité, contraintes aménagement",
        "update_frequency": "Annuelle"
    },
    "PROTECTEDAREAS.ZPS": {
        "title": "Zones de Protection Spéciale (Natura 2000)",
        "description": "Zones ZPS Natura 2000, protection oiseaux",
        "category": "Environnement",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, ornithologie, contraintes aménagement",
        "update_frequency": "Annuelle"
    },
    "PROTECTEDAREAS.PN": {
        "title": "Parcs Nationaux",
        "description": "Périmètres des parcs nationaux français",
        "category": "Environnement",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, tourisme, réglementation",
        "update_frequency": "Annuelle"
    },
    "PROTECTEDAREAS.PNR": {
        "title": "Parcs Naturels Régionaux",
        "description": "Périmètres des PNR",
        "category": "Environnement",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, tourisme, développement durable",
        "update_frequency": "Annuelle"
    },
    "PROTECTEDAREAS.RN": {
        "title": "Réserves Naturelles",
        "description": "Réserves naturelles nationales et régionales",
        "category": "Environnement",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 16,
        "crs": ["PM", "LAMB93"],
        "usage": "Environnement, biodiversité, protection stricte",
        "update_frequency": "Annuelle"
    },

    # === RISQUES ===
    "GEOGRAPHICALGRIDSYSTEMS.SLOPES.MOUNTAIN": {
        "title": "Zones de montagne (pentes)",
        "description": "Délimitation des zones de montagne selon pentes",
        "category": "Risques",
        "formats": ["image/png"],
        "min_zoom": 6,
        "max_zoom": 14,
        "crs": ["PM", "LAMB93"],
        "usage": "Aménagement montagne, risques avalanches",
        "update_frequency": "Stable"
    },

    # === GÉOLOGIE ===
    "GEOLOGY.GEOLOGY": {
        "title": "Géologie",
        "description": "Carte géologique harmonisée à 1/1M",
        "category": "Géologie",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 13,
        "crs": ["PM", "LAMB93"],
        "usage": "Géologie, pédologie, ressources naturelles, enseignement",
        "update_frequency": "Stable"
    },

    # === LIMITES MARITIME ===
    "LIMITES.MARITIME": {
        "title": "Limites maritimes",
        "description": "Zones maritimes françaises (eaux territoriales, ZEE)",
        "category": "Maritime",
        "formats": ["image/png"],
        "min_zoom": 0,
        "max_zoom": 12,
        "crs": ["PM", "LAMB93"],
        "usage": "Droit maritime, pêche, ressources marines",
        "update_frequency": "Stable"
    },

    # === DONNÉES HISTORIQUES ===
    "GEOGRAPHICALGRIDSYSTEMS.CASSINI": {
        "title": "Carte de Cassini (XVIIIe siècle)",
        "description": "Première carte topographique générale de France (1750-1815)",
        "category": "Historique",
        "formats": ["image/jpeg"],
        "min_zoom": 6,
        "max_zoom": 15,
        "crs": ["PM"],
        "usage": "Histoire, patrimoine, évolution territoriale, généalogie",
        "update_frequency": "Historique"
    },
    "GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40": {
        "title": "Carte d'État-Major (1820-1866)",
        "description": "Carte d'État-Major 1:40000, première cartographie précise de France",
        "category": "Historique",
        "formats": ["image/jpeg"],
        "min_zoom": 6,
        "max_zoom": 15,
        "crs": ["PM"],
        "usage": "Histoire, évolution paysages, urbanisme historique",
        "update_frequency": "Historique"
    },

    # === DONNÉES INTERNATIONALES ===
    "GEOGRAPHICALGRIDSYSTEMS.WORLD-SRTM": {
        "title": "SRTM Monde",
        "description": "Modèle numérique de terrain mondial SRTM (90m)",
        "category": "Altimétrie",
        "formats": ["image/jpeg"],
        "min_zoom": 0,
        "max_zoom": 14,
        "crs": ["PM"],
        "usage": "Relief mondial, analyses globales",
        "update_frequency": "Historique (2000)"
    }
}

# Couches WFS principales (données vectorielles) - 25+ couches
WFS_LAYERS = {
    # === DÉCOUPAGE ADMINISTRATIF ===
    "ADMINEXPRESS-COG-CARTO.LATEST:commune": {
        "title": "Communes",
        "description": "Limites communales françaises (Code Officiel Géographique)",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "~36000",
        "attributes": ["nom", "code_insee", "population", "superficie", "code_postal", "code_region", "code_departement"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Analyses territoriales, statistiques, cartographie administrative, élections",
        "bbox_recommended": True,
        "max_features_recommended": 500,
        "update_frequency": "Annuelle"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:departement": {
        "title": "Départements",
        "description": "Limites départementales françaises",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "101",
        "attributes": ["nom", "code_insee", "nom_region", "code_region", "superficie"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cartographie départementale, analyses régionales, statistiques",
        "bbox_recommended": False,
        "update_frequency": "Annuelle"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:region": {
        "title": "Régions",
        "description": "Limites régionales françaises (nouvelles régions 2016)",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "18",
        "attributes": ["nom", "code_insee", "chef_lieu", "superficie"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cartographie nationale, analyses macro-régionales, politiques publiques",
        "bbox_recommended": False,
        "update_frequency": "Stable"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:epci": {
        "title": "EPCI (Intercommunalités)",
        "description": "Établissements Publics de Coopération Intercommunale (métropoles, agglos, communautés de communes)",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "~1260",
        "attributes": ["nom", "code_siren", "nature", "population", "nb_communes"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Gouvernance locale, intercommunalité, compétences territoriales",
        "bbox_recommended": True,
        "update_frequency": "Annuelle"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:arrondissement": {
        "title": "Arrondissements",
        "description": "Arrondissements départementaux",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "~330",
        "attributes": ["nom", "code_insee", "code_departement"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Découpage administratif fin, élections",
        "bbox_recommended": True,
        "update_frequency": "Annuelle"
    },
    "ADMINEXPRESS-COG-CARTO.LATEST:canton": {
        "title": "Cantons",
        "description": "Cantons (circonscriptions électorales départementales)",
        "category": "Découpage administratif",
        "geometry_type": "Polygon",
        "feature_count": "~2000",
        "attributes": ["nom", "code_insee", "code_departement"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Élections départementales, découpage électoral",
        "bbox_recommended": True,
        "update_frequency": "Stable"
    },

    # === BÂTI (BD TOPO V3) ===
    "BDTOPO_V3:batiment": {
        "title": "Bâtiments",
        "description": "Emprises bâties BD TOPO, bâtiments remarquables identifiés (mairies, églises, etc.)",
        "category": "Bâti",
        "geometry_type": "Polygon",
        "feature_count": "~50 millions",
        "attributes": ["nature", "usage_1", "usage_2", "hauteur", "nombre_etages", "etat", "leger", "nom"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Urbanisme, modélisation 3D, analyses urbaines, accessibilité, patrimoine",
        "bbox_recommended": True,
        "max_features_recommended": 5000,
        "update_frequency": "Continue (mise à jour glissante)"
    },
    "BDTOPO_V3:construction_surfacique": {
        "title": "Constructions surfaciques",
        "description": "Constructions non bâties (réservoirs, tribunes, péages, etc.)",
        "category": "Bâti",
        "geometry_type": "Polygon",
        "feature_count": "~500000",
        "attributes": ["nature", "hauteur"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Infrastructures, équipements publics",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:construction_lineaire": {
        "title": "Constructions linéaires",
        "description": "Constructions linéaires (murs, digues, quais)",
        "category": "Bâti",
        "geometry_type": "LineString",
        "feature_count": "~1 million",
        "attributes": ["nature"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Infrastructures linéaires, protection",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },

    # === RÉSEAUX ROUTIERS ===
    "BDTOPO_V3:troncon_de_route": {
        "title": "Tronçons de route",
        "description": "Réseau routier BD TOPO avec attributs détaillés (importance, largeur, nom)",
        "category": "Réseaux",
        "geometry_type": "LineString",
        "feature_count": "~3 millions",
        "attributes": ["importance", "nature", "nom_voie_gauche", "nom_voie_droite", "largeur_de_chaussee", "nb_voies", "sens_de_circulation", "vitesse_moyenne_vl"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Analyses de réseaux, navigation, accessibilité routière, trafic",
        "bbox_recommended": True,
        "max_features_recommended": 1000,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:noeud_routier": {
        "title": "Nœuds routiers",
        "description": "Intersections et échangeurs routiers",
        "category": "Réseaux",
        "geometry_type": "Point",
        "feature_count": "~2 millions",
        "attributes": ["nature"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Graphes routiers, analyses de réseaux",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },

    # === RÉSEAUX FERRÉS ===
    "BDTOPO_V3:troncon_de_voie_ferree": {
        "title": "Tronçons de voie ferrée",
        "description": "Réseau ferroviaire (trains, tramways, métros)",
        "category": "Réseaux",
        "geometry_type": "LineString",
        "feature_count": "~100000",
        "attributes": ["nature", "nombre_de_voies", "electrifie", "largeur"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Transport ferroviaire, analyses de réseaux, aménagement",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },

    # === HYDROGRAPHIE ===
    "BDTOPO_V3:surface_hydrographique": {
        "title": "Plans d'eau",
        "description": "Surfaces en eau (lacs, étangs, bassins, mers)",
        "category": "Hydrographie",
        "geometry_type": "Polygon",
        "feature_count": "~150000",
        "attributes": ["nature", "nom", "superficie"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Hydrologie, environnement, risques inondation, loisirs nautiques",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:troncon_de_cours_d_eau": {
        "title": "Cours d'eau",
        "description": "Réseau hydrographique linéaire (rivières, fleuves, canaux)",
        "category": "Hydrographie",
        "geometry_type": "LineString",
        "feature_count": "~500000",
        "attributes": ["nom", "classe", "largeur", "position_par_rapport_au_sol", "sens_de_ecoulement"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Bassins versants, hydrologie, environnement, navigation fluviale",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },

    # === VÉGÉTATION ===
    "BDTOPO_V3:zone_de_vegetation": {
        "title": "Zones de végétation",
        "description": "Zones arborées, forêts, haies, vignes, vergers",
        "category": "Végétation",
        "geometry_type": "Polygon",
        "feature_count": "~2 millions",
        "attributes": ["nature"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Environnement, biodiversité, foresterie, agriculture",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },

    # === ÉQUIPEMENTS ===
    "BDTOPO_V3:reservoir": {
        "title": "Réservoirs",
        "description": "Réservoirs et châteaux d'eau",
        "category": "Équipements",
        "geometry_type": "Point",
        "feature_count": "~20000",
        "attributes": ["nature", "hauteur"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Réseaux d'eau, infrastructures",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },
    "BDTOPO_V3:pylone": {
        "title": "Pylônes",
        "description": "Pylônes électriques et télécommunications",
        "category": "Équipements",
        "geometry_type": "Point",
        "feature_count": "~150000",
        "attributes": ["nature", "hauteur"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Réseaux électriques, télécoms",
        "bbox_recommended": True,
        "update_frequency": "Continue"
    },

    # === CADASTRE ===
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle": {
        "title": "Parcelles cadastrales",
        "description": "Parcelles cadastrales Plan Cadastral Informatisé (PCI Vecteur)",
        "category": "Cadastre",
        "geometry_type": "Polygon",
        "feature_count": "~100 millions",
        "attributes": ["numero", "section", "prefixe", "commune", "contenance", "idu"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Foncier, urbanisme, immobilier, fiscalité, notariat",
        "bbox_recommended": True,
        "max_features_recommended": 500,
        "update_frequency": "Trimestrielle"
    },
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:commune": {
        "title": "Communes cadastrales",
        "description": "Limites communales cadastrales",
        "category": "Cadastre",
        "geometry_type": "Polygon",
        "feature_count": "~36000",
        "attributes": ["nom", "code_insee"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cadastre, référentiel administratif",
        "bbox_recommended": True,
        "update_frequency": "Trimestrielle"
    },
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:section": {
        "title": "Sections cadastrales",
        "description": "Sections cadastrales (subdivisions communales)",
        "category": "Cadastre",
        "geometry_type": "Polygon",
        "feature_count": "~600000",
        "attributes": ["code_section", "commune"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cadastre, découpage foncier",
        "bbox_recommended": True,
        "update_frequency": "Trimestrielle"
    },
    "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:batiment": {
        "title": "Bâtiments cadastraux",
        "description": "Emprises bâties cadastrales (simplifié)",
        "category": "Cadastre",
        "geometry_type": "Polygon",
        "feature_count": "~50 millions",
        "attributes": ["commune", "section"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Cadastre, bâti fiscal",
        "bbox_recommended": True,
        "max_features_recommended": 5000,
        "update_frequency": "Trimestrielle"
    },

    # === ADRESSES (BAN) ===
    "ADRESSE.BAN:adresse": {
        "title": "Adresses (Base Adresse Nationale)",
        "description": "Points adresses géolocalisés BAN",
        "category": "Adresses",
        "geometry_type": "Point",
        "feature_count": "~26 millions",
        "attributes": ["numero", "rep", "nom_voie", "code_postal", "nom_commune", "code_insee"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Géocodage, adressage, navigation, logistique, secours",
        "bbox_recommended": True,
        "max_features_recommended": 1000,
        "update_frequency": "Continue"
    },

    # === ZONES PROTÉGÉES ===
    "PROTECTEDAREAS:protectedarea": {
        "title": "Aires protégées",
        "description": "Zones de protection environnementale (tous types)",
        "category": "Environnement",
        "geometry_type": "Polygon",
        "feature_count": "~8000",
        "attributes": ["nom", "type", "statut", "date_creation"],
        "crs": ["EPSG:4326", "EPSG:2154", "EPSG:3857"],
        "usage": "Environnement, biodiversité, contraintes aménagement, tourisme",
        "bbox_recommended": True,
        "update_frequency": "Annuelle"
    }
}

# Couches WMS principales (images à la demande) - mêmes que WMTS mais avec plus de flexibilité
WMS_LAYERS = WMTS_LAYERS.copy()

# Catégories pour filtrage enrichies
CATEGORIES = {
    "Cartes topographiques": [
        "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2",
        "GEOGRAPHICALGRIDSYSTEMS.MAPS",
        "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR",
        "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-EXPRESS.STANDARD",
        "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-EXPRESS.CLASSIQUE"
    ],
    "Imagerie": [
        "ORTHOIMAGERY.ORTHOPHOTOS",
        "ORTHOIMAGERY.ORTHOPHOTOS.IRC",
        "ORTHOIMAGERY.ORTHOPHOTOS.COAST2000"
    ],
    "Cadastre": [
        "CADASTRALPARCELS.PARCELLAIRE_EXPRESS",
        "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle",
        "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:commune",
        "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:section",
        "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:batiment"
    ],
    "Altimétrie": [
        "ELEVATION.ELEVATIONGRIDCOVERAGE",
        "ELEVATION.SLOPES",
        "ELEVATION.LEVEL0",
        "GEOGRAPHICALGRIDSYSTEMS.WORLD-SRTM",
        "GEOGRAPHICALGRIDSYSTEMS.SLOPES.MOUNTAIN"
    ],
    "Réseaux": [
        "TRANSPORTNETWORKS.ROADS",
        "TRANSPORTNETWORKS.RAILWAYS",
        "TRANSPORTNETWORKS.RUNWAYS",
        "BDTOPO_V3:troncon_de_route",
        "BDTOPO_V3:noeud_routier",
        "BDTOPO_V3:troncon_de_voie_ferree"
    ],
    "Occupation du sol": [
        "LANDUSE.AGRICULTURE2020",
        "LANDUSE.AGRICULTURE2021",
        "LANDCOVER.CORINELANDCOVER",
        "LANDCOVER.FORESTINVENTORY.V2"
    ],
    "Découpage administratif": [
        "ADMINISTRATIVEUNITS.BOUNDARIES",
        "ADMINEXPRESS-COG-CARTO.LATEST:commune",
        "ADMINEXPRESS-COG-CARTO.LATEST:departement",
        "ADMINEXPRESS-COG-CARTO.LATEST:region",
        "ADMINEXPRESS-COG-CARTO.LATEST:epci",
        "ADMINEXPRESS-COG-CARTO.LATEST:arrondissement",
        "ADMINEXPRESS-COG-CARTO.LATEST:canton"
    ],
    "Bâti": [
        "BUILDINGS.BUILDINGS",
        "BDTOPO_V3:batiment",
        "BDTOPO_V3:construction_surfacique",
        "BDTOPO_V3:construction_lineaire"
    ],
    "Hydrographie": [
        "HYDROGRAPHY.HYDROGRAPHY",
        "BDTOPO_V3:surface_hydrographique",
        "BDTOPO_V3:troncon_de_cours_d_eau"
    ],
    "Végétation": [
        "BDTOPO_V3:zone_de_vegetation"
    ],
    "Environnement": [
        "PROTECTEDAREAS.SIC",
        "PROTECTEDAREAS.ZPS",
        "PROTECTEDAREAS.PN",
        "PROTECTEDAREAS.PNR",
        "PROTECTEDAREAS.RN",
        "PROTECTEDAREAS:protectedarea"
    ],
    "Historique": [
        "GEOGRAPHICALGRIDSYSTEMS.CASSINI",
        "GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40"
    ],
    "Maritime": [
        "LIMITES.MARITIME"
    ],
    "Géologie": [
        "GEOLOGY.GEOLOGY"
    ],
    "Équipements": [
        "BDTOPO_V3:reservoir",
        "BDTOPO_V3:pylone"
    ],
    "Adresses": [
        "ADRESSE.BAN:adresse"
    ],
    "Risques": [
        "GEOGRAPHICALGRIDSYSTEMS.SLOPES.MOUNTAIN"
    ]
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


def get_catalog_stats() -> dict:
    """Statistiques du catalogue"""
    return {
        "wmts_layers_count": len(WMTS_LAYERS),
        "wfs_layers_count": len(WFS_LAYERS),
        "wms_layers_count": len(WMS_LAYERS),
        "categories_count": len(CATEGORIES),
        "total_layers": len(WMTS_LAYERS) + len(WFS_LAYERS),
        "version": "1.4.2",
        "last_update": "2025-01-26"
    }
