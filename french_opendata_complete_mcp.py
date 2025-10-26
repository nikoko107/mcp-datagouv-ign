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
            description="""Calculer un itinéraire routier optimisé entre deux points avec l'API de navigation IGN Géoplateforme.

📍 SERVICE : API Itinéraire IGN Géoplateforme (données ouvertes, sans clé API)
🔄 LIMITE : Jusqu'à 5 requêtes/seconde
🗺️ SOURCE : BD TOPO® (réseau routier et tables de communication)

RESSOURCES DISPONIBLES (graphes de navigation basés sur BD TOPO V3) :

1. **bdtopo-osrm** (OSRM) - ⚡ PERFORMANCES MAXIMALES
   - Le plus rapide des 3 moteurs
   - Support : car (voiture) uniquement
   - Contraintes : Limitées (options de base)
   - Usage : Calculs simples, applications grand public, forte volumétrie
   - ⚠️ LIMITATION : "fastest" non disponible pour pedestrian sur cette ressource

2. **bdtopo-valhalla** (Valhalla) - ⚖️ ÉQUILIBRÉ
   - Bon compromis performance/fonctionnalités
   - Support : car (voiture) ET pedestrian (piéton)
   - Contraintes : Moyennes
   - Usage : Applications polyvalentes, bon choix par défaut

3. **bdtopo-pgr** (pgRouting) - 🎯 CONTRAINTES AVANCÉES
   - Performance moindre mais fonctionnalités étendues
   - Support : car et pedestrian avec contraintes complexes
   - Contraintes : Étendues (banned, preferred, unpreferred)
   - Attributs BD TOPO : Accès aux attributs détaillés des tronçons
   - Usage : Calculs complexes, routage avec contraintes métier

PROFILS DE TRANSPORT :

- **car** (voiture) - DÉFAUT
  * Vitesses : 10-125 km/h selon type de voie
  * Autoroutes : 125 km/h (base)
  * Routes importance 1-6 : 90-50 km/h
  * Voies restreintes : 10 km/h minimum
  * Modèle de vitesse : Calcul dynamique selon :
    - Classification routière (autoroute, importance 1-6)
    - Caractéristiques urbain/rural
    - Caractéristiques physiques (largeur, sinuosité)
    - Contexte environnemental (densité bâti, écoles)
    - Pénalités cumulatives jusqu'à 80% (voies rurales étroites, proximité intersections, zones urbaines denses)

- **pedestrian** (piéton)
  * Vitesse base : 4 km/h sur routes non autoroutières
  * Réseau : Chemins piétons, trottoirs, passages protégés
  * ⚠️ LIMITATION : optimization="fastest" non disponible avec bdtopo-osrm

MODES D'OPTIMISATION :

- **fastest** - Itinéraire le plus RAPIDE (minimise temps de trajet) - DÉFAUT
  * Privilégie les routes rapides (autoroutes, voies express)
  * ⚠️ Non disponible pour pedestrian + bdtopo-osrm

- **shortest** - Itinéraire le plus COURT (minimise distance)
  * Privilégie le kilométrage minimal
  * Peut emprunter des routes plus lentes

COORDONNÉES :

- Format : "longitude,latitude" (ex: "2.337306,48.849319" pour Paris)
- CRS par défaut : EPSG:4326 (WGS84) - coordonnées géographiques en degrés
- Autres CRS : EPSG:2154 (Lambert 93), EPSG:3857 (Web Mercator), etc. (via paramètre 'crs')

POINTS INTERMÉDIAIRES :

- Permet de forcer le passage par des points spécifiques
- Format : Liste de chaînes ["lon1,lat1", "lon2,lat2", ...]
- L'itinéraire sera calculé : start → intermediate1 → intermediate2 → ... → end
- Usage : Livraisons multi-points, circuits touristiques, respect d'un parcours imposé

CONTRAINTES DE ROUTAGE (nécessite resource="bdtopo-pgr") :

- Structure JSON : {"constraintType": "TYPE", "key": "ATTRIBUTE", "operator": "=", "value": "VALUE"}

- **Types de contraintes** :
  * banned : INTERDIT - Éviter absolument (ex: pas d'autoroutes)
  * preferred : PRÉFÉRÉ - Favoriser (ex: préférer les routes principales)
  * unpreferred : NON PRÉFÉRÉ - Éviter si possible (ex: éviter les tunnels)

- **Attributs disponibles (clés)** :
  * wayType : Type de voie (autoroute, route, chemin, etc.)
  * tollway : Routes à péage (true/false)
  * tunnel : Tunnels (true/false)
  * bridge : Ponts (true/false)
  * importance : Niveau d'importance (1-6)
  * nature : Nature de la voie (voir BD TOPO)

- **Exemples de contraintes** :
  * Éviter autoroutes : {"constraintType": "banned", "key": "wayType", "operator": "=", "value": "autoroute"}
  * Éviter péages : {"constraintType": "banned", "key": "tollway", "operator": "=", "value": "true"}
  * Préférer routes principales : {"constraintType": "preferred", "key": "importance", "operator": "=", "value": "1"}
  * Éviter tunnels : {"constraintType": "unpreferred", "key": "tunnel", "operator": "=", "value": "true"}

UNITÉS CONFIGURABLES :

- distanceUnit : kilometer (défaut), meter, mile
- timeUnit : hour (défaut), minute, second

RÉSULTAT RETOURNÉ :

- **start/end** : Points de départ/arrivée (coordonnées)
- **distance** : Distance totale (dans l'unité spécifiée)
- **duration** : Durée totale (dans l'unité spécifiée)
- **geometry** : Géométrie LineString (GeoJSON ou Encoded Polyline)
- **bbox** : Emprise géographique [minx, miny, maxx, maxy] (si getBbox=true)
- **resourceVersion** : Version du graphe de navigation (date de mise à jour)
- **profile** : Profil utilisé (car, pedestrian)
- **optimization** : Optimisation appliquée (fastest, shortest)
- **crs** : Système de coordonnées des géométries
- **portions** : Liste des portions de l'itinéraire
  * start/end : Début/fin de la portion
  * duration/distance : Durée/distance de la portion
  * bbox : Emprise de la portion
  * steps : Étapes détaillées (si getSteps=true)
    - id : Identifiant du tronçon
    - duration/distance : Durée/distance du tronçon
    - geometry : Géométrie du tronçon
    - instructions : Instructions de navigation turn-by-turn
    - attributes : Attributs BD TOPO (si waysAttributes spécifié)
      - name : Nom de la rue/route
      - wayType : Type de voie
      - importance : Niveau d'importance
      - tollway, tunnel, bridge : Caractéristiques

EXEMPLES D'UTILISATION :

1. Itinéraire simple Paris → Lyon en voiture (rapide) :
   start="2.3522,48.8566", end="4.8357,45.7640", resource="bdtopo-osrm", profile="car"

2. Itinéraire piéton avec instructions détaillées :
   start="2.33,48.85", end="2.37,48.86", profile="pedestrian", get_steps=true,
   ways_attributes=["name", "wayType"]

3. Itinéraire voiture évitant autoroutes et péages :
   start="2.35,48.85", end="4.84,45.76", resource="bdtopo-pgr", profile="car",
   constraints=[
     {"constraintType": "banned", "key": "wayType", "operator": "=", "value": "autoroute"},
     {"constraintType": "banned", "key": "tollway", "operator": "=", "value": "true"}
   ]

4. Circuit touristique avec points de passage (Louvre → Tour Eiffel → Sacré-Cœur) :
   start="2.3376,48.8606",
   intermediates=["2.2945,48.8584"],
   end="2.3431,48.8867",
   get_steps=true, get_bbox=true

5. Itinéraire le plus court (pas le plus rapide) :
   start="2.35,48.85", end="2.45,48.90", optimization="shortest"

WORKFLOW RECOMMANDÉ :

1. **Découverte** : Utiliser get_route_capabilities pour voir ressources/profils/options disponibles
2. **Choix ressource** :
   - Simple/rapide → bdtopo-osrm
   - Polyvalent → bdtopo-valhalla (défaut recommandé)
   - Contraintes → bdtopo-pgr
3. **Calcul** : Appeler calculate_route avec paramètres appropriés
4. **Visualisation** : Afficher geometry sur carte (WMS/WMTS IGN) ou utiliser steps pour navigation guidée
5. **Exploitation** : Extraire distance, duration, et attributs pour analyse ou affichage

CAS D'USAGE :

- 🚗 Applications GPS et navigation
- 🚚 Optimisation de tournées de livraison
- 🚑 Planification d'interventions d'urgence
- 🚌 Calcul d'itinéraires de transports scolaires
- 📊 Analyses de temps de trajet domicile-travail
- 🏢 Études d'accessibilité de sites commerciaux
- 🗺️ Création de cartes interactives avec routage""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Point de départ au format 'longitude,latitude' (ex: '2.337306,48.849319')"},
                    "end": {"type": "string", "description": "Point d'arrivée au format 'longitude,latitude' (ex: '2.367776,48.852891')"},
                    "resource": {
                        "type": "string",
                        "default": "bdtopo-osrm",
                        "description": "Graphe de navigation : bdtopo-osrm (rapide, car uniquement), bdtopo-valhalla (équilibré, car+pedestrian), bdtopo-pgr (contraintes avancées)"
                    },
                    "profile": {"type": "string", "description": "Mode de transport : car (voiture, défaut) ou pedestrian (piéton). Vérifier disponibilité par ressource."},
                    "optimization": {
                        "type": "string",
                        "default": "fastest",
                        "description": "Mode d'optimisation : fastest (temps minimal, défaut) ou shortest (distance minimale)"
                    },
                    "intermediates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Points de passage obligatoires au format 'longitude,latitude'. L'itinéraire passera par ces points dans l'ordre."
                    },
                    "get_steps": {
                        "type": "boolean",
                        "default": True,
                        "description": "Inclure les étapes détaillées (instructions de navigation, durée/distance par tronçon, noms de rues)"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Contraintes de routage (nécessite bdtopo-pgr). Ex: [{\"constraintType\": \"banned\", \"key\": \"wayType\", \"operator\": \"=\", \"value\": \"autoroute\"}]"
                    },
                    "get_bbox": {
                        "type": "boolean",
                        "default": False,
                        "description": "Inclure l'emprise géographique (bounding box) de l'itinéraire dans la réponse"
                    },
                    "geometry_format": {
                        "type": "string",
                        "default": "geojson",
                        "description": "Format de géométrie : geojson (GeoJSON LineString, défaut) ou polyline (Encoded Polyline)"
                    },
                    "distance_unit": {
                        "type": "string",
                        "default": "kilometer",
                        "description": "Unité de distance : kilometer (défaut), meter, mile"
                    },
                    "time_unit": {
                        "type": "string",
                        "default": "hour",
                        "description": "Unité de temps : hour (défaut), minute, second"
                    },
                    "crs": {
                        "type": "string",
                        "default": "EPSG:4326",
                        "description": "Système de coordonnées pour les géométries : EPSG:4326 (WGS84, défaut), EPSG:2154 (Lambert 93), etc."
                    },
                    "ways_attributes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Attributs des tronçons à inclure dans la réponse (ex: ['name', 'wayType', 'tollway']). Voir GetCapabilities."
                    }
                },
                "required": ["start", "end"],
            },
        ),
        Tool(
            name="calculate_isochrone",
            description="""Calculer une isochrone (zone accessible en un temps donné) ou isodistance (zone accessible en une distance donnée) avec l'API de navigation IGN Géoplateforme.

