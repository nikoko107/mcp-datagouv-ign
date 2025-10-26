#!/usr/bin/env python3
"""
Serveur MCP complet pour data.gouv.fr + 4 APIs nationales françaises
- data.gouv.fr : Données publiques
- IGN Géoplateforme : Cartographie (WMTS, WMS, WFS) + Navigation (Itinéraire, Isochrone)
- API Adresse : Géocodage national
- API Geo : Découpage administratif
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, quote
from functools import partial

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from ign_geo_services import IGNGeoServices
from spatial_processing import (
    GeoProcessingError,
    buffer_geodata,
    clip_geodata,
    convert_geodata_format,
    dissolve_geodata,
    explode_geodata,
    get_geodata_bbox,
    intersect_geodata,
    reproject_geodata,
)

# Configuration
API_BASE_URL = "https://www.data.gouv.fr/api/1"
API_ADRESSE_URL = "https://api-adresse.data.gouv.fr"
API_GEO_URL = "https://geo.api.gouv.fr"
API_KEY = os.getenv("DATAGOUV_API_KEY", "")

# Initialisation
app = Server("french-opendata-complete-mcp")
ign_services = IGNGeoServices()


async def run_geoprocessing(func, **kwargs):
    return await asyncio.to_thread(partial(func, **kwargs))


async def _execute_tool_logic(name: str, arguments: Any, client: httpx.AsyncClient) -> list[TextContent]:
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
        response = await client.get(
            f"{API_GEO_URL}/communes/{code}",
            params={"fields": "nom,code,codesPostaux,population,departement,region"}
        )
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

    # ====================================================================
    # IGN NAVIGATION
    # ====================================================================
    elif name == "get_route_capabilities":
        capabilities = await ign_services.get_route_capabilities(client)
        return [TextContent(type="text", text=json.dumps(capabilities, ensure_ascii=False, indent=2))]

    elif name == "calculate_route":
        route_data = await ign_services.calculate_route(
            client=client,
            start=arguments["start"],
            end=arguments["end"],
            resource=arguments.get("resource", "bdtopo-osrm"),
            profile=arguments.get("profile"),
            optimization=arguments.get("optimization", "fastest"),
            intermediates=arguments.get("intermediates"),
            get_steps=arguments.get("get_steps", True),
            get_bbox=arguments.get("get_bbox", True),
            constraints=arguments.get("constraints")
        )

        result = {
            "distance": route_data.get("distance"),
            "duration": route_data.get("duration"),
            "geometry": route_data.get("geometry"),
            "bbox": route_data.get("bbox"),
            "portions": route_data.get("portions", [])
        }

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "calculate_isochrone":
        isochrone_data = await ign_services.calculate_isochrone(
            client=client,
            point=arguments["point"],
            cost_value=arguments["cost_value"],
            cost_type=arguments.get("cost_type", "time"),
            resource=arguments.get("resource", "bdtopo-valhalla"),
            profile=arguments.get("profile"),
            direction=arguments.get("direction", "departure"),
            constraints=arguments.get("constraints"),
            distance_unit=arguments.get("distance_unit", "kilometer"),
            time_unit=arguments.get("time_unit", "hour")
        )

        return [TextContent(type="text", text=json.dumps(isochrone_data, ensure_ascii=False, indent=2))]

    # ====================================================================
    # IGN ALTIMETRIE
    # ====================================================================
    elif name == "get_altimetry_resources":
        resources = await ign_services.get_altimetry_resources(client)
        return [TextContent(type="text", text=json.dumps(resources, ensure_ascii=False, indent=2))]

    elif name == "get_elevation":
        elevation_data = await ign_services.get_elevation(
            client=client,
            lon=arguments["lon"],
            lat=arguments["lat"],
            resource=arguments.get("resource", "ign_rge_alti_wld"),
            delimiter=arguments.get("delimiter", "|"),
            zonly=arguments.get("zonly", False),
            measures=arguments.get("measures", False)
        )

        return [TextContent(type="text", text=json.dumps(elevation_data, ensure_ascii=False, indent=2))]

    elif name == "get_elevation_line":
        profile_data = await ign_services.get_elevation_line(
            client=client,
            lon=arguments["lon"],
            lat=arguments["lat"],
            resource=arguments.get("resource", "ign_rge_alti_wld"),
            delimiter=arguments.get("delimiter", "|"),
            profile_mode=arguments.get("profile_mode", "simple"),
            sampling=arguments.get("sampling", 50),
            zonly=arguments.get("zonly", False)
        )

        result = profile_data
        if "height_differences" in profile_data:
            hd = profile_data["height_differences"]
            summary = {
                "summary": f"Dénivelé positif: {hd.get('positive', 0)} m, Dénivelé négatif: {hd.get('negative', 0)} m",
                "profile": profile_data
            }
            result = summary

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    # ====================================================================
    # TRAITEMENTS SPATIAUX
    # ====================================================================
    elif name == "reproject_geodata":
        result = await run_geoprocessing(
            reproject_geodata,
            data=arguments["data"],
            input_format=arguments["input_format"],
            target_crs=arguments["target_crs"],
            source_crs=arguments.get("source_crs"),
            output_format=arguments.get("output_format"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "buffer_geodata":
        result = await run_geoprocessing(
            buffer_geodata,
            data=arguments["data"],
            input_format=arguments["input_format"],
            distance=arguments["distance"],
            source_crs=arguments.get("source_crs"),
            buffer_crs=arguments.get("buffer_crs"),
            output_crs=arguments.get("output_crs"),
            output_format=arguments.get("output_format"),
            cap_style=arguments.get("cap_style"),
            join_style=arguments.get("join_style"),
            mitre_limit=arguments.get("mitre_limit"),
            single_sided=arguments.get("single_sided"),
            resolution=arguments.get("resolution", 16),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "intersect_geodata":
        result = await run_geoprocessing(
            intersect_geodata,
            data_a=arguments["data_a"],
            input_format_a=arguments["input_format_a"],
            data_b=arguments["data_b"],
            input_format_b=arguments["input_format_b"],
            source_crs_a=arguments.get("source_crs_a"),
            source_crs_b=arguments.get("source_crs_b"),
            target_crs=arguments.get("target_crs"),
            output_format=arguments.get("output_format"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "clip_geodata":
        result = await run_geoprocessing(
            clip_geodata,
            data=arguments["data"],
            input_format=arguments["input_format"],
            clip_data=arguments["clip_data"],
            clip_format=arguments["clip_format"],
            source_crs=arguments.get("source_crs"),
            clip_source_crs=arguments.get("clip_source_crs"),
            target_crs=arguments.get("target_crs"),
            output_format=arguments.get("output_format"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "convert_geodata_format":
        result = await run_geoprocessing(
            convert_geodata_format,
            data=arguments["data"],
            input_format=arguments["input_format"],
            output_format=arguments["output_format"],
            source_crs=arguments.get("source_crs"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_geodata_bbox":
        result = await run_geoprocessing(
            get_geodata_bbox,
            data=arguments["data"],
            input_format=arguments["input_format"],
            source_crs=arguments.get("source_crs"),
            target_crs=arguments.get("target_crs"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "dissolve_geodata":
        result = await run_geoprocessing(
            dissolve_geodata,
            data=arguments["data"],
            input_format=arguments["input_format"],
            by=arguments.get("by"),
            aggregations=arguments.get("aggregations"),
            source_crs=arguments.get("source_crs"),
            target_crs=arguments.get("target_crs"),
            output_format=arguments.get("output_format"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "explode_geodata":
        result = await run_geoprocessing(
            explode_geodata,
            data=arguments["data"],
            input_format=arguments["input_format"],
            source_crs=arguments.get("source_crs"),
            keep_index=arguments.get("keep_index", False),
            output_format=arguments.get("output_format"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


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
        
        # IGN GÉOPLATEFORME (9 outils)
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
            description="""Récupérer des données vectorielles IGN au format GeoJSON via le service WFS.

