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
            description="Reprojeter des données géographiques vers un autre système de coordonnées (GeoJSON, KML, GeoPackage, Shapefile). Les formats binaires doivent être encodés en base64.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données géographiques. Pour les formats binaires (gpkg, shapefile), fournir du base64."},
                    "input_format": {"type": "string", "description": "Format d'entrée: geojson, kml, gpkg, shapefile"},
                    "target_crs": {"type": "string", "description": "CRS cible (ex: EPSG:3857)"},
                    "source_crs": {"type": "string", "description": "CRS source si absent des données"},
                    "output_format": {"type": "string", "description": "Format de sortie (par défaut geojson)"},
                },
                "required": ["data", "input_format", "target_crs"],
            },
        ),
        Tool(
            name="buffer_geodata",
            description="Calculer un tampon (buffer) autour des géométries. Fournir un CRS métrique pour des distances en mètres.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données géographiques (texte ou base64 selon format)."},
                    "input_format": {"type": "string", "description": "Format d'entrée: geojson, kml, gpkg, shapefile"},
                    "distance": {"type": "number", "description": "Distance du buffer (en unités du CRS utilisé)."},
                    "source_crs": {"type": "string", "description": "CRS source si absent des données"},
                    "buffer_crs": {"type": "string", "description": "CRS pour le calcul du buffer (ex: EPSG:2154)"},
                    "output_crs": {"type": "string", "description": "CRS du résultat"},
                    "output_format": {"type": "string", "description": "Format de sortie"},
                    "cap_style": {"type": "string", "enum": ["round", "flat", "square"], "description": "Style des extrémités"},
                    "join_style": {"type": "string", "enum": ["round", "mitre", "bevel"], "description": "Style des joints"},
                    "mitre_limit": {"type": "number", "description": "Limite pour les angles rentrants (mitre)"},
                    "single_sided": {"type": "boolean", "description": "Buffer unilatéral"},
                    "resolution": {"type": "integer", "description": "Résolution du buffer (par défaut 16)"},
                },
                "required": ["data", "input_format", "distance"],
            },
        ),
        Tool(
            name="intersect_geodata",
            description="Calculer l'intersection de deux jeux de données géographiques.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_a": {"type": "string", "description": "Premier jeu de données."},
                    "input_format_a": {"type": "string", "description": "Format du premier jeu (geojson, kml, gpkg, shapefile)"},
                    "data_b": {"type": "string", "description": "Second jeu de données."},
                    "input_format_b": {"type": "string", "description": "Format du second jeu"},
                    "source_crs_a": {"type": "string", "description": "CRS source du premier jeu"},
                    "source_crs_b": {"type": "string", "description": "CRS source du second jeu"},
                    "target_crs": {"type": "string", "description": "CRS commun pour l'opération"},
                    "output_format": {"type": "string", "description": "Format de sortie"},
                },
                "required": ["data_a", "input_format_a", "data_b", "input_format_b"],
            },
        ),
        Tool(
            name="clip_geodata",
            description="Découper un jeu de données avec une zone de découpe (clip).",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données à découper."},
                    "input_format": {"type": "string", "description": "Format de ces données"},
                    "clip_data": {"type": "string", "description": "Géométrie de découpe."},
                    "clip_format": {"type": "string", "description": "Format de la géométrie de découpe"},
                    "source_crs": {"type": "string", "description": "CRS des données à découper"},
                    "clip_source_crs": {"type": "string", "description": "CRS de la géométrie de découpe"},
                    "target_crs": {"type": "string", "description": "CRS commun pour l'opération"},
                    "output_format": {"type": "string", "description": "Format de sortie"},
                },
                "required": ["data", "input_format", "clip_data", "clip_format"],
            },
        ),
        Tool(
            name="convert_geodata_format",
            description="Convertir des données géographiques entre formats (GeoJSON, KML, GeoPackage, Shapefile).",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données sources"},
                    "input_format": {"type": "string", "description": "Format d'entrée"},
                    "output_format": {"type": "string", "description": "Format de sortie désiré"},
                    "source_crs": {"type": "string", "description": "CRS source si absent des données"},
                },
                "required": ["data", "input_format", "output_format"],
            },
        ),
        Tool(
            name="get_geodata_bbox",
            description="Calculer la bounding box (enveloppe minimale) d'un jeu de données.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données géographiques"},
                    "input_format": {"type": "string", "description": "Format d'entrée"},
                    "source_crs": {"type": "string", "description": "CRS source si absent des données"},
                    "target_crs": {"type": "string", "description": "CRS dans lequel retourner la bbox"},
                },
                "required": ["data", "input_format"],
            },
        ),
        Tool(
            name="dissolve_geodata",
            description="Regrouper (dissolve) des géométries selon un attribut ou globalement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données géographiques"},
                    "input_format": {"type": "string", "description": "Format d'entrée"},
                    "by": {"type": "string", "description": "Nom de l'attribut pour regrouper (optionnel)"},
                    "aggregations": {"type": "object", "description": "Agrégations supplémentaires pour les attributs (ex: {\"population\": \"sum\"})"},
                    "source_crs": {"type": "string", "description": "CRS source si absent des données"},
                    "target_crs": {"type": "string", "description": "CRS du résultat"},
                    "output_format": {"type": "string", "description": "Format de sortie"},
                },
                "required": ["data", "input_format"],
            },
        ),
        Tool(
            name="explode_geodata",
            description="Désassembler les géométries multi-parties en entités simples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Données géographiques"},
                    "input_format": {"type": "string", "description": "Format d'entrée"},
                    "source_crs": {"type": "string", "description": "CRS source si absent des données"},
                    "keep_index": {"type": "boolean", "description": "Conserver l'index d'origine"},
                    "output_format": {"type": "string", "description": "Format de sortie"},
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