CONCEPT :
- ISOCHRONE : Polygone représentant tous les points atteignables depuis un point de départ en un temps donné (ex: 15 minutes en voiture)
- ISODISTANCE : Polygone représentant tous les points atteignables depuis un point de départ en une distance donnée (ex: 5 km à pied)

RESSOURCES DISPONIBLES (graphes de navigation basés sur BDTOPO V3) :
- bdtopo-valhalla : Moteur Valhalla - RECOMMANDÉ pour isochrones/isodistances, supporte car et pedestrian
- bdtopo-pgr : Moteur pgRouting - Supporte les contraintes (banned uniquement pour isochrones)
- bdtopo-iso : Ressource optimisée spécifiquement pour calculs d'isochrones (voir GetCapabilities)

PROFILS DE TRANSPORT (vérifier disponibilité via get_route_capabilities) :
- car : Voiture (défaut) - Réseau routier automobile
- pedestrian : Piéton - Chemins piétons, trottoirs, passages

TYPE DE COÛT (cost_type) :
- time : Calcul basé sur le TEMPS de trajet → ISOCHRONE (défaut)
  Exemple : "Tous les lieux accessibles en 30 minutes"
- distance : Calcul basé sur la DISTANCE parcourue → ISODISTANCE
  Exemple : "Tous les lieux accessibles en 5 kilomètres"