⚠️ DONNÉES RETOURNÉES : Le résultat est directement du GeoJSON (format 'geojson') utilisable par les outils de traitement spatial.

COUCHES IGN PRINCIPALES :
- ADMINEXPRESS-COG-CARTO.LATEST:commune : Limites communales
- ADMINEXPRESS-COG-CARTO.LATEST:departement : Limites départementales
- ADMINEXPRESS-COG-CARTO.LATEST:region : Limites régionales
- ADMINEXPRESS-COG-CARTO.LATEST:epci : EPCI (intercommunalités)
- BDTOPO_V3:batiment : Bâtiments
- BDTOPO_V3:troncon_de_route : Routes
- BDTOPO_V3:surface_hydrographique : Plans d'eau
- BDTOPO_V3:troncon_de_cours_d_eau : Cours d'eau
- CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle : Parcelles cadastrales

UTILISATION AVEC BBOX :
Pour limiter à une zone géographique (recommandé pour éviter trop de données) :
- bbox format : "minx,miny,maxx,maxy" en EPSG:4326 (lon/lat)
- Exemple : "2.25,48.81,2.42,48.90" pour Paris centre

WORKFLOW TYPIQUE :
1. get_wfs_features(typename="ADMINEXPRESS-COG-CARTO.LATEST:commune", bbox=zone)
2. Le résultat est du GeoJSON utilisable directement
3. Utiliser avec buffer_geodata, clip_geodata, etc.

