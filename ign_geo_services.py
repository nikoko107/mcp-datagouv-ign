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
