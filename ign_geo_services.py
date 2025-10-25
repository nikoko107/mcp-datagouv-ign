"""
Module pour accéder aux services géographiques de l'IGN
Supporte WMTS (tuiles), WMS (cartes), WFS (données vectorielles)
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import httpx


class IGNGeoServices:
    """Client pour les services géographiques IGN"""

    WMTS_URL = "https://data.geopf.fr/wmts"
    WMS_URL = "https://data.geopf.fr/wms-r"
    WFS_URL = "https://data.geopf.fr/wfs"
    NAVIGATION_ROUTE_URL = "https://data.geopf.fr/navigation/itineraire"
    NAVIGATION_ISOCHRONE_URL = "https://data.geopf.fr/navigation/isochrone"
    
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

    async def calculate_route(
        self,
        client: httpx.AsyncClient,
        start_lon: float,
        start_lat: float,
        end_lon: float,
        end_lat: float,
        resource: str = "bdtopo-valhalla",
        profile: str = "car",
        optimization: str = "fastest",
        get_steps: bool = True,
        geometry_format: str = "geojson",
        intermediates: Optional[str] = None,
        constraints: Optional[str] = None
    ) -> Dict:
        """
        Calcule un itinéraire entre deux points

        Args:
            client: Client HTTP asyncio
            start_lon: Longitude du point de départ
            start_lat: Latitude du point de départ
            end_lon: Longitude du point d'arrivée
            end_lat: Latitude du point d'arrivée
            resource: Moteur de calcul (bdtopo-valhalla, bdtopo-osrm, bdtopo-pgr)
            profile: Profil de déplacement (car, pedestrian)
            optimization: Type d'optimisation (fastest, shortest)
            get_steps: Retourner les instructions détaillées
            geometry_format: Format de la géométrie (geojson, polyline)
            intermediates: Points intermédiaires (format: lon1,lat1|lon2,lat2)
            constraints: Contraintes de voyage (ex: avoidTolls)

        Returns:
            Dict contenant l'itinéraire calculé
        """
        params = {
            "resource": resource,
            "start": f"{start_lon},{start_lat}",
            "end": f"{end_lon},{end_lat}",
            "profile": profile,
            "optimization": optimization,
            "geometryFormat": geometry_format,
        }

        if get_steps:
            params["getSteps"] = "true"

        if intermediates:
            params["intermediates"] = intermediates

        if constraints:
            params["constraints"] = constraints

        response = await client.get(self.NAVIGATION_ROUTE_URL, params=params)
        response.raise_for_status()
        return response.json()

    async def calculate_isochrone(
        self,
        client: httpx.AsyncClient,
        lon: float,
        lat: float,
        cost_value: int,
        resource: str = "bdtopo-valhalla",
        profile: str = "car",
        cost_type: str = "time",
        direction: str = "departure",
        geometry_format: str = "geojson",
        constraints: Optional[str] = None
    ) -> Dict:
        """
        Calcule une isochrone ou isodistance depuis/vers un point

        Args:
            client: Client HTTP asyncio
            lon: Longitude du point
            lat: Latitude du point
            cost_value: Valeur de coût (temps en secondes ou distance en mètres)
            resource: Moteur de calcul (bdtopo-valhalla, bdtopo-osrm, bdtopo-pgr)
            profile: Profil de déplacement (car, pedestrian)
            cost_type: Type de coût (time pour isochrone, distance pour isodistance)
            direction: Direction (departure depuis le point, arrival vers le point)
            geometry_format: Format de la géométrie (geojson, polyline)
            constraints: Contraintes de voyage (ex: avoidTolls)

        Returns:
            Dict contenant l'isochrone/isodistance calculée en GeoJSON
        """
        params = {
            "resource": resource,
            "point": f"{lon},{lat}",
            "costType": cost_type,
            "costValue": str(cost_value),
            "profile": profile,
            "direction": direction,
            "geometryFormat": geometry_format,
        }

        if constraints:
            params["constraints"] = constraints

        response = await client.get(self.NAVIGATION_ISOCHRONE_URL, params=params)
        response.raise_for_status()
        return response.json()