NOTES :
- max_features limite le nombre d'entités (défaut: 100)
- Résultat en EPSG:4326 par défaut (lon/lat en degrés)
- Pour des calculs métriques, utiliser reproject_geodata vers EPSG:2154

EXEMPLE 1 - Communes d'un département :
typename="ADMINEXPRESS-COG-CARTO.LATEST:commune"
bbox="4.0,45.0,6.0,47.0" (région Rhône-Alpes)
max_features=500

EXEMPLE 2 - Bâtiments de Lyon centre :
typename="BDTOPO_V3:batiment"
bbox="4.82,45.75,4.85,45.77"
max_features=1000""",
            inputSchema={
                "type": "object",
                "properties": {
                    "typename": {
                        "type": "string",
                        "description": "Nom complet de la couche WFS. Format: 'DATASET:couche'. Ex: 'ADMINEXPRESS-COG-CARTO.LATEST:commune'. Utiliser search_wfs_features pour trouver les noms."
                    },
                    "bbox": {
                        "type": "string",
                        "description": "Zone géographique (optionnel mais recommandé). Format: 'minx,miny,maxx,maxy' en EPSG:4326. Ex: '2.25,48.81,2.42,48.90' pour Paris."
                    },
                    "max_features": {
                        "type": "integer",
                        "default": 100,
                        "description": "Nombre maximum d'entités à retourner (défaut: 100). Augmenter si besoin mais attention à la taille des données."
                    },
                },
                "required": ["typename"],
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

        # IGN NAVIGATION (3 outils)
        Tool(
            name="get_route_capabilities",
            description="Récupérer les capacités du service de navigation IGN (ressources disponibles, profils, optimisations)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="calculate_route",
            description="Calculer un itinéraire entre deux points avec l'API IGN",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Point de départ (longitude,latitude)"},
                    "end": {"type": "string", "description": "Point d'arrivée (longitude,latitude)"},
                    "resource": {
                        "type": "string",
                        "default": "bdtopo-osrm",
                        "description": "Graphe de navigation: bdtopo-osrm (rapide), bdtopo-valhalla (équilibré), bdtopo-pgr (contraintes avancées)"
                    },
                    "profile": {"type": "string", "description": "Mode de transport: car, pedestrian"},
                    "optimization": {
                        "type": "string",
                        "default": "fastest",
                        "description": "Mode d'optimisation: fastest (plus rapide) ou shortest (plus court)"
                    },
                    "intermediates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste de points intermédiaires (longitude,latitude)"
                    },
                    "get_steps": {
                        "type": "boolean",
                        "default": True,
                        "description": "Inclure les étapes détaillées de l'itinéraire"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Contraintes de routage (banned, preferred, unpreferred)"
                    },
                },
                "required": ["start", "end"],
            },
        ),
        Tool(
            name="calculate_isochrone",
            description="Calculer une isochrone (zone accessible en un temps donné) ou isodistance (zone accessible en une distance donnée)",
            inputSchema={
                "type": "object",
                "properties": {
                    "point": {"type": "string", "description": "Point central (longitude,latitude)"},
                    "cost_value": {"type": "number", "description": "Valeur de temps ou distance"},
                    "cost_type": {
                        "type": "string",
                        "default": "time",
                        "description": "Type de coût: time (temps) ou distance"
                    },
                    "resource": {
                        "type": "string",
                        "default": "bdtopo-valhalla",
                        "description": "Graphe de navigation: bdtopo-valhalla (recommandé) ou bdtopo-pgr"
                    },
                    "profile": {"type": "string", "description": "Mode de transport: car, pedestrian"},
                    "direction": {
                        "type": "string",
                        "default": "departure",
                        "description": "Direction: departure (depuis le point) ou arrival (vers le point)"
                    },
                    "time_unit": {
                        "type": "string",
                        "default": "hour",
                        "description": "Unité de temps: second, minute, hour"
                    },
                    "distance_unit": {
                        "type": "string",
                        "default": "kilometer",
                        "description": "Unité de distance: meter, kilometer, mile"
                    },
                },
                "required": ["point", "cost_value"],
            },
        ),

        # IGN ALTIMETRIE (3 outils)
        Tool(
            name="get_altimetry_resources",
            description="Récupérer la liste des ressources altimétriques disponibles (MNT, MNS, etc.)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_elevation",
            description="Récupérer l'altitude d'un ou plusieurs points géographiques",
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "string",
                        "description": "Longitude(s) séparée(s) par | (ex: '2.3522' ou '2.3|2.4|2.5')"
                    },
                    "lat": {
                        "type": "string",
                        "description": "Latitude(s) séparée(s) par | (ex: '48.8566' ou '48.8|48.9|49.0')"
                    },
                    "resource": {
                        "type": "string",
                        "default": "ign_rge_alti_wld",
                        "description": "Ressource altimétrique (ign_rge_alti_wld pour mondial)"
                    },
                    "delimiter": {
                        "type": "string",
                        "default": "|",
                        "description": "Séparateur de coordonnées: | ; ou ,"
                    },
                    "zonly": {
                        "type": "boolean",
                        "default": False,
                        "description": "Retourner uniquement les altitudes (sans coordonnées)"
                    },
                    "measures": {
                        "type": "boolean",
                        "default": False,
                        "description": "Inclure les détails de mesure multi-sources"
                    },
                },
                "required": ["lon", "lat"],
            },
        ),
        Tool(
            name="get_elevation_line",
            description="Calculer un profil altimétrique le long d'une ligne (dénivelés positif/négatif)",
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "string",
                        "description": "Longitudes des points de la ligne séparés par | (minimum 2 points)"
                    },
                    "lat": {
                        "type": "string",
                        "description": "Latitudes des points de la ligne séparés par | (minimum 2 points)"
                    },
                    "resource": {
                        "type": "string",
                        "default": "ign_rge_alti_wld",
                        "description": "Ressource altimétrique"
                    },
                    "delimiter": {
                        "type": "string",
                        "default": "|",
                        "description": "Séparateur: | ; ou ,"
                    },
                    "profile_mode": {
                        "type": "string",
                        "default": "simple",
                        "description": "Mode de calcul: simple (rapide) ou accurate (précis)"
                    },
                    "sampling": {
                        "type": "integer",
                        "default": 50,
                        "description": "Nombre de points d'échantillonnage (2-5000)"
                    },
                    "zonly": {
                        "type": "boolean",
                        "default": False,
                        "description": "Retourner uniquement les altitudes"
                    },
                },
                "required": ["lon", "lat"],
            },
        ),

        # TRAITEMENTS SPATIAUX (8 outils)
        Tool(
            name="reproject_geodata",
            description="""Reprojeter des données géographiques d'un système de coordonnées vers un autre.

