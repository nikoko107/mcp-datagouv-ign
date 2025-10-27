#!/usr/bin/env python3
"""
Système de cache pour réponses API volumineuses (itinéraires, isochrones, WFS)
Évite de saturer le contexte Claude avec des milliers de coordonnées.

Architecture :
- Fichiers JSON temporaires dans ~/.mcp_cache/
- Métadonnées légères retournées à Claude
- Réutilisation via référence cache_id
- Nettoyage automatique après 24h
"""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import hashlib


# Dossier de cache
CACHE_DIR = Path.home() / ".mcp_cache" / "french_opendata"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Durée de vie des fichiers cache (24 heures)
CACHE_TTL_SECONDS = 24 * 3600


def _get_cache_path(cache_id: str) -> Path:
    """Chemin du fichier cache"""
    return CACHE_DIR / f"{cache_id}.json"


def _get_metadata_path(cache_id: str) -> Path:
    """Chemin du fichier métadonnées"""
    return CACHE_DIR / f"{cache_id}_meta.json"


def _generate_cache_id(tool_name: str, params: Dict[str, Any]) -> str:
    """Génère un ID unique basé sur l'outil et les paramètres"""
    # Hash des paramètres pour unicité
    params_str = json.dumps(params, sort_keys=True)
    hash_suffix = hashlib.md5(params_str.encode()).hexdigest()[:8]
    timestamp = int(time.time())
    return f"{tool_name}_{timestamp}_{hash_suffix}"


def _clean_old_cache_files():
    """Nettoie les fichiers cache de plus de 24h"""
    if not CACHE_DIR.exists():
        return

    now = time.time()
    for file in CACHE_DIR.glob("*.json"):
        if file.stat().st_mtime < now - CACHE_TTL_SECONDS:
            try:
                file.unlink()
            except Exception:
                pass  # Ignore les erreurs de suppression


