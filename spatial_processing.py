"""
Traitements spatiaux basés sur GeoPandas pour le serveur MCP français.
Permet de charger des données dans différents formats, d'appliquer des opérations
géométriques (reprojection, buffer, intersection, clip, dissolve, explode) et
d'exporter vers plusieurs formats (GeoJSON, KML, GeoPackage, Shapefile).

Notes :
- Les formats GeoPackage et Shapefile sont échangés sous forme binaire encodée en base64.
- Les formats GeoJSON et KML sont échangés sous forme de texte UTF-8.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import zipfile
from typing import Any, Dict, Optional

import geopandas as gpd
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry


SUPPORTED_FORMATS = {"geojson", "json", "kml", "gpkg", "shapefile"}
TEXT_FORMATS = {"geojson", "json", "kml"}
BINARY_FORMATS = {"gpkg", "shapefile"}
DEFAULT_OUTPUT_FORMAT = "geojson"


class GeoProcessingError(ValueError):
    """Erreur spécifique aux traitements GeoPandas."""


def normalize_format(fmt: str) -> str:
    if not fmt:
        raise GeoProcessingError("Le format n'a pas été fourni.")
    fmt_normalized = fmt.lower()
    if fmt_normalized == "json":
        fmt_normalized = "geojson"
    if fmt_normalized not in SUPPORTED_FORMATS:
        raise GeoProcessingError(
            f"Format « {fmt} » non supporté. Formats acceptés : {', '.join(sorted(SUPPORTED_FORMATS))}."
        )
    return fmt_normalized


def load_geodata(data: str, input_format: str, source_crs: Optional[str] = None) -> gpd.GeoDataFrame:
    fmt = normalize_format(input_format)
    if data is None:
        raise GeoProcessingError("Aucune donnée géographique fournie.")

    with tempfile.TemporaryDirectory() as tmpdir:
        if fmt in {"geojson", "json"}:
            path = os.path.join(tmpdir, "input.geojson")
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        elif fmt == "kml":
            path = os.path.join(tmpdir, "input.kml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        elif fmt == "gpkg":
            path = os.path.join(tmpdir, "input.gpkg")
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
        elif fmt == "shapefile":
            zip_path = os.path.join(tmpdir, "input.zip")
            with open(zip_path, "wb") as f:
                f.write(base64.b64decode(data))
            path = f"zip://{zip_path}"
        else:
            raise GeoProcessingError(f"Format d'entrée non supporté : {fmt}")

        gdf = gpd.read_file(path)

    if gdf.empty:
        raise GeoProcessingError("Le fichier ne contient aucune entité.")

    gdf = gdf.dropna(subset=["geometry"])
    if gdf.empty:
        raise GeoProcessingError("Toutes les géométries sont nulles ou invalides.")

    if source_crs:
        gdf = gdf.set_crs(source_crs, allow_override=True)

    return gdf


def dump_geodata(gdf: gpd.GeoDataFrame, output_format: Optional[str] = None) -> Dict[str, Any]:
    fmt = normalize_format(output_format or DEFAULT_OUTPUT_FORMAT)
    gdf = gdf.dropna(subset=["geometry"])
    if gdf.empty:
        raise GeoProcessingError("Le résultat est vide après l'opération demandée.")

    crs = gdf.crs.to_string() if gdf.crs else None

    if fmt == "geojson":
        return {
            "format": "geojson",
            "encoding": "utf-8",
            "crs": crs,
            "data": gdf.to_json(),
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        if fmt == "kml":
            path = os.path.join(tmpdir, "output.kml")
            gdf.to_file(path, driver="KML")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "format": "kml",
                "encoding": "utf-8",
                "crs": crs,
                "data": content,
            }

        if fmt == "gpkg":
            path = os.path.join(tmpdir, "output.gpkg")
            gdf.to_file(path, driver="GPKG")
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode("ascii")
            return {
                "format": "gpkg",
                "encoding": "base64",
                "crs": crs,
                "data": content,
            }

        if fmt == "shapefile":
            shp_path = os.path.join(tmpdir, "output.shp")
            gdf.to_file(shp_path, driver="ESRI Shapefile")
            zip_path = os.path.join(tmpdir, "output.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for filename in os.listdir(tmpdir):
                    if filename.startswith("output.") and filename != "output.zip":
                        zf.write(os.path.join(tmpdir, filename), arcname=filename)
            with open(zip_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("ascii")
            return {
                "format": "shapefile",
                "encoding": "base64",
                "crs": crs,
                "data": content,
            }

    raise GeoProcessingError(f"Format de sortie non géré : {fmt}")


def ensure_same_crs(
    gdf_a: gpd.GeoDataFrame,
    gdf_b: gpd.GeoDataFrame,
    target_crs: Optional[str] = None,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    if target_crs:
        gdf_a = gdf_a.to_crs(target_crs)
        gdf_b = gdf_b.to_crs(target_crs)
        return gdf_a, gdf_b

    if gdf_a.crs and gdf_b.crs:
        if gdf_a.crs == gdf_b.crs:
            return gdf_a, gdf_b
        return gdf_a, gdf_b.to_crs(gdf_a.crs)

    raise GeoProcessingError(
        "Les CRS des deux jeux de données sont inconnus ou incompatibles. "
        "Fournissez `source_crs` pour chaque entrée ou `target_crs`."
    )


def reproject_geodata(
    data: str,
    input_format: str,
    target_crs: str,
    source_crs: Optional[str] = None,
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    gdf = load_geodata(data, input_format, source_crs)
    if not target_crs:
        raise GeoProcessingError("Le CRS cible `target_crs` est requis.")
    gdf = gdf.to_crs(target_crs)
    return dump_geodata(gdf, output_format)


def buffer_geodata(
    data: str,
    input_format: str,
    distance: float,
    source_crs: Optional[str] = None,
    buffer_crs: Optional[str] = None,
    output_crs: Optional[str] = None,
    output_format: Optional[str] = None,
    cap_style: Optional[str] = None,
    join_style: Optional[str] = None,
    mitre_limit: Optional[float] = None,
    single_sided: Optional[bool] = None,
    resolution: int = 16,
) -> Dict[str, Any]:
    if distance is None:
        raise GeoProcessingError("Le paramètre `distance` est requis pour le buffer.")

    gdf = load_geodata(data, input_format, source_crs)
    working_crs = buffer_crs or (gdf.crs.to_string() if gdf.crs else None)
    if not working_crs:
        raise GeoProcessingError(
            "Impossible de déterminer un CRS métrique pour calculer un buffer. "
            "Fournissez `source_crs` ou `buffer_crs`."
        )

    gdf = gdf.to_crs(working_crs)

    cap_style_map = {"round": 1, "flat": 2, "square": 3}
    join_style_map = {"round": 1, "mitre": 2, "miter": 2, "bevel": 3}

    buffer_kwargs: Dict[str, Any] = {"resolution": resolution}
    if cap_style:
        if cap_style not in cap_style_map:
            raise GeoProcessingError(f"cap_style doit être parmi {list(cap_style_map)}.")
        buffer_kwargs["cap_style"] = cap_style_map[cap_style]
    if join_style:
        if join_style not in join_style_map:
            raise GeoProcessingError(f"join_style doit être parmi {list(join_style_map)}.")
        buffer_kwargs["join_style"] = join_style_map[join_style]
    if mitre_limit is not None:
        buffer_kwargs["mitre_limit"] = mitre_limit
    if single_sided is not None:
        buffer_kwargs["single_sided"] = single_sided

    buffered = gdf.copy()
    buffered["geometry"] = buffered.geometry.buffer(distance, **buffer_kwargs)

    if output_crs:
        buffered = buffered.to_crs(output_crs)

    return dump_geodata(buffered, output_format)


def intersect_geodata(
    data_a: str,
    input_format_a: str,
    data_b: str,
    input_format_b: str,
    source_crs_a: Optional[str] = None,
    source_crs_b: Optional[str] = None,
    target_crs: Optional[str] = None,
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    gdf_a = load_geodata(data_a, input_format_a, source_crs_a)
    gdf_b = load_geodata(data_b, input_format_b, source_crs_b)
    gdf_a, gdf_b = ensure_same_crs(gdf_a, gdf_b, target_crs)
    intersection = gpd.overlay(gdf_a, gdf_b, how="intersection", keep_geom_type=True)
    return dump_geodata(intersection, output_format)


def clip_geodata(
    data: str,
    input_format: str,
    clip_data: str,
    clip_format: str,
    source_crs: Optional[str] = None,
    clip_source_crs: Optional[str] = None,
    target_crs: Optional[str] = None,
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    gdf = load_geodata(data, input_format, source_crs)
    clip_gdf = load_geodata(clip_data, clip_format, clip_source_crs)
    gdf, clip_gdf = ensure_same_crs(gdf, clip_gdf, target_crs)
    clipped = gpd.clip(gdf, clip_gdf)
    return dump_geodata(clipped, output_format)


def convert_geodata_format(
    data: str,
    input_format: str,
    output_format: str,
    source_crs: Optional[str] = None,
) -> Dict[str, Any]:
    gdf = load_geodata(data, input_format, source_crs)
    return dump_geodata(gdf, output_format)


def get_geodata_bbox(
    data: str,
    input_format: str,
    source_crs: Optional[str] = None,
    target_crs: Optional[str] = None,
) -> Dict[str, Any]:
    gdf = load_geodata(data, input_format, source_crs)
    if target_crs:
        gdf = gdf.to_crs(target_crs)
    minx, miny, maxx, maxy = gdf.total_bounds
    return {
        "format": "bbox",
        "crs": gdf.crs.to_string() if gdf.crs else None,
        "bounds": {
            "minx": minx,
            "miny": miny,
            "maxx": maxx,
            "maxy": maxy,
        },
    }


def dissolve_geodata(
    data: str,
    input_format: str,
    by: Optional[str] = None,
    aggregations: Optional[Dict[str, str]] = None,
    source_crs: Optional[str] = None,
    target_crs: Optional[str] = None,
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    gdf = load_geodata(data, input_format, source_crs)
    if target_crs:
        gdf = gdf.to_crs(target_crs)

    aggfunc = aggregations or "first"
    dissolved = gdf.dissolve(by=by, aggfunc=aggfunc)
    dissolved = dissolved.reset_index(drop=by is None)

    return dump_geodata(dissolved, output_format)


def explode_geodata(
    data: str,
    input_format: str,
    source_crs: Optional[str] = None,
    keep_index: bool = False,
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    gdf = load_geodata(data, input_format, source_crs)
    exploded = gdf.copy()
    exploded = exploded.explode(index_parts=keep_index, ignore_index=not keep_index)
    return dump_geodata(exploded, output_format)