VALEUR DE COÛT (cost_value) :
- Pour time : Durée en unité spécifiée par time_unit (ex: 30 pour 30 minutes)
- Pour distance : Distance en unité spécifiée par distance_unit (ex: 5 pour 5 km)
- Valeurs typiques :
  * Voiture : 5-60 minutes ou 5-50 km
  * Piéton : 5-30 minutes ou 1-5 km

DIRECTION (sens du calcul) :
- departure : Point de DÉPART → calcule les zones d'ARRIVÉE possibles (défaut)
  Exemple : "Où puis-je aller depuis Paris en 20 minutes ?"
- arrival : Point d'ARRIVÉE → calcule les zones de DÉPART possibles
  Exemple : "D'où peut-on venir pour atteindre Paris en 20 minutes ?"

COORDONNÉES :
- Format : "longitude,latitude" (ex: "2.337306,48.849319" pour Paris)
- CRS par défaut : EPSG:4326 (WGS84) - coordonnées géographiques en degrés
- Possibilité d'utiliser d'autres CRS via paramètre 'crs' (voir GetCapabilities)

CONTRAINTES DE ROUTAGE (nécessite bdtopo-pgr) :
- ⚠️ Pour isochrones, seul le type "banned" est supporté (pas preferred/unpreferred)
- Structure : {"constraintType": "banned", "key": "wayType", "operator": "=", "value": "autoroute"}
- Exemple : Éviter les autoroutes pour isochrone piéton
  constraints=[{"constraintType": "banned", "key": "wayType", "operator": "=", "value": "autoroute"}]

UNITÉS :
- time_unit : second, minute, hour (défaut : hour, mais minute recommandé pour isochrones)
- distance_unit : meter, kilometer (défaut), mile

FORMAT DE GÉOMÉTRIE :
- geojson : Polygon GeoJSON (défaut) - Facilement affichable sur carte
- polyline : Encoded Polyline (format compact)

RÉSULTAT RETOURNÉ :
- point : Point de référence utilisé
- resource : Ressource de calcul utilisée
- costType : Type de coût (time ou distance)
- costValue : Valeur du coût
- profile : Profil de transport (car, pedestrian)
- direction : Direction du calcul (departure, arrival)
- crs : Système de coordonnées
- geometry : Géométrie du polygone (Polygon GeoJSON ou Encoded Polyline)
- departure/arrival : Timestamps de départ/arrivée (si applicable)
- alerts : Messages d'alerte éventuels

EXEMPLES D'UTILISATION :

1. Zone accessible en 15 minutes en voiture depuis Paris :
   point="2.3522,48.8566", cost_value=15, cost_type="time", time_unit="minute", profile="car"

2. Zone accessible en 30 minutes à pied depuis Gare du Nord :
   point="2.3547,48.8809", cost_value=30, cost_type="time", time_unit="minute", profile="pedestrian"

3. Zone accessible en 5 km à vélo (si profil disponible) :
   point="2.35,48.85", cost_value=5, cost_type="distance", distance_unit="kilometer"

