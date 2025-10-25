"""
Module pour accéder aux services géographiques de l'IGN
Supporte WMTS (tuiles), WMS (cartes), WFS (données vectorielles),
Navigation (itinéraires, isochrones), Altimétrie (altitude, profils)
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import httpx


class IGNGeoServices:
    """Client pour les services géographiques IGN"""

    WMTS_URL = "https://data.geopf.fr/wmts"
    WMS_URL = "https://data.geopf.fr/wms-r"
    WFS_URL = "https://data.geopf.fr/wfs"
    ROUTE_URL = "https://data.geopf.fr/navigation/itineraire"
    ISOCHRONE_URL = "https://data.geopf.fr/navigation/isochrone"
    GETCAPABILITIES_URL = "https://data.geopf.fr/navigation/getcapabilities"
    ALTIMETRY_BASE_URL = "https://data.geopf.fr/altimetrie/1.0"
    ALTIMETRY_RESOURCES_URL = "https://data.geopf.fr/altimetrie/1.0/resources"
    
    NAMESPACES = {
        'wmts': 'http://www.opengis.net/wmts/1.0',
        'ows': 'http://www.opengis.net/ows/1.1',
        'wms': 'http://www.opengis.net/wms',
        'wfs': 'http://www.opengis.net/wfs/2.0',
    }
    
    def __init__(self):
        self._wmts_capabilities = None
        self._wms_capabilities = None
        self._wfs_capabilities = None
    
    async def list_wmts_layers(self, client: httpx.AsyncClient) -> List[Dict]:
        """Liste toutes les couches WMTS disponibles"""
        params = {
            "SERVICE": "WMTS",
            "VERSION": "1.0.0",
            "REQUEST": "GetCapabilities"
        }
        response = await client.get(self.WMTS_URL, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        layers = []
        
        for layer in root.findall('.//wmts:Layer', self.NAMESPACES):
            title_elem = layer.find('ows:Title', self.NAMESPACES)
            abstract_elem = layer.find('ows:Abstract', self.NAMESPACES)
            identifier_elem = layer.find('ows:Identifier', self.NAMESPACES)
            
            if identifier_elem is not None:
                layers.append({
                    'name': identifier_elem.text,
                    'title': title_elem.text if title_elem is not None else '',
                    'abstract': abstract_elem.text if abstract_elem is not None else '',
                })
        
        return layers
    
    async def list_wms_layers(self, client: httpx.AsyncClient) -> List[Dict]:
        """Liste toutes les couches WMS disponibles"""
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetCapabilities"
        }
        response = await client.get(self.WMS_URL, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        layers = []
        
        for layer in root.findall('.//Layer/Layer'):
            name_elem = layer.find('Name')
            title_elem = layer.find('Title')
            abstract_elem = layer.find('Abstract')
            
            if name_elem is not None:
                layers.append({
                    'name': name_elem.text,
                    'title': title_elem.text if title_elem is not None else '',
                    'abstract': abstract_elem.text if abstract_elem is not None else '',
                })
        
        return layers
    
    async def list_wfs_features(self, client: httpx.AsyncClient) -> List[Dict]:
        """Liste tous les types de features WFS"""
        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetCapabilities"
        }
        response = await client.get(self.WFS_URL, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        features = []
        
        for feature_type in root.findall('.//wfs:FeatureType', self.NAMESPACES):
            name_elem = feature_type.find('wfs:Name', self.NAMESPACES)
            title_elem = feature_type.find('wfs:Title', self.NAMESPACES)
            abstract_elem = feature_type.find('wfs:Abstract', self.NAMESPACES)
            
            if name_elem is not None:
                features.append({
                    'name': name_elem.text,
                    'title': title_elem.text if title_elem is not None else '',
                    'abstract': abstract_elem.text if abstract_elem is not None else '',
                })
        
        return features
    
    async def search_layers(self, client: httpx.AsyncClient, service: str, query: str) -> List[Dict]:
        """Recherche des couches par mots-clés"""
        query_lower = query.lower()
        
        if service == "wmts":
            all_layers = await self.list_wmts_layers(client)
        elif service == "wms":
            all_layers = await self.list_wms_layers(client)
        elif service == "wfs":
            all_layers = await self.list_wfs_features(client)
        else:
            raise ValueError(f"Service inconnu: {service}")
        
        return [
            layer for layer in all_layers
            if query_lower in layer.get('title', '').lower() or
               query_lower in layer.get('abstract', '').lower() or
               query_lower in layer.get('name', '').lower()
        ]
    
    def get_wmts_tile_url(self, layer: str, z: int, x: int, y: int) -> str:
        """Génère l'URL d'une tuile WMTS"""
        return (
            f"{self.WMTS_URL}?"
            f"SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&"
            f"LAYER={layer}&STYLE=normal&FORMAT=image/png&"
            f"TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}"
        )
    
    def get_wms_map_url(self, layers: str, bbox: str, width: int, height: int, format: str) -> str:
        """Génère l'URL d'une carte WMS"""
        return (
            f"{self.WMS_URL}?"
            f"SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&"
            f"LAYERS={layers}&STYLES=&FORMAT={format}&"
            f"CRS=EPSG:4326&BBOX={bbox}&WIDTH={width}&HEIGHT={height}"
        )

    async def get_route_capabilities(self, client: httpx.AsyncClient) -> Dict:
        """Récupère les capacités du service de navigation (ressources, profils, optimisations)"""
        response = await client.get(self.GETCAPABILITIES_URL)
        response.raise_for_status()
        return response.json()

    async def calculate_route(
        self,
        client: httpx.AsyncClient,
        start: str,
        end: str,
        resource: str = "bdtopo-osrm",
        profile: Optional[str] = None,
        optimization: str = "fastest",
        intermediates: Optional[List[str]] = None,
        geometry_format: str = "geojson",
        get_steps: bool = True,
        get_bbox: bool = True,
        constraints: Optional[List[Dict]] = None,
        distance_unit: str = "kilometer",
        time_unit: str = "hour"
    ) -> Dict:
        """
        Calcule un itinéraire entre deux points

        Args:
            start: Point de départ au format "longitude,latitude"
            end: Point d'arrivée au format "longitude,latitude"
            resource: Graphe de navigation (bdtopo-osrm, bdtopo-valhalla, bdtopo-pgr)
            profile: Mode de transport (car, pedestrian)
            optimization: Mode de calcul (fastest, shortest)
            intermediates: Liste de points intermédiaires
            geometry_format: Format de la géométrie (geojson, polyline)
            get_steps: Inclure les étapes détaillées
            get_bbox: Inclure l'emprise de l'itinéraire
            constraints: Liste de contraintes (banned, preferred, unpreferred)
            distance_unit: Unité de distance (meter, kilometer, mile)
            time_unit: Unité de temps (second, minute, hour)
        """
        params = {
            "resource": resource,
            "start": start,
            "end": end,
            "optimization": optimization,
            "geometryFormat": geometry_format,
            "getSteps": str(get_steps).lower(),
            "getBbox": str(get_bbox).lower(),
            "distanceUnit": distance_unit,
            "timeUnit": time_unit
        }

        if profile:
            params["profile"] = profile

        if intermediates:
            params["intermediates"] = "|".join(intermediates)

        if constraints:
            import json
            params["constraints"] = json.dumps(constraints)

        response = await client.get(self.ROUTE_URL, params=params)
        response.raise_for_status()
        return response.json()

    async def calculate_isochrone(
        self,
        client: httpx.AsyncClient,
        point: str,
        cost_value: float,
        cost_type: str = "time",
        resource: str = "bdtopo-valhalla",
        profile: Optional[str] = None,
        direction: str = "departure",
        geometry_format: str = "geojson",
        constraints: Optional[List[Dict]] = None,
        distance_unit: str = "kilometer",
        time_unit: str = "hour"
    ) -> Dict:
        """
        Calcule une isochrone ou une isodistance

        Args:
            point: Point central au format "longitude,latitude"
            cost_value: Valeur de temps ou distance
            cost_type: Type de coût (time, distance)
            resource: Graphe de navigation (bdtopo-valhalla, bdtopo-pgr)
            profile: Mode de transport (car, pedestrian)
            direction: Direction de calcul (departure, arrival)
            geometry_format: Format de la géométrie (geojson, polyline)
            constraints: Liste de contraintes (banned uniquement pour isochrone)
            distance_unit: Unité de distance (meter, kilometer, mile)
            time_unit: Unité de temps (second, minute, hour)
        """
        params = {
            "resource": resource,
            "point": point,
            "costValue": str(cost_value),
            "costType": cost_type,
            "direction": direction,
            "geometryFormat": geometry_format,
            "distanceUnit": distance_unit,
            "timeUnit": time_unit
        }

        if profile:
            params["profile"] = profile

        if constraints:
            import json
            params["constraints"] = json.dumps(constraints)

        response = await client.get(self.ISOCHRONE_URL, params=params)
        response.raise_for_status()
        return response.json()

    async def get_altimetry_resources(self, client: httpx.AsyncClient) -> Dict:
        """Récupère la liste des ressources altimétriques disponibles"""
        response = await client.get(self.ALTIMETRY_RESOURCES_URL)
        response.raise_for_status()
        return response.json()

    async def get_elevation(
        self,
        client: httpx.AsyncClient,
        lon: str,
        lat: str,
        resource: str = "ign_rge_alti_wld",
        delimiter: str = "|",
        zonly: bool = False,
        measures: bool = False
    ) -> Dict:
        """
        Récupère l'altitude d'un ou plusieurs points

        Args:
            lon: Longitude(s) séparée(s) par le délimiteur (max 5000 points)
            lat: Latitude(s) séparée(s) par le délimiteur (max 5000 points)
            resource: Ressource altimétrique à utiliser
            delimiter: Séparateur de coordonnées (|, ;, ou ,)
            zonly: Si True, retourne uniquement les valeurs d'altitude
            measures: Si True, inclut les détails de mesure multi-sources

        Returns:
            Dict contenant les altitudes avec coordonnées et précision
        """
        params = {
            "lon": lon,
            "lat": lat,
            "resource": resource,
            "delimiter": delimiter,
            "zonly": str(zonly).lower(),
            "measures": str(measures).lower()
        }

        url = f"{self.ALTIMETRY_BASE_URL}/calcul/alti/rest/elevation.json"
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_elevation_line(
        self,
        client: httpx.AsyncClient,
        lon: str,
        lat: str,
        resource: str = "ign_rge_alti_wld",
        delimiter: str = "|",
        profile_mode: str = "simple",
        sampling: int = 50,
        zonly: bool = False
    ) -> Dict:
        """
        Calcule un profil altimétrique le long d'une ligne

        Args:
            lon: Longitudes des points de la ligne séparés par le délimiteur
            lat: Latitudes des points de la ligne séparés par le délimiteur
            resource: Ressource altimétrique à utiliser
            delimiter: Séparateur de coordonnées (|, ;, ou ,)
            profile_mode: Mode de calcul (simple ou accurate)
            sampling: Nombre de points d'échantillonnage (2-5000)
            zonly: Si True, retourne uniquement les valeurs d'altitude

        Returns:
            Dict contenant le profil avec altitudes et dénivelés positif/négatif
        """
        params = {
            "lon": lon,
            "lat": lat,
            "resource": resource,
            "delimiter": delimiter,
            "profile_mode": profile_mode,
            "sampling": str(sampling),
            "zonly": str(zonly).lower()
        }

        url = f"{self.ALTIMETRY_BASE_URL}/calcul/alti/rest/elevationLine.json"
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
