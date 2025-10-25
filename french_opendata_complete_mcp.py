#!/usr/bin/env python3
"""
Serveur MCP complet pour data.gouv.fr + 4 APIs nationales françaises
- data.gouv.fr : Données publiques
- IGN Géoplateforme : Cartographie (WMTS, WMS, WFS)
- API Adresse : Géocodage national
- API Geo : Découpage administratif
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, quote

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from ign_geo_services import IGNGeoServices

# Configuration
API_BASE_URL = "https://www.data.gouv.fr/api/1"
API_ADRESSE_URL = "https://api-adresse.data.gouv.fr"
API_GEO_URL = "https://geo.api.gouv.fr"
API_KEY = os.getenv("DATAGOUV_API_KEY", "")

# Initialisation
app = Server("french-opendata-complete-mcp")
ign_services = IGNGeoServices()


# ============================================================================
# TOOLS - DATA.GOUV.FR
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Liste tous les outils disponibles"""
    return [
        # DATA.GOUV.FR (6 outils)
        Tool(
            name="search_datasets",
            description="Rechercher des jeux de données sur data.gouv.fr avec filtres avancés",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Requête de recherche"},
                    "organization": {"type": "string", "description": "Filtrer par organisation"},
                    "tag": {"type": "string", "description": "Filtrer par tag"},
                    "page_size": {"type": "integer", "default": 20, "description": "Nombre de résultats (max 100)"},
                },
                "required": ["q"],
            },
        ),
        Tool(
            name="get_dataset",
            description="Obtenir les détails complets d'un dataset par son ID ou slug",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "ID ou slug du dataset"},
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="search_organizations",
            description="Rechercher des organisations publiques sur data.gouv.fr",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Nom de l'organisation"},
                    "page_size": {"type": "integer", "default": 20},
                },
                "required": ["q"],
            },
        ),
        Tool(
            name="get_organization",
            description="Obtenir les détails d'une organisation",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "ID ou slug de l'organisation"},
                },
                "required": ["org_id"],
            },
        ),
        Tool(
            name="search_reuses",
            description="Rechercher des réutilisations (applications, visualisations) de données",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Requête de recherche"},
                    "page_size": {"type": "integer", "default": 20},
                },
                "required": ["q"],
            },
        ),
        Tool(
            name="get_dataset_resources",
            description="Lister les ressources (fichiers) d'un dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "ID du dataset"},
                },
                "required": ["dataset_id"],
            },
        ),
        
        # IGN GÉOPLATEFORME (11 outils)
        Tool(
            name="list_wmts_layers",
            description="Lister toutes les couches cartographiques WMTS disponibles (tuiles pré-générées)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="search_wmts_layers",
            description="Rechercher des couches WMTS par mots-clés (ex: 'orthophoto', 'cadastre', 'admin')",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mots-clés de recherche"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_wmts_tile_url",
            description="Générer l'URL d'une tuile WMTS pour intégration dans une application",
            inputSchema={
                "type": "object",
                "properties": {
                    "layer": {"type": "string", "description": "Nom de la couche"},
                    "z": {"type": "integer", "description": "Niveau de zoom (0-20)"},
                    "x": {"type": "integer", "description": "Coordonnée X de la tuile"},
                    "y": {"type": "integer", "description": "Coordonnée Y de la tuile"},
                },
                "required": ["layer", "z", "x", "y"],
            },
        ),
        Tool(
            name="list_wms_layers",
            description="Lister toutes les couches WMS disponibles (cartes à la demande)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="search_wms_layers",
            description="Rechercher des couches WMS par mots-clés",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mots-clés de recherche"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_wms_map_url",
            description="Générer l'URL d'une carte WMS personnalisée (bbox, taille, format)",
            inputSchema={
                "type": "object",
                "properties": {
                    "layers": {"type": "string", "description": "Couches séparées par des virgules"},
                    "bbox": {"type": "string", "description": "Bbox format: minx,miny,maxx,maxy (EPSG:4326)"},
                    "width": {"type": "integer", "default": 800, "description": "Largeur en pixels"},
                    "height": {"type": "integer", "default": 600, "description": "Hauteur en pixels"},
                    "format": {"type": "string", "default": "image/png", "description": "Format d'image"},
                },
                "required": ["layers", "bbox"],
            },
        ),
        Tool(
            name="list_wfs_features",
            description="Lister tous les types de features WFS (données vectorielles)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="search_wfs_features",
            description="Rechercher des features WFS par mots-clés",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mots-clés de recherche"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_wfs_features",
            description="Récupérer des données vectorielles WFS (GeoJSON)",
            inputSchema={
                "type": "object",
                "properties": {
                    "typename": {"type": "string", "description": "Type de feature"},
                    "bbox": {"type": "string", "description": "Bbox optionnel"},
                    "max_features": {"type": "integer", "default": 100},
                },
                "required": ["typename"],
            },
        ),
        Tool(
            name="calculate_route",
            description="Calculer un itinéraire entre deux points avec l'API IGN Navigation (voiture, piéton, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_lon": {"type": "number", "description": "Longitude du point de départ"},
                    "start_lat": {"type": "number", "description": "Latitude du point de départ"},
                    "end_lon": {"type": "number", "description": "Longitude du point d'arrivée"},
                    "end_lat": {"type": "number", "description": "Latitude du point d'arrivée"},
                    "resource": {
                        "type": "string",
                        "default": "bdtopo-valhalla",
                        "description": "Moteur de calcul (bdtopo-valhalla, bdtopo-osrm, bdtopo-pgr)"
                    },
                    "profile": {
                        "type": "string",
                        "default": "car",
                        "description": "Profil de déplacement (car, pedestrian)"
                    },
                    "optimization": {
                        "type": "string",
                        "default": "fastest",
                        "description": "Type d'optimisation (fastest, shortest)"
                    },
                    "get_steps": {
                        "type": "boolean",
                        "default": True,
                        "description": "Retourner les instructions détaillées"
                    },
                    "intermediates": {
                        "type": "string",
                        "description": "Points intermédiaires (format: lon1,lat1|lon2,lat2)"
                    },
                    "constraints": {
                        "type": "string",
                        "description": "Contraintes de voyage (ex: avoidTolls, avoidHighways)"
                    }
                },
                "required": ["start_lon", "start_lat", "end_lon", "end_lat"],
            },
        ),
        Tool(
            name="calculate_isochrone",
            description="Calculer une zone accessible depuis un point en un temps donné (isochrone) ou une distance donnée (isodistance)",
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {"type": "number", "description": "Longitude du point de référence"},
                    "lat": {"type": "number", "description": "Latitude du point de référence"},
                    "cost_value": {
                        "type": "integer",
                        "description": "Valeur de coût : temps en secondes pour isochrone (ex: 600 = 10min) ou distance en mètres pour isodistance"
                    },
                    "resource": {
                        "type": "string",
                        "default": "bdtopo-valhalla",
                        "description": "Moteur de calcul (bdtopo-valhalla, bdtopo-osrm, bdtopo-pgr)"
                    },
                    "profile": {
                        "type": "string",
                        "default": "car",
                        "description": "Profil de déplacement (car, pedestrian)"
                    },
                    "cost_type": {
                        "type": "string",
                        "default": "time",
                        "description": "Type de coût (time pour isochrone, distance pour isodistance)"
                    },
                    "direction": {
                        "type": "string",
                        "default": "departure",
                        "description": "Direction (departure: zone accessible depuis le point, arrival: zone depuis laquelle on peut rejoindre le point)"
                    },
                    "constraints": {
                        "type": "string",
                        "description": "Contraintes de voyage (ex: avoidTolls, avoidHighways)"
                    }
                },
                "required": ["lon", "lat", "cost_value"],
            },
        ),

        # API ADRESSE (3 outils)
        Tool(
            name="geocode_address",
            description="Convertir une adresse en coordonnées GPS (géocodage)",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "Adresse à géocoder"},
                    "limit": {"type": "integer", "default": 5, "description": "Nombre de résultats"},
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="reverse_geocode",
            description="Convertir des coordonnées GPS en adresse (géocodage inverse)",
            inputSchema={
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude"},
                    "lon": {"type": "number", "description": "Longitude"},
                },
                "required": ["lat", "lon"],
            },
        ),
        Tool(
            name="search_addresses",
            description="Autocomplétion d'adresses pour formulaires",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Début d'adresse"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["q"],
            },
        ),
        
        # API GEO (6 outils)
        Tool(
            name="search_communes",
            description="Rechercher des communes par nom ou code postal",
            inputSchema={
                "type": "object",
                "properties": {
                    "nom": {"type": "string", "description": "Nom de la commune"},
                    "code_postal": {"type": "string", "description": "Code postal"},
                    "fields": {"type": "string", "default": "nom,code,codesPostaux,population", "description": "Champs à retourner"},
                },
            },
        ),
        Tool(
            name="get_commune_info",
            description="Obtenir toutes les informations d'une commune (population, département, région)",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code INSEE de la commune"},
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="get_departement_communes",
            description="Lister toutes les communes d'un département",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code du département (ex: 75, 2A)"},
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="search_departements",
            description="Rechercher des départements",
            inputSchema={
                "type": "object",
                "properties": {
                    "nom": {"type": "string", "description": "Nom du département"},
                },
            },
        ),
        Tool(
            name="search_regions",
            description="Rechercher des régions",
            inputSchema={
                "type": "object",
                "properties": {
                    "nom": {"type": "string", "description": "Nom de la région"},
                },
            },
        ),
        Tool(
            name="get_region_info",
            description="Obtenir les informations détaillées d'une région",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code de la région"},
                },
                "required": ["code"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Exécute un outil"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # ====================================================================
        # DATA.GOUV.FR
        # ====================================================================
        
        if name == "search_datasets":
            params = {
                "q": arguments["q"],
                "page_size": arguments.get("page_size", 20),
            }
            if "organization" in arguments:
                params["organization"] = arguments["organization"]
            if "tag" in arguments:
                params["tag"] = arguments["tag"]
                
            response = await client.get(f"{API_BASE_URL}/datasets/", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for ds in data.get("data", []):
                results.append({
                    "title": ds.get("title"),
                    "id": ds.get("id"),
                    "slug": ds.get("slug"),
                    "description": ds.get("description", "")[:200],
                    "organization": ds.get("organization", {}).get("name"),
                    "url": f"https://www.data.gouv.fr/fr/datasets/{ds.get('slug')}/",
                })
            
            return [TextContent(
                type="text",
                text=json.dumps({"total": data.get("total"), "results": results}, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_dataset":
            dataset_id = arguments["dataset_id"]
            response = await client.get(f"{API_BASE_URL}/datasets/{dataset_id}/")
            response.raise_for_status()
            data = response.json()
            
            result = {
                "title": data.get("title"),
                "description": data.get("description"),
                "url": f"https://www.data.gouv.fr/fr/datasets/{data.get('slug')}/",
                "organization": data.get("organization", {}).get("name"),
                "tags": data.get("tags", []),
                "license": data.get("license"),
                "frequency": data.get("frequency"),
                "resources_count": len(data.get("resources", [])),
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "search_organizations":
            params = {"q": arguments["q"], "page_size": arguments.get("page_size", 20)}
            response = await client.get(f"{API_BASE_URL}/organizations/", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for org in data.get("data", []):
                results.append({
                    "name": org.get("name"),
                    "id": org.get("id"),
                    "slug": org.get("slug"),
                    "url": f"https://www.data.gouv.fr/fr/organizations/{org.get('slug')}/",
                })
            
            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
        
        elif name == "get_organization":
            org_id = arguments["org_id"]
            response = await client.get(f"{API_BASE_URL}/organizations/{org_id}/")
            response.raise_for_status()
            data = response.json()
            
            result = {
                "name": data.get("name"),
                "description": data.get("description"),
                "url": f"https://www.data.gouv.fr/fr/organizations/{data.get('slug')}/",
                "datasets_count": data.get("metrics", {}).get("datasets"),
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "search_reuses":
            params = {"q": arguments["q"], "page_size": arguments.get("page_size", 20)}
            response = await client.get(f"{API_BASE_URL}/reuses/", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for reuse in data.get("data", []):
                results.append({
                    "title": reuse.get("title"),
                    "url": reuse.get("url"),
                    "type": reuse.get("type"),
                })
            
            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
        
        elif name == "get_dataset_resources":
            dataset_id = arguments["dataset_id"]
            response = await client.get(f"{API_BASE_URL}/datasets/{dataset_id}/")
            response.raise_for_status()
            data = response.json()
            
            resources = []
            for res in data.get("resources", []):
                resources.append({
                    "title": res.get("title"),
                    "url": res.get("url"),
                    "format": res.get("format"),
                    "filesize": res.get("filesize"),
                })
            
            return [TextContent(type="text", text=json.dumps(resources, ensure_ascii=False, indent=2))]
        
        # ====================================================================
        # IGN GÉOPLATEFORME
        # ====================================================================
        
        elif name == "list_wmts_layers":
            layers = await ign_services.list_wmts_layers(client)
            return [TextContent(type="text", text=json.dumps(layers, ensure_ascii=False, indent=2))]
        
        elif name == "search_wmts_layers":
            query = arguments["query"]
            layers = await ign_services.search_layers(client, "wmts", query)
            return [TextContent(type="text", text=json.dumps(layers, ensure_ascii=False, indent=2))]
        
        elif name == "get_wmts_tile_url":
            url = ign_services.get_wmts_tile_url(
                arguments["layer"],
                arguments["z"],
                arguments["x"],
                arguments["y"]
            )
            return [TextContent(type="text", text=json.dumps({"url": url}, indent=2))]
        
        elif name == "list_wms_layers":
            layers = await ign_services.list_wms_layers(client)
            return [TextContent(type="text", text=json.dumps(layers, ensure_ascii=False, indent=2))]
        
        elif name == "search_wms_layers":
            query = arguments["query"]
            layers = await ign_services.search_layers(client, "wms", query)
            return [TextContent(type="text", text=json.dumps(layers, ensure_ascii=False, indent=2))]
        
        elif name == "get_wms_map_url":
            url = ign_services.get_wms_map_url(
                arguments["layers"],
                arguments["bbox"],
                arguments.get("width", 800),
                arguments.get("height", 600),
                arguments.get("format", "image/png")
            )
            return [TextContent(type="text", text=json.dumps({"url": url}, indent=2))]
        
        elif name == "list_wfs_features":
            features = await ign_services.list_wfs_features(client)
            return [TextContent(type="text", text=json.dumps(features, ensure_ascii=False, indent=2))]
        
        elif name == "search_wfs_features":
            query = arguments["query"]
            features = await ign_services.search_layers(client, "wfs", query)
            return [TextContent(type="text", text=json.dumps(features, ensure_ascii=False, indent=2))]
        
        elif name == "get_wfs_features":
            typename = arguments["typename"]
            bbox = arguments.get("bbox")
            max_features = arguments.get("max_features", 100)
            
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typename": typename,
                "outputFormat": "application/json",
                "count": max_features,
            }
            if bbox:
                params["bbox"] = bbox
            
            response = await client.get(ign_services.WFS_URL, params=params)
            response.raise_for_status()
            data = response.json()

            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

        elif name == "calculate_route":
            result = await ign_services.calculate_route(
                client,
                start_lon=arguments["start_lon"],
                start_lat=arguments["start_lat"],
                end_lon=arguments["end_lon"],
                end_lat=arguments["end_lat"],
                resource=arguments.get("resource", "bdtopo-valhalla"),
                profile=arguments.get("profile", "car"),
                optimization=arguments.get("optimization", "fastest"),
                get_steps=arguments.get("get_steps", True),
                intermediates=arguments.get("intermediates"),
                constraints=arguments.get("constraints")
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "calculate_isochrone":
            result = await ign_services.calculate_isochrone(
                client,
                lon=arguments["lon"],
                lat=arguments["lat"],
                cost_value=arguments["cost_value"],
                resource=arguments.get("resource", "bdtopo-valhalla"),
                profile=arguments.get("profile", "car"),
                cost_type=arguments.get("cost_type", "time"),
                direction=arguments.get("direction", "departure"),
                constraints=arguments.get("constraints")
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        # ====================================================================
        # API ADRESSE
        # ====================================================================
        
        elif name == "geocode_address":
            params = {
                "q": arguments["address"],
                "limit": arguments.get("limit", 5),
            }
            response = await client.get(f"{API_ADRESSE_URL}/search/", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])
                results.append({
                    "label": props.get("label"),
                    "score": props.get("score"),
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "type": props.get("type"),
                    "city": props.get("city"),
                    "postcode": props.get("postcode"),
                })
            
            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
        
        elif name == "reverse_geocode":
            params = {
                "lat": arguments["lat"],
                "lon": arguments["lon"],
            }
            response = await client.get(f"{API_ADRESSE_URL}/reverse/", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                results.append({
                    "label": props.get("label"),
                    "score": props.get("score"),
                    "type": props.get("type"),
                    "city": props.get("city"),
                    "postcode": props.get("postcode"),
                })
            
            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
        
        elif name == "search_addresses":
            params = {
                "q": arguments["q"],
                "limit": arguments.get("limit", 5),
                "autocomplete": 1,
            }
            response = await client.get(f"{API_ADRESSE_URL}/search/", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                results.append({
                    "label": props.get("label"),
                    "type": props.get("type"),
                    "city": props.get("city"),
                })
            
            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
        
        # ====================================================================
        # API GEO
        # ====================================================================
        
        elif name == "search_communes":
            params = {}
            if "nom" in arguments:
                params["nom"] = arguments["nom"]
            if "code_postal" in arguments:
                params["codePostal"] = arguments["code_postal"]
            if "fields" in arguments:
                params["fields"] = arguments["fields"]
            
            response = await client.get(f"{API_GEO_URL}/communes", params=params)
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        
        elif name == "get_commune_info":
            code = arguments["code"]
            response = await client.get(f"{API_GEO_URL}/communes/{code}", params={"fields": "nom,code,codesPostaux,population,departement,region"})
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        
        elif name == "get_departement_communes":
            code = arguments["code"]
            response = await client.get(f"{API_GEO_URL}/departements/{code}/communes")
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        
        elif name == "search_departements":
            params = {}
            if "nom" in arguments:
                params["nom"] = arguments["nom"]
            
            response = await client.get(f"{API_GEO_URL}/departements", params=params)
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        
        elif name == "search_regions":
            params = {}
            if "nom" in arguments:
                params["nom"] = arguments["nom"]
            
            response = await client.get(f"{API_GEO_URL}/regions", params=params)
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        
        elif name == "get_region_info":
            code = arguments["code"]
            response = await client.get(f"{API_GEO_URL}/regions/{code}")
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")


async def main():
    """Point d'entrée principal"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