4. D'où peut-on venir pour atteindre l'aéroport en 45 minutes :
   point="2.5479,49.0097", cost_value=45, cost_type="time", time_unit="minute", direction="arrival"

5. Isochrone évitant les autoroutes :
   point="2.35,48.85", cost_value=20, cost_type="time", resource="bdtopo-pgr",
   constraints=[{"constraintType": "banned", "key": "wayType", "operator": "=", "value": "autoroute"}]

WORKFLOW RECOMMANDÉ :
1. Utiliser get_route_capabilities pour vérifier les ressources et profils disponibles
2. Choisir resource=bdtopo-valhalla (standard) ou bdtopo-iso (optimisé)
3. Définir cost_type=time (isochrone) ou distance (isodistance)
4. Spécifier cost_value avec l'unité appropriée (ex: 15 minutes, 5 km)
5. Calculer avec calculate_isochrone
6. Afficher le polygone résultant sur une carte WMS/WMTS IGN

CAS D'USAGE PRATIQUES :
- Analyser l'accessibilité d'un lieu (commerces, services publics, transports)
- Délimiter des zones de chalandise
- Planifier des interventions d'urgence (pompiers, ambulances)
- Analyser des temps de trajet domicile-travail
- Optimiser l'emplacement de nouveaux services""",
            inputSchema={
                "type": "object",
                "properties": {
                    "point": {"type": "string", "description": "Point de référence au format 'longitude,latitude' (ex: '2.337306,48.849319')"},
                    "cost_value": {"type": "number", "description": "Valeur du coût : durée (ex: 15, 30) ou distance (ex: 5, 10) selon cost_type"},
                    "cost_type": {
                        "type": "string",
                        "default": "time",
                        "description": "Type de coût : time (isochrone basée sur temps) ou distance (isodistance basée sur distance)"
                    },
                    "resource": {
                        "type": "string",
                        "default": "bdtopo-valhalla",
                        "description": "Graphe de navigation : bdtopo-valhalla (recommandé), bdtopo-iso (optimisé), bdtopo-pgr (avec contraintes)"
                    },
                    "profile": {"type": "string", "description": "Mode de transport : car (voiture, défaut) ou pedestrian (piéton). Vérifier disponibilité par ressource."},
                    "direction": {
                        "type": "string",
                        "default": "departure",
                        "description": "Sens du calcul : departure (depuis le point vers destinations) ou arrival (depuis origines vers le point)"
                    },
                    "time_unit": {
                        "type": "string",
                        "default": "minute",
                        "description": "Unité de temps pour cost_type=time : second, minute (défaut), hour"
                    },
                    "distance_unit": {
                        "type": "string",
                        "default": "kilometer",
                        "description": "Unité de distance pour cost_type=distance : meter, kilometer (défaut), mile"
                    },
                    "geometry_format": {
                        "type": "string",
                        "default": "geojson",
                        "description": "Format de géométrie : geojson (Polygon GeoJSON, défaut) ou polyline (Encoded Polyline)"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Contraintes de routage (nécessite bdtopo-pgr, uniquement 'banned'). Ex: [{\"constraintType\": \"banned\", \"key\": \"wayType\", \"operator\": \"=\", \"value\": \"autoroute\"}]"
                    },
                    "crs": {
                        "type": "string",
                        "default": "EPSG:4326",
                        "description": "Système de coordonnées : EPSG:4326 (WGS84, défaut), EPSG:2154 (Lambert 93), etc."
                    }
                },
                "required": ["point", "cost_value"],
            },
        ),

        # IGN ALTIMETRIE (3 outils)
        Tool(
            name="get_altimetry_resources",
            description="""Récupérer la liste des ressources altimétriques disponibles (MNT, MNS, etc.) avec l'API IGN Géoplateforme.

📍 SERVICE : API Altimétrie IGN Géoplateforme (données ouvertes, sans clé API)
🔄 LIMITE : Jusqu'à 5 requêtes/seconde
🗺️ SOURCE : RGE ALTI®, BD ALTI®, et autres Modèles Numériques de Terrain/Surface

ENDPOINT :
- Liste ressources : https://data.geopf.fr/altimetrie/resources
- Détails ressource : https://data.geopf.fr/altimetrie/resources/{id_ressource}

TYPES DE RESSOURCES DISPONIBLES :

1. **Données nationales simples** :
   - Couverture nationale ou mondiale
   - MNT (Modèle Numérique de Terrain) : surface du sol sans végétation/bâtiments
   - Exemple : ign_rge_alti_wld (RGE ALTI® mondial)

2. **MNT/MNS avec métadonnées** :
   - MNT : Modèle Numérique de Terrain (sol nu)
   - MNS : Modèle Numérique de Surface (surface visible, avec végétation/bâti)
   - Métadonnées dynamiques : source de mesure, précision, distance d'interpolation
   - Exemple : RGE ALTI indique "Distance d'interpolation inférieure à 1 m"

3. **Ressources superposées/juxtaposées** :
   - Combinaison de plusieurs sources pour couverture étendue
   - Gestion automatique des priorités entre sources

INFORMATIONS RETOURNÉES PAR RESSOURCE :

- **id** : Identifiant unique de la ressource
- **titre** : Nom descriptif
- **description** : Description détaillée de la ressource
- **source_name** : Nom de la source de données (RGE ALTI, BD ALTI, etc.)
- **source_measure** : Type de mesure
  * "Fixed value" : Valeur fixe (résolution constante)
  * "Dynamic value" : Valeur dynamique (précision variable selon zone)
- **coverage** : Zone de couverture géographique
- **resolution** : Résolution spatiale (ex: 1m, 5m, 25m)
- **precision** : Précision altimétrique (métrique)

PRINCIPALES RESSOURCES IGN :

- **ign_rge_alti_wld** : RGE ALTI® couverture mondiale (recommandé par défaut)
  * Haute précision sur France métropolitaine
  * Couverture mondiale avec dégradation progressive
  * Résolution 1m à 5m selon zones

- **ign_bd_alti_75m** : BD ALTI® 75m
  * Couverture France métropolitaine
  * Résolution 75m
  * Précision métrique

- **ign_bd_alti_25m** : BD ALTI® 25m
  * Couverture France métropolitaine
  * Résolution 25m
  * Précision métrique améliorée

USAGE :

Cette opération de découverte permet de :
1. Lister toutes les ressources disponibles pour un usage
2. Vérifier la couverture géographique d'une ressource
3. Comparer les résolutions et précisions
4. Choisir la ressource adaptée avant appel à get_elevation ou get_elevation_line

WORKFLOW RECOMMANDÉ :

1. **Découverte** : Appeler get_altimetry_resources pour lister les ressources
2. **Analyse** : Comparer résolution, précision, couverture selon besoin
3. **Sélection** : Choisir la ressource appropriée (par défaut : ign_rge_alti_wld)
4. **Utilisation** : Utiliser l'id de la ressource dans get_elevation ou get_elevation_line

EXEMPLES D'UTILISATION :

1. Lister toutes les ressources disponibles :
   (aucun paramètre requis, retourne la liste complète)

2. Cas d'usage typiques :
   - Cartographie précise → ign_rge_alti_wld (1-5m)
   - Analyse régionale → ign_bd_alti_25m
   - Études à grande échelle → ign_bd_alti_75m

CAS D'USAGE :

- 🏔️ Planification de randonnées et trails
- 📊 Analyses de visibilité et exposition
- 🏗️ Études de projets d'aménagement
- 🌊 Modélisation hydraulique et bassins versants
- 📡 Calculs de lignes de vue (télécommunications)
- 🚁 Planification de vols de drones
- 🗺️ Production de cartes topographiques""",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_elevation",
            description="""Récupérer l'altitude d'un ou plusieurs points géographiques avec l'API Altimétrie IGN Géoplateforme.

📍 SERVICE : API Altimétrie IGN Géoplateforme (données ouvertes, sans clé API)
🔄 LIMITE : Jusqu'à 5 requêtes/seconde
📏 LIMITE POINTS : Maximum 5 000 points par requête
🎯 PRÉCISION : Altitudes arrondies à 2 décimales

ENDPOINT :
- GET/POST : https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json

OPÉRATION : ALTITUDE PONCTUELLE

Obtenir l'altitude précise d'un ou plusieurs points géographiques à partir de Modèles Numériques de Terrain (MNT).

COORDONNÉES :

- **Format** : Listes de longitudes et latitudes séparées par délimiteur
- **Longitude** : -180° à +180° (WGS84)
- **Latitude** : -90° à +90° (WGS84)
- **Délimiteurs supportés** : | (pipe), ; (point-virgule), , (virgule)
- **Nombre de points** : 1 à 5 000 par requête
- ⚠️ **Important** : Même nombre de longitudes et latitudes obligatoire

RESSOURCES DISPONIBLES :

- **ign_rge_alti_wld** (DÉFAUT RECOMMANDÉ) :
  * RGE ALTI® couverture mondiale
  * Haute précision France métropolitaine (1-5m)
  * Couverture mondiale dégradée

- **ign_bd_alti_25m** :
  * BD ALTI® 25m France métropolitaine
  * Résolution 25m, précision métrique

- **ign_bd_alti_75m** :
  * BD ALTI® 75m France métropolitaine
  * Résolution 75m, analyses à grande échelle

Voir get_altimetry_resources pour liste complète et détails.

PARAMÈTRES :

1. **lon** (obligatoire) : Longitude(s)
   - Format : "2.3522" (point unique) ou "2.3|2.4|2.5" (multiples)
   - Séparateur : selon paramètre delimiter (défaut |)

2. **lat** (obligatoire) : Latitude(s)
   - Format : "48.8566" (point unique) ou "48.8|48.9|49.0" (multiples)
   - Même nombre que lon

3. **resource** (optionnel) : Ressource altimétrique
   - Défaut : "ign_rge_alti_wld"
   - Utiliser get_altimetry_resources pour découvrir les options

4. **delimiter** (optionnel) : Séparateur
   - Valeurs : "|" (défaut), ";", ","
   - Doit être cohérent pour lon et lat

5. **zonly** (optionnel) : Format de réponse simplifié
   - false (défaut) : Réponse complète {lon, lat, z, acc}
   - true : Tableau simple d'altitudes [z1, z2, z3, ...]

6. **measures** (optionnel) : Métadonnées multi-sources
   - false (défaut) : Altitude simple
   - true : Inclut source_name, source_measure, titre ressource
   - Utile pour ressources superposées/juxtaposées

FORMAT DE RÉPONSE :

**Réponse standard (zonly=false)** :
```json
{
  "elevations": [
    {"lon": 2.3522, "lat": 48.8566, "z": 35.17, "acc": "Précision mètre"},
    {"lon": 6.8651, "lat": 45.8326, "z": 4759.23, "acc": "Haute précision"}
  ]
}
```

**Réponse simplifiée (zonly=true)** :
```json
{
  "elevations": [35.17, 4759.23, 121.45]
}
```

**Réponse avec métadonnées (measures=true)** :
```json
{
  "elevations": [
    {
      "lon": 2.3522, "lat": 48.8566, "z": 35.17, "acc": "1m",
      "measures": [
        {
          "source_name": "RGE ALTI",
          "source_measure": "Dynamic value",
          "resource_title": "RGE ALTI® - France métropolitaine",
          "z": 35.17
        }
      ]
    }
  ]
}
```

VALEURS SPÉCIALES :

- **-99999** : Valeur "no data" pour zones non couvertes par la ressource
  * Points en mer
  * Zones hors couverture de la ressource
  * Données manquantes

EXEMPLES D'UTILISATION :

1. Altitude d'un point unique (Tour Eiffel, Paris) :
   lon="2.2945", lat="48.8584", resource="ign_rge_alti_wld"
   → Résultat : ~35 mètres

2. Altitude de plusieurs sommets français :
   lon="6.8651|4.8357|0.1410", lat="45.8326|45.7640|-0.5792"
   → Mont Blanc (4759m), Lyon (~200m), Bordeaux (~50m)

3. Profil simplifié avec zonly (pour graphique) :
   lon="2.0|2.1|2.2|2.3|2.4", lat="48.8|48.8|48.8|48.8|48.8", zonly=true
   → Tableau simple : [45.2, 52.1, 38.9, 35.4, 41.7]

4. Délimiteur point-virgule :
   lon="2.3;2.4;2.5", lat="48.8;48.9;49.0", delimiter=";"

5. Métadonnées multi-sources (ressource composite) :
   lon="2.35", lat="48.85", measures=true
   → Détails de la source de données utilisée

6. Calcul d'altitudes pour itinéraire (50 points) :
   lon="2.3|2.31|2.32|...", lat="48.8|48.81|48.82|...", zonly=true
   → Altitudes pour profil altimétrique

WORKFLOW RECOMMANDÉ :

1. **Découverte** (optionnel) : Appeler get_altimetry_resources pour choisir ressource
2. **Préparation** : Formater coordonnées lon/lat avec délimiteur cohérent
3. **Appel** : Requête get_elevation avec paramètres appropriés
4. **Traitement** :
   - Vérifier z != -99999 (données valides)
   - Utiliser zonly=true pour intégration graphique simplifiée
   - Utiliser measures=true pour audit de sources de données

CAS D'USAGE PRATIQUES :

- 🏔️ **Randonnée** : Altitude de refuges, sommets, cols
- 📊 **Cartographie** : Annotations altimétriques sur cartes
- 🏗️ **BTP** : Altitude de points de construction, nivellement
- 🌊 **Hydraulique** : Altitude de points d'intérêt pour bassins versants
- ✈️ **Aviation** : Altitude terrain pour planification vol
- 📡 **Télécoms** : Altitude antennes/relais pour calculs de portée
- 🚴 **Cyclisme/Running** : Altitude de parcours pour dénivelés
- 🎯 **Géolocalisation** : Enrichissement de coordonnées GPS avec altitude

PERFORMANCE :

- Requête unique : ~100ms pour 1 point
- Requête batch : ~500ms pour 5000 points
- ⚡ **Optimisation** : Regrouper les points en batch plutôt que requêtes individuelles

NOTES IMPORTANTES :

- Altitudes exprimées en mètres au-dessus du niveau de la mer (NGF pour France)
- Précision dépend de la ressource et de la zone géographique
- Pour profils altimétriques interpolés, utiliser get_elevation_line à la place
- CRS : EPSG:4326 (WGS84) uniquement pour les coordonnées d'entrée""",
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "string",
                        "description": "Longitude(s) séparée(s) par délimiteur (ex: '2.3522' ou '2.3|2.4|2.5'). Plage: -180 à +180. Max: 5000 points."
                    },
                    "lat": {
                        "type": "string",
                        "description": "Latitude(s) séparée(s) par délimiteur (ex: '48.8566' ou '48.8|48.9|49.0'). Plage: -90 à +90. Même nombre que lon."
                    },
                    "resource": {
                        "type": "string",
                        "default": "ign_rge_alti_wld",
                        "description": "Ressource altimétrique : ign_rge_alti_wld (mondial, défaut), ign_bd_alti_25m, ign_bd_alti_75m. Voir get_altimetry_resources."
                    },
                    "delimiter": {
                        "type": "string",
                        "default": "|",
                        "description": "Séparateur de coordonnées : | (pipe, défaut), ; (point-virgule), ou , (virgule)"
                    },
                    "zonly": {
                        "type": "boolean",
                        "default": False,
                        "description": "true: retourne tableau simple d'altitudes [z1,z2,...]. false (défaut): objets complets {lon,lat,z,acc}"
                    },
                    "measures": {
                        "type": "boolean",
                        "default": False,
                        "description": "true: inclut métadonnées multi-sources (source_name, source_measure, titre). false (défaut): altitude simple"
                    },
                },
                "required": ["lon", "lat"],
            },
        ),
        Tool(
            name="get_elevation_line",
            description="""Calculer un profil altimétrique le long d'une ligne (trajet) avec dénivelés positif/négatif.

📍 SERVICE : API Altimétrie IGN Géoplateforme (données ouvertes, sans clé API)
🔄 LIMITE : Jusqu'à 5 requêtes/seconde
📏 LIMITE ÉCHANTILLONNAGE : 2 à 5 000 points par requête
🎯 PRÉCISION : Altitudes arrondies à 2 décimales

ENDPOINT :
- GET/POST : https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevationLine.json

OPÉRATION : PROFIL ALTIMÉTRIQUE EN LONG

Calcule un profil altimétrique interpolé le long d'une polyligne définie par plusieurs points. Contrairement à get_elevation qui retourne les altitudes ponctuelles, cet outil :
- **Interpole** les altitudes entre les points définis
- **Échantillonne** la ligne en un nombre configurable de points
- **Calcule** les dénivelés positifs et négatifs cumulés

COORDONNÉES DE LA LIGNE :

- **Format** : Minimum 2 points (départ et arrivée)
- **Longitude** : -180° à +180° (WGS84)
- **Latitude** : -90° à +90° (WGS84)
- **Délimiteurs supportés** : | (pipe), ; (point-virgule), , (virgule)
- ⚠️ **Important** : Même nombre de longitudes et latitudes obligatoire

RESSOURCES DISPONIBLES :

- **ign_rge_alti_wld** (DÉFAUT RECOMMANDÉ) :
  * RGE ALTI® couverture mondiale
  * Haute précision France métropolitaine (1-5m)
  * Idéal pour randonnées, cyclisme

- **ign_bd_alti_25m** :
  * BD ALTI® 25m France métropolitaine
  * Résolution 25m pour analyses régionales

- **ign_bd_alti_75m** :
  * BD ALTI® 75m France métropolitaine
  * Grandes distances, analyses macro

PARAMÈTRES :

1. **lon** (obligatoire) : Longitudes de la polyligne
   - Format : "2.3|2.4|2.5" (minimum 2 points)
   - Définit le tracé horizontal de la ligne
   - Séparateur : selon paramètre delimiter

2. **lat** (obligatoire) : Latitudes de la polyligne
   - Format : "48.8|48.9|49.0" (minimum 2 points)
   - Même nombre que lon

3. **sampling** (optionnel) : Nombre de points d'échantillonnage
   - Plage : 2 à 5 000
   - Défaut : nombre de couples lon/lat fournis
   - Plus élevé = profil plus détaillé mais temps calcul supérieur
   - Recommandations :
     * 50-100 : Randonnée courte (< 10 km)
     * 100-500 : Randonnée longue (10-50 km)
     * 500-1000 : Cyclosportive, ultra-trail
     * > 1000 : Routes nationales, analyses détaillées

4. **profile_mode** (optionnel) : Mode de calcul
   - **simple** (défaut) : Interpolation linéaire rapide
   - **accurate** : Précision accrue, échantillonnage plus fin
   - Utiliser "accurate" pour :
     * Terrains montagneux accidentés
     * Besoins de précision élevée
     * Calculs de dénivelés exacts pour compétitions

5. **resource** (optionnel) : Ressource altimétrique
   - Défaut : "ign_rge_alti_wld"
   - Voir get_altimetry_resources pour options

6. **delimiter** (optionnel) : Séparateur
   - Valeurs : "|" (défaut), ";", ","
   - Cohérent pour lon et lat

7. **zonly** (optionnel) : Format de réponse simplifié
   - false (défaut) : Réponse complète avec lon, lat, z
   - true : Tableau simple d'altitudes

FORMAT DE RÉPONSE :

**Réponse complète (zonly=false)** :
```json
{
  "elevations": [
    {"lon": 2.3, "lat": 48.8, "z": 150.23},
    {"lon": 2.31, "lat": 48.81, "z": 175.67},
    {"lon": 2.32, "lat": 48.82, "z": 165.12},
    ...
  ],
  "positiveHeightDifference": 245.8,
  "negativeHeightDifference": 189.3
}
```

**Réponse simplifiée (zonly=true)** :
```json
{
  "elevations": [150.23, 175.67, 165.12, 180.45, ...],
  "positiveHeightDifference": 245.8,
  "negativeHeightDifference": 189.3
}
```

DÉNIVELÉS CALCULÉS :

- **positiveHeightDifference** (D+) : Dénivelé positif cumulé en mètres
  * Somme de toutes les montées
  * Exemple : 1200m D+ pour un col de montagne

- **negativeHeightDifference** (D-) : Dénivelé négatif cumulé en mètres
  * Somme de toutes les descentes (valeur absolue)
  * Exemple : 800m D- pour descente

VALEURS SPÉCIALES :

- **-99999** : "no data" pour zones non couvertes
  * Portions en mer
  * Données manquantes

EXEMPLES D'UTILISATION :

1. Profil simple randonnée (5 points, 50 échantillons) :
   lon="2.3|2.32|2.34|2.36|2.38", lat="48.8|48.82|48.84|48.86|48.88",
   sampling=50, profile_mode="simple"
   → Profil interpolé avec D+/D-

2. Profil précis ascension Mont Blanc (trace GPX simplifiée) :
   lon="6.86|6.87|6.865", lat="45.82|45.83|45.832",
   sampling=200, profile_mode="accurate", resource="ign_rge_alti_wld"
   → D+ ~2000m depuis refuge

3. Cyclosportive (étape de montagne) :
   lon="long_trace_avec_10_points", lat="lat_trace_avec_10_points",
   sampling=500, profile_mode="accurate"
   → Profil détaillé pour calculateur de watts

4. Profil simplifié pour graphique (zonly) :
   lon="2.0|2.5|3.0", lat="48.0|48.5|49.0",
   sampling=100, zonly=true
   → Tableau simple pour affichage direct

5. Itinéraire routier Paris → Lyon (route simplifiée) :
   lon="2.35|3.0|3.5|4.0|4.5|4.84", lat="48.85|48.5|47.5|46.5|46.0|45.76",
   sampling=300
   → Profil altimétrique national

6. Trail ultra-distance avec délimiteur ; :
   lon="2.3;2.4;2.5;2.6", lat="48.8;48.9;49.0;49.1",
   delimiter=";", sampling=1000, profile_mode="accurate"
   → Profil haute précision pour analyse

WORKFLOW RECOMMANDÉ :

1. **Définition du tracé** :
   - Obtenir coordonnées GPS du parcours (GPX, itinéraire calculate_route, etc.)
   - Simplifier si trop de points (garder points stratégiques : sommets, cols, vallées)

2. **Choix du sampling** :
   - Distance courte (< 10 km) : 50-100
   - Distance moyenne (10-50 km) : 100-500
   - Longue distance (> 50 km) : 500-1000+

3. **Choix du mode** :
   - Montagne/terrain accidenté : "accurate"
   - Plaine/vitesse : "simple"

4. **Appel API** : get_elevation_line avec paramètres

5. **Exploitation** :
   - Afficher graphique altitude vs distance
   - Calculer pentes moyennes/maximales
   - Estimer temps de parcours (D+ influence)
   - Identifier sections difficiles

CAS D'USAGE PRATIQUES :

- 🏔️ **Randonnée/Trail** : Profils de sentiers GR, cols alpins, ultra-trails
- 🚴 **Cyclisme** : Profils étapes Tour de France, cyclosportives, cols mythiques
- 🏃 **Running** : Parcours courses nature, semi-marathons vallonnés
- 🏗️ **BTP** : Profils de tracés routiers, lignes ferroviaires, canalisations
- 🌊 **Hydraulique** : Profils de cours d'eau, canaux, lignes de crête
- 📊 **Cartographie** : Coupes topographiques pour cartes IGN
- ✈️ **Aviation** : Profils de trajectoires d'approche
- 🎿 **Sports d'hiver** : Profils de pistes de ski, difficultés

INTÉGRATION AVEC AUTRES OUTILS :

- **calculate_route** → get_elevation_line :
  1. Calculer itinéraire routier avec calculate_route
  2. Extraire geometry (LineString GeoJSON)
  3. Convertir en lon/lat avec sampling adapté
  4. Calculer profil altimétrique avec get_elevation_line

- **get_wfs_features** → get_elevation_line :
  1. Récupérer tracé GR (sentiers IGN) via WFS
  2. Extraire coordonnées du tracé
  3. Calculer profil avec get_elevation_line

PERFORMANCE :

- 2 points, 50 samples : ~150ms
- 10 points, 500 samples : ~400ms
- 20 points, 1000 samples (accurate) : ~800ms
- ⚡ **Optimisation** :
  * Simplifier trace d'entrée (garder points clés)
  * Ajuster sampling selon besoin (pas toujours nécessaire 5000)

NOTES IMPORTANTES :

- Altitudes en mètres NGF (France) ou niveau mer (monde)
- L'interpolation suit la ligne droite entre points, pas le terrain réel
- Pour tracé précis suivant routes/sentiers, augmenter le sampling
- D+/D- prennent en compte TOUTES les variations, même mineures
- Pour compatibilité GPX : exporter elevations + reconstruire GPX avec altitudes""",
            inputSchema={
                "type": "object",
                "properties": {
                    "lon": {
                        "type": "string",
                        "description": "Longitudes des points de la polyligne séparés par délimiteur (minimum 2). Ex: '2.3|2.4|2.5|2.6'"
                    },
                    "lat": {
                        "type": "string",
                        "description": "Latitudes des points de la polyligne séparés par délimiteur (minimum 2, même nombre que lon). Ex: '48.8|48.9|49.0|49.1'"
                    },
                    "sampling": {
                        "type": "integer",
                        "default": 50,
                        "description": "Nombre de points d'échantillonnage sur la ligne (2-5000). Plus élevé = profil plus détaillé. Défaut: nombre de points fournis"
                    },
                    "profile_mode": {
                        "type": "string",
                        "default": "simple",
                        "description": "Mode de calcul : 'simple' (interpolation rapide, défaut) ou 'accurate' (précision accrue, montagne)"
                    },
                    "resource": {
                        "type": "string",
                        "default": "ign_rge_alti_wld",
                        "description": "Ressource altimétrique : ign_rge_alti_wld (mondial, défaut), ign_bd_alti_25m, ign_bd_alti_75m"
                    },
                    "delimiter": {
                        "type": "string",
                        "default": "|",
                        "description": "Séparateur de coordonnées : | (pipe, défaut), ; (point-virgule), ou , (virgule)"
                    },
                    "zonly": {
                        "type": "boolean",
                        "default": False,
                        "description": "true: retourne tableau simple d'altitudes. false (défaut): objets complets {lon,lat,z}"
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