def _extract_summary(data: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """Extrait un résumé léger selon le type de données"""

    if tool_name == "calculate_route":
        # Itinéraire : distance, durée, bbox, nb de steps
        summary = {
            "distance": data.get("distance"),
            "duration": data.get("duration"),
            "bbox": data.get("bbox"),
            "start": data.get("start"),
            "end": data.get("end"),
            "profile": data.get("profile"),
            "resource": data.get("resource"),
        }

        # Compter les coordonnées de géométrie
        geometry = data.get("geometry", {})
        if geometry.get("type") == "LineString":
            coords = geometry.get("coordinates", [])
            summary["geometry_points_count"] = len(coords)
            # Garder seulement début et fin
            if coords:
                summary["geometry_sample"] = {
                    "type": "LineString",
                    "coordinates": [coords[0], coords[-1]] if len(coords) >= 2 else coords
                }

        # Compter les steps
        portions = data.get("portions", [])
        total_steps = 0
        for portion in portions:
            steps = portion.get("steps", [])
            total_steps += len(steps)
        summary["steps_count"] = total_steps

        return summary

    elif tool_name == "calculate_isochrone":
        # Isochrone : point départ, temps/distance, bbox, nb de coordonnées
        summary = {
            "point": data.get("point"),
            "time": data.get("time"),
            "distance": data.get("distance"),
            "direction": data.get("direction"),
            "profile": data.get("profile"),
            "resource": data.get("resource"),
        }

        # Compter les coordonnées du polygone
        geometry = data.get("geometry", {})
        if geometry.get("type") == "Polygon":
            coords = geometry.get("coordinates", [[]])
            if coords and len(coords) > 0:
                summary["geometry_points_count"] = len(coords[0])
                # Garder seulement bbox
                summary["bbox"] = data.get("bbox")
        elif geometry.get("type") == "MultiPolygon":
            total_points = sum(len(ring) for polygon in geometry.get("coordinates", []) for ring in polygon)
            summary["geometry_points_count"] = total_points
            summary["polygons_count"] = len(geometry.get("coordinates", []))
            summary["bbox"] = data.get("bbox")

        return summary

    elif tool_name == "get_wfs_features":
        # WFS : nombre de features, bbox, attributs
        features = data.get("features", [])
        summary = {
            "type": "FeatureCollection",
            "features_count": len(features),
            "typename": data.get("typename"),
            "bbox_filter": data.get("bbox_filter"),
        }

        # Premier feature comme exemple (sans géométrie complète)
        if features:
            first_feature = features[0].copy()
            if "geometry" in first_feature:
                geom = first_feature["geometry"]
                first_feature["geometry"] = {
                    "type": geom.get("type"),
                    "coordinates_count": len(str(geom.get("coordinates", [])))
                }
            summary["sample_feature"] = first_feature

        return summary

    elif tool_name == "get_elevation_line":
        # Profil altimétrique : nb de points, min/max altitude
        summary = {
            "sampling": data.get("sampling"),
            "lon": data.get("lon"),
            "lat": data.get("lat"),
        }

        elevations = data.get("elevations", [])
        summary["points_count"] = len(elevations)

        if elevations:
            altitudes = [e.get("z") for e in elevations if e.get("z") is not None]
            if altitudes:
                summary["altitude_min"] = min(altitudes)
                summary["altitude_max"] = max(altitudes)
                summary["altitude_range"] = max(altitudes) - min(altitudes)

        # Garder premiers et derniers points
        if len(elevations) > 4:
            summary["elevations_sample"] = elevations[:2] + elevations[-2:]
        else:
            summary["elevations_sample"] = elevations

        return summary

    else:
        # Générique : taille JSON
        return {
            "data_size_bytes": len(json.dumps(data)),
            "keys": list(data.keys()) if isinstance(data, dict) else None
        }


def should_cache_response(data: Any, tool_name: str) -> bool:
    """Détermine si la réponse doit être cachée (>10KB ou >100 features)"""

    # Toujours cacher pour ces outils
    if tool_name in ["calculate_route", "calculate_isochrone", "get_elevation_line"]:
        return True

    # WFS : cacher si >50 features
    if tool_name == "get_wfs_features":
        if isinstance(data, dict):
            features = data.get("features", [])
            if len(features) > 50:
                return True

    # Taille JSON >10KB
    json_size = len(json.dumps(data))
    if json_size > 10 * 1024:
        return True

    return False


def cache_response(data: Dict[str, Any], tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cache une réponse volumineuse et retourne des métadonnées légères.

    Returns:
        Dict avec cache_id, summary, et instructions pour récupération
    """
    # Nettoyer vieux fichiers
    _clean_old_cache_files()

    # Générer ID unique
    cache_id = _generate_cache_id(tool_name, params)

    # Sauvegarder données complètes
    cache_path = _get_cache_path(cache_id)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Extraire résumé
    summary = _extract_summary(data, tool_name)

    # Métadonnées
    metadata = {
        "cache_id": cache_id,
        "tool_name": tool_name,
        "params": params,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS)).isoformat(),
        "file_path": str(cache_path),
        "file_size_bytes": cache_path.stat().st_size,
        "summary": summary
    }

    # Sauvegarder métadonnées
    meta_path = _get_metadata_path(cache_id)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Retourner métadonnées légères pour Claude
    return {
        "cached": True,
        "cache_id": cache_id,
        "file_path": str(cache_path),
        "file_size_kb": round(cache_path.stat().st_size / 1024, 2),
        "expires_at": metadata["expires_at"],
        "summary": summary,
        "usage": f"Pour réutiliser ces données, utilisez l'outil 'get_cached_data' avec cache_id='{cache_id}'"
    }


def get_cached_data(cache_id: str, include_full_data: bool = False) -> Optional[Dict[str, Any]]:
    """
    Récupère des données cachées.

    Args:
        cache_id: ID du cache
        include_full_data: Si True, inclut les données complètes (à éviter pour grosses données)

    Returns:
        Métadonnées + optionnellement données complètes
    """
    # Vérifier métadonnées
    meta_path = _get_metadata_path(cache_id)
    if not meta_path.exists():
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Vérifier expiration
    expires_at = datetime.fromisoformat(metadata["expires_at"])
    if datetime.now() > expires_at:
        # Supprimer fichiers expirés
        try:
            _get_cache_path(cache_id).unlink()
            meta_path.unlink()
        except Exception:
            pass
        return None

    result = metadata.copy()

    # Inclure données complètes si demandé
    if include_full_data:
        cache_path = _get_cache_path(cache_id)
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                result["full_data"] = json.load(f)

    return result


def list_cached_items() -> List[Dict[str, Any]]:
    """Liste tous les items en cache avec leurs métadonnées"""
    items = []

    for meta_file in CACHE_DIR.glob("*_meta.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Vérifier si expiré
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if datetime.now() > expires_at:
                continue

            items.append({
                "cache_id": metadata["cache_id"],
                "tool_name": metadata["tool_name"],
                "created_at": metadata["created_at"],
                "expires_at": metadata["expires_at"],
                "file_size_kb": round(metadata["file_size_bytes"] / 1024, 2),
                "summary": metadata["summary"]
            })
        except Exception:
            continue

    return items


def clear_cache():
    """Supprime tous les fichiers cache"""
    for file in CACHE_DIR.glob("*.json"):
        try:
            file.unlink()
        except Exception:
            pass