FORMATS SUPPORTÉS :
- geojson/json : Texte JSON (le plus courant, utilisé par get_wfs_features)
- kml : Texte XML Google Earth
- gpkg : Binaire base64 encodé (GeoPackage)
- shapefile : Binaire base64 encodé (zip contenant .shp, .shx, .dbf, .prj)

CRS COURANTS :
- EPSG:4326 : WGS84 (GPS, longitude/latitude en degrés, utilisé par défaut)
- EPSG:3857 : Web Mercator (Google Maps, en mètres)
- EPSG:2154 : Lambert 93 (France métropolitaine, en mètres)
- EPSG:32631 : UTM Zone 31N (Ouest France, en mètres)

USAGE TYPIQUE :
Pour calculer des distances ou buffers en mètres, reprojeter d'abord en EPSG:2154 ou EPSG:3857.
Les données WFS IGN sont souvent en EPSG:4326 par défaut.

EXEMPLE : Reprojeter des communes de EPSG:4326 vers Lambert 93 (EPSG:2154)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données géographiques (string GeoJSON ou base64 pour binaires). Exemple : récupérées via get_wfs_features"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format d'entrée : 'geojson' (si données de get_wfs_features), 'kml', 'gpkg', 'shapefile'"
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "CRS cible au format EPSG:XXXX. Ex: 'EPSG:2154' pour Lambert 93 France, 'EPSG:3857' pour Web Mercator"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS source si absent des données (optionnel). Ex: 'EPSG:4326'"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format de sortie : 'geojson' (par défaut, recommandé), 'kml', 'gpkg', 'shapefile'"
                    },
                },
                "required": ["data", "input_format", "target_crs"],
            },
        ),
        Tool(
            name="buffer_geodata",
            description="""Calculer un tampon (zone tampon) autour des géométries à une distance donnée.

⚠️ IMPORTANT : Pour des distances en MÈTRES, les données DOIVENT être en CRS métrique (EPSG:2154, EPSG:3857, etc.), PAS en EPSG:4326 (degrés).

WORKFLOW RECOMMANDÉ :
1. Récupérer les données (ex: get_wfs_features)
2. Si les données sont en EPSG:4326, utiliser reproject_geodata vers EPSG:2154
3. Appliquer buffer_geodata avec la distance en mètres

CRS MÉTRIQUES POUR LA FRANCE :
- EPSG:2154 : Lambert 93 (recommandé pour France métropolitaine)
- EPSG:3857 : Web Mercator (approximation mondiale)
- EPSG:32631 : UTM Zone 31N (Ouest France)

EXEMPLES :
- Buffer de 500m autour de bâtiments : distance=500, buffer_crs='EPSG:2154'
- Buffer de 1km autour de communes : distance=1000, buffer_crs='EPSG:2154'
- Buffer de 100m autour de routes : distance=100, buffer_crs='EPSG:2154'

NOTES :
- cap_style='round' (par défaut) : extrémités arrondies
- join_style='round' (par défaut) : angles arrondis
- resolution=16 (par défaut) : qualité du cercle (plus = plus lisse)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données géographiques (GeoJSON string ou base64). Doivent être en CRS métrique pour distance en mètres"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "distance": {
                        "type": "number",
                        "description": "Distance du buffer en UNITÉS DU CRS. Si buffer_crs=EPSG:2154, alors en MÈTRES. Ex: 500 pour 500m"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS source si absent (optionnel). Ex: 'EPSG:4326'"
                    },
                    "buffer_crs": {
                        "type": "string",
                        "description": "CRS pour le calcul (OBLIGATOIRE si métrique). Ex: 'EPSG:2154' pour mètres en France"
                    },
                    "output_crs": {
                        "type": "string",
                        "description": "CRS du résultat (optionnel, par défaut = buffer_crs). Ex: 'EPSG:4326' pour retour en GPS"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format de sortie : 'geojson' (par défaut), 'kml', 'gpkg', 'shapefile'"
                    },
                    "cap_style": {
                        "type": "string",
                        "enum": ["round", "flat", "square"],
                        "description": "Style extrémités : 'round' (arrondi, défaut), 'flat' (plat), 'square' (carré)"
                    },
                    "join_style": {
                        "type": "string",
                        "enum": ["round", "mitre", "bevel"],
                        "description": "Style angles : 'round' (arrondi, défaut), 'mitre' (pointu), 'bevel' (biseauté)"
                    },
                    "resolution": {
                        "type": "integer",
                        "description": "Nombre de segments pour arrondir (défaut: 16). Plus = plus lisse mais plus lourd"
                    },
                },
                "required": ["data", "input_format", "distance"],
            },
        ),
        Tool(
            name="intersect_geodata",
            description="""Calculer l'intersection géométrique de deux jeux de données (partie commune).

USAGE TYPIQUE :
- Trouver les bâtiments DANS une zone inondable
- Parcelles cadastrales DANS les limites communales
- Routes QUI TRAVERSENT des zones protégées

IMPORTANT : Les deux jeux de données seront automatiquement reprojetés dans le même CRS.

WORKFLOW :
1. Récupérer data_a (ex: get_wfs_features pour bâtiments)
2. Récupérer data_b (ex: get_wfs_features pour zone)
3. Appeler intersect_geodata pour obtenir data_a ∩ data_b

RÉSULTAT :
- Conserve les géométries ET les attributs des deux sources
- Ne retourne QUE les entités qui se chevauchent
- Géométries découpées aux limites de l'intersection

EXEMPLE :
Trouver les parcelles dans une commune :
- data_a = parcelles cadastrales (WFS CADASTRALPARCELS.PARCELLAIRE_EXPRESS)
- data_b = limite de commune (WFS ADMINEXPRESS-COG-CARTO.LATEST:commune)
→ Résultat = parcelles découpées aux limites communales""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_a": {
                        "type": "string",
                        "description": "Premier jeu de données (GeoJSON string ou base64). Ex: bâtiments, parcelles"
                    },
                    "input_format_a": {
                        "type": "string",
                        "description": "Format de data_a : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "data_b": {
                        "type": "string",
                        "description": "Second jeu de données (zone de découpe/filtre). Ex: commune, zone inondable"
                    },
                    "input_format_b": {
                        "type": "string",
                        "description": "Format de data_b : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "source_crs_a": {
                        "type": "string",
                        "description": "CRS de data_a si absent (optionnel). Ex: 'EPSG:4326'"
                    },
                    "source_crs_b": {
                        "type": "string",
                        "description": "CRS de data_b si absent (optionnel). Ex: 'EPSG:4326'"
                    },
                    "target_crs": {"type": "string", "description": "CRS commun pour l'opération"},
                    "output_format": {"type": "string", "description": "Format de sortie"},
                },
                "required": ["data_a", "input_format_a", "data_b", "input_format_b"],
            },
        ),
        Tool(
            name="clip_geodata",
            description="""Découper (clip) un jeu de données avec une géométrie de découpe. Similaire à un "cookie cutter" - garde uniquement ce qui est À L'INTÉRIEUR de la zone de découpe.

DIFFÉRENCE avec intersect_geodata :
- clip_geodata : COUPE les géométries ET ne conserve QUE la partie dans la zone
- intersect_geodata : Conserve les attributs des DEUX sources

USAGE TYPIQUE :
- Découper des bâtiments avec les limites d'une commune
- Extraire les routes dans un département
- Isoler les parcelles dans une zone d'étude

EXEMPLE :
Bâtiments de Paris :
- data = tous les bâtiments d'Île-de-France (WFS BDTOPO_V3:batiment)
- clip_data = limite de Paris (WFS commune, INSEE=75056)
→ Résultat = UNIQUEMENT bâtiments dans Paris, découpés aux limites""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données à découper (GeoJSON string ou base64). Ex: bâtiments, routes"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "clip_data": {
                        "type": "string",
                        "description": "Zone de découpe (GeoJSON string ou base64). Ex: limite commune"
                    },
                    "clip_format": {
                        "type": "string",
                        "description": "Format de la zone : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS des données si absent (optionnel)"
                    },
                    "clip_source_crs": {
                        "type": "string",
                        "description": "CRS de la zone de découpe si absent (optionnel)"
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "CRS commun pour l'opération (optionnel)"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format de sortie : 'geojson' (par défaut), 'kml', 'gpkg', 'shapefile'"
                    },
                },
                "required": ["data", "input_format", "clip_data", "clip_format"],
            },
        ),
        Tool(
            name="convert_geodata_format",
            description="""Convertir des données géographiques d'un format vers un autre.

FORMATS SUPPORTÉS :
- geojson/json : Texte JSON (léger, web-friendly, par défaut)
- kml : Texte XML (Google Earth, Google Maps)
- gpkg : Binaire GeoPackage (standard OGC, fichier unique, retourné en base64)
- shapefile : Binaire ESRI (multi-fichiers zippés, retourné en base64)

USAGE TYPIQUE :
- Préparer données WFS (GeoJSON) pour QGIS/ArcGIS → shapefile ou gpkg
- Convertir Shapefile ancien → GeoJSON moderne
- Export pour Google Earth → kml

NOTES :
- Les formats binaires (gpkg, shapefile) sont encodés en base64
- Les attributs et géométries sont préservés
- Le CRS est conservé (ou peut être spécifié)

EXEMPLE :
Convertir communes GeoJSON en Shapefile pour QGIS :
- data = résultat de get_wfs_features (GeoJSON)
- input_format = "geojson"
- output_format = "shapefile"
→ Résultat = ZIP base64 contenant .shp, .shx, .dbf, .prj""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données sources (GeoJSON string ou base64 si binaire)"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format d'entrée : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format désiré : 'geojson' (texte), 'kml' (texte), 'gpkg' (base64), 'shapefile' (base64)"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS source si absent des données (optionnel). Ex: 'EPSG:4326'"
                    },
                },
                "required": ["data", "input_format", "output_format"],
            },
        ),
        Tool(
            name="get_geodata_bbox",
            description="""Calculer la bounding box (rectangle englobant minimum) d'un jeu de données.

RÉSULTAT : Un objet avec minx, miny, maxx, maxy (coordonnées du rectangle).

USAGE TYPIQUE :
- Obtenir l'étendue d'un jeu de données pour paramètres get_wms_map_url
- Calculer la zone couverte par des entités
- Vérifier si données dans zone attendue

EXEMPLE :
BBox d'une commune en EPSG:4326 (lon/lat) :
- data = commune de Lyon (WFS)
- input_format = "geojson"
- target_crs = "EPSG:4326"
→ Résultat = {"minx": 4.79, "miny": 45.71, "maxx": 4.88, "maxy": 45.81}

Utilisation avec WMS :
bbox = get_geodata_bbox(communes)
map = get_wms_map_url(bbox=f"{bbox.minx},{bbox.miny},{bbox.maxx},{bbox.maxy}")""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données géographiques (GeoJSON string ou base64)"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS source si absent (optionnel)"
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "CRS pour la bbox (optionnel). Ex: 'EPSG:4326' pour lon/lat"
                    },
                },
                "required": ["data", "input_format"],
            },
        ),
        Tool(
            name="dissolve_geodata",
            description="""Fusionner (dissolve) des géométries en les regroupant par attribut ou globalement.

USAGE TYPIQUE :
- Fusionner toutes les communes d'un département → limite départementale
- Fusionner parcelles par propriétaire → îlots de propriété
- Fusionner zones par type → zones homogènes

AVEC ATTRIBUT (by) :
Les entités ayant la MÊME VALEUR d'attribut sont fusionnées ensemble.
Ex: dissolve par "departement" → une géométrie par département

SANS ATTRIBUT (by=None) :
TOUTES les géométries sont fusionnées en UNE seule.
Ex: toutes les communes de France → frontière de la France

AGRÉGATIONS :
Spécifier comment combiner les autres attributs (sum, mean, first, etc.)
Ex: {"population": "sum"} → somme des populations

EXEMPLE 1 - Par département :
- data = communes d'une région (WFS)
- by = "code_departement"
- aggregations = {"population": "sum"}
→ Résultat = géométries départementales avec population totale

EXEMPLE 2 - Fusion globale :
- data = toutes les communes d'un EPCI
- by = None (ou omis)
→ Résultat = UNE géométrie = limite de l'EPCI""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données géographiques (GeoJSON string ou base64)"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "by": {
                        "type": "string",
                        "description": "Nom de l'attribut pour regrouper (optionnel). Si omis = fusion globale. Ex: 'departement', 'region', 'type'"
                    },
                    "aggregations": {
                        "type": "object",
                        "description": "Agrégations pour autres attributs (optionnel). Ex: {\"population\": \"sum\", \"superficie\": \"sum\"}"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS source si absent (optionnel)"
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "CRS du résultat (optionnel)"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format de sortie : 'geojson' (par défaut), 'kml', 'gpkg', 'shapefile'"
                    },
                },
                "required": ["data", "input_format"],
            },
        ),
        Tool(
            name="explode_geodata",
            description="""Séparer les géométries multi-parties (Multi*) en géométries simples individuelles.

TRANSFORMATIONS :
- MultiPoint → plusieurs Point
- MultiLineString → plusieurs LineString
- MultiPolygon → plusieurs Polygon
- GeometryCollection → géométries séparées

USAGE TYPIQUE :
- Séparer les îles d'un archipel (MultiPolygon → Polygons)
- Isoler chaque segment d'un réseau (MultiLineString → LineStrings)
- Analyser individuellement chaque partie d'une géométrie complexe

RÉSULTAT :
Chaque partie devient une entité distincte.
Les attributs sont DUPLIQUÉS pour chaque partie.

EXEMPLE :
Commune avec plusieurs polygones (territoire + îles) :
- data = commune en MultiPolygon
- input_format = "geojson"
→ Résultat = N entités, une par polygone (territoire principal, île 1, île 2, etc.)

Utile avant d'analyser la superficie de chaque île séparément.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Données géographiques avec Multi* (GeoJSON string ou base64)"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Format : 'geojson', 'kml', 'gpkg', 'shapefile'"
                    },
                    "source_crs": {
                        "type": "string",
                        "description": "CRS source si absent (optionnel)"
                    },
                    "keep_index": {
                        "type": "boolean",
                        "description": "Conserver index d'origine (défaut: false)"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format de sortie : 'geojson' (par défaut), 'kml', 'gpkg', 'shapefile'"
                    },
                },
                "required": ["data", "input_format"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Exécute un outil"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await _execute_tool_logic(name, arguments, client)
    except GeoProcessingError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))]
    except httpx.HTTPStatusError as exc:
        error = {
            "error": "HTTP error while calling external API",
            "status_code": exc.response.status_code,
            "detail": exc.response.text,
        }
        return [TextContent(type="text", text=json.dumps(error, ensure_ascii=False, indent=2))]
    except httpx.HTTPError as exc:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"HTTP communication error: {exc}"}, ensure_ascii=False, indent=2),
        )]
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))]


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
