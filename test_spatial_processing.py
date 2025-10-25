import base64
import json

import geopandas as gpd
import pytest
import shapely.affinity
from shapely.geometry import MultiPolygon, Point, Polygon

import fiona

from spatial_processing import (
    GeoProcessingError,
    buffer_geodata,
    convert_geodata_format,
    dissolve_geodata,
    explode_geodata,
    get_geodata_bbox,
    intersect_geodata,
    reproject_geodata,
)


@pytest.fixture(scope="module")
def square_geojson() -> str:
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[Polygon([(-1.0, 0.0), (0.0, 1.0), (1.0, 0.0), (0.0, -1.0)])],
        crs="EPSG:4326",
    )
    return gdf.to_json()


@pytest.fixture(scope="module")
def triangle_geojson() -> str:
    gdf = gpd.GeoDataFrame(
        {"name": ["triangle"]},
        geometry=[Polygon([(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)])],
        crs="EPSG:4326",
    )
    return gdf.to_json()


def test_reproject(square_geojson):
    result = reproject_geodata(
        data=square_geojson,
        input_format="geojson",
        target_crs="EPSG:3857",
        output_format="geojson",
    )
    assert result["format"] == "geojson"
    assert result["crs"] == "EPSG:3857"


def test_buffer(square_geojson):
    result = buffer_geodata(
        data=square_geojson,
        input_format="geojson",
        distance=500,
        buffer_crs="EPSG:3857",
        output_crs="EPSG:3857",
    )
    assert result["format"] == "geojson"
    geojson = json.loads(result["data"])
    polygon = shapely.from_geojson(json.dumps(geojson["features"][0]["geometry"]))  # type: ignore[attr-defined]
    assert polygon.area > 0


def test_intersection(square_geojson, triangle_geojson):
    result = intersect_geodata(
        data_a=square_geojson,
        input_format_a="geojson",
        data_b=triangle_geojson,
        input_format_b="geojson",
        target_crs="EPSG:4326",
    )
    assert result["format"] == "geojson"
    payload = json.loads(result["data"])
    assert payload["features"]  # intersection non vide


def test_get_bbox(square_geojson):
    result = get_geodata_bbox(
        data=square_geojson,
        input_format="geojson",
        target_crs="EPSG:4326",
    )
    assert result["format"] == "bbox"
    bounds = result["bounds"]
    assert bounds["minx"] < bounds["maxx"]
    assert bounds["miny"] < bounds["maxy"]


def test_dissolve(square_geojson):
    gdf = gpd.read_file(json.loads(square_geojson))
    gdf["region"] = ["A"]
    enriched = json.loads(gdf.to_json())
    result = dissolve_geodata(
        data=json.dumps(enriched),
        input_format="geojson",
        by="region",
    )
    payload = json.loads(result["data"])
    assert len(payload["features"]) == 1


def test_explode():
    polygon1 = Polygon([(0, 0), (1, 0), (0, 1)])
    polygon2 = shapely.affinity.translate(polygon1, xoff=2.0)  # type: ignore[attr-defined]
    multi = MultiPolygon([polygon1, polygon2])
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[multi], crs="EPSG:4326")
    result = explode_geodata(
        data=gdf.to_json(),
        input_format="geojson",
    )
    payload = json.loads(result["data"])
    assert len(payload["features"]) == 2


@pytest.mark.skipif("ESRI Shapefile" not in fiona.supported_drivers, reason="Shapefile driver non disponible")
def test_convert_to_shapefile(square_geojson):
    result = convert_geodata_format(
        data=square_geojson,
        input_format="geojson",
        output_format="shapefile",
    )
    assert result["format"] == "shapefile"
    decoded = base64.b64decode(result["data"])
    assert len(decoded) > 0


def test_invalid_format_raises(square_geojson):
    with pytest.raises(GeoProcessingError):
        reproject_geodata(
            data=square_geojson,
            input_format="unsupported",
            target_crs="EPSG:3857",
        )
