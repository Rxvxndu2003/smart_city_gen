"""
Geo Data Service - Fetch and process real-world geographic data from OSM.
"""
import osmnx as ox
import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import Polygon, MultiPolygon, Point, LineString
from shapely.ops import unary_union, transform
import pyproj
from typing import Dict, List, Tuple, Optional
import json
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Configure osmnx
ox.settings.use_cache = True
ox.settings.log_console = False


class GeoDataService:
    """Service for fetching and processing geographic data."""
    
    def __init__(self):
        """Initialize the geo data service."""
        self.data_dir = Path("storage/geo_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_city_data(
        self,
        bbox: Dict[str, float] = None,
        polygon: List[List[float]] = None,
        place_name: str = None
    ) -> Dict:
        """
        Fetch real-world city data from OpenStreetMap.
        
        Args:
            bbox: Bounding box dict with keys: north, south, east, west (lat/lon)
            polygon: List of [lat, lon] coordinates defining a polygon
            place_name: Name of place to geocode (e.g., "Colombo, Sri Lanka")
        
        Returns:
            Dictionary containing processed geographic data
        """
        try:
            # Determine query area
            if polygon:
                # Convert to shapely polygon (lon, lat order for shapely)
                coords = [(point[1], point[0]) for point in polygon]
                query_polygon = Polygon(coords)
            elif bbox:
                query_polygon = shapely.geometry.box(
                    bbox['west'], bbox['south'],
                    bbox['east'], bbox['north']
                )
            elif place_name:
                # Geocode the place name
                gdf = ox.geocode_to_gdf(place_name)
                query_polygon = gdf.geometry.iloc[0]
            else:
                raise ValueError("Must provide bbox, polygon, or place_name")
            
            logger.info(f"Fetching data for area: {query_polygon.bounds}")
            
            # Get center point for coordinate transformation
            centroid = query_polygon.centroid
            center_lat, center_lon = centroid.y, centroid.x
            
            # Fetch different data layers
            data = {
                'roads': self._fetch_roads(query_polygon),
                'buildings': self._fetch_buildings(query_polygon),
                'landuse': self._fetch_landuse(query_polygon),
                'natural': self._fetch_natural_features(query_polygon),
                'amenities': self._fetch_amenities(query_polygon),
                'center': {'lat': center_lat, 'lon': center_lon},
                'bounds': query_polygon.bounds
            }
            
            # Process and normalize coordinates
            processed_data = self._process_and_normalize(data, center_lat, center_lon)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching city data: {e}")
            raise
    
    def _fetch_roads(self, polygon: Polygon) -> gpd.GeoDataFrame:
        """Fetch road network from OSM."""
        try:
            # Get street network
            G = ox.graph_from_polygon(
                polygon,
                network_type='drive',
                simplify=True,
                retain_all=False
            )
            
            # Convert to GeoDataFrame of edges
            gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
            
            # Keep important columns
            columns_to_keep = ['geometry', 'highway', 'name', 'lanes', 'width', 'maxspeed']
            available_cols = [col for col in columns_to_keep if col in gdf_edges.columns]
            gdf_edges = gdf_edges[available_cols]
            
            return gdf_edges
            
        except Exception as e:
            logger.warning(f"Error fetching roads: {e}")
            return gpd.GeoDataFrame()
    
    def _fetch_buildings(self, polygon: Polygon) -> gpd.GeoDataFrame:
        """Fetch building footprints from OSM."""
        try:
            tags = {'building': True}
            gdf = ox.features_from_polygon(polygon, tags=tags)
            
            # Filter to only polygons
            gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            
            # Keep relevant columns including building type identifiers
            columns_to_keep = [
                'geometry', 'building', 'height', 'building:levels', 'name', 
                'amenity', 'shop', 'office', 'tourism', 'government', 'building:use'
            ]
            available_cols = [col for col in columns_to_keep if col in gdf.columns]
            gdf = gdf[available_cols]
            
            # Classify building types for visualization
            gdf['building_type'] = gdf.apply(self._classify_building_type, axis=1)
            
            return gdf
            
        except Exception as e:
            logger.warning(f"Error fetching buildings: {e}")
            return gpd.GeoDataFrame()
    
    def _classify_building_type(self, row) -> str:
        """Classify building type based on OSM tags for color-coding."""
        # Priority order: specific use -> amenity -> shop -> office -> building type
        
        # Check amenity tags
        amenity = row.get('amenity', None)
        if pd.notna(amenity):
            # Financial institutions
            if amenity in ['bank', 'atm', 'bureau_de_change']:
                return 'bank'
            # Government/public services
            elif amenity in ['police', 'fire_station', 'post_office', 'townhall', 'courthouse', 'embassy']:
                return 'government'
            # Healthcare
            elif amenity in ['hospital', 'clinic', 'doctors', 'pharmacy']:
                return 'healthcare'
            # Education
            elif amenity in ['school', 'university', 'college', 'library']:
                return 'education'
            # Religious
            elif amenity in ['place_of_worship', 'monastery', 'temple']:
                return 'religious'
            # Commercial/retail
            elif amenity in ['marketplace', 'restaurant', 'cafe', 'fast_food', 'pub', 'bar']:
                return 'commercial'
        
        # Check shop tags
        shop = row.get('shop', None)
        if pd.notna(shop):
            if shop in ['supermarket', 'mall', 'department_store']:
                return 'retail_large'
            else:
                return 'shop'
        
        # Check office tags
        office = row.get('office', None)
        if pd.notna(office):
            if office in ['government', 'administrative']:
                return 'government'
            else:
                return 'office'
        
        # Check government tag
        government = row.get('government', None)
        if pd.notna(government):
            return 'government'
        
        # Check tourism tags
        tourism = row.get('tourism', None)
        if pd.notna(tourism):
            if tourism in ['hotel', 'motel', 'guest_house']:
                return 'hotel'
            elif tourism in ['museum', 'gallery', 'attraction']:
                return 'cultural'
        
        # Check building type
        building = row.get('building', None)
        if pd.notna(building) and building != 'yes':
            if building in ['commercial', 'retail', 'shop']:
                return 'commercial'
            elif building in ['office']:
                return 'office'
            elif building in ['industrial', 'warehouse']:
                return 'industrial'
            elif building in ['hotel']:
                return 'hotel'
            elif building in ['hospital']:
                return 'healthcare'
            elif building in ['school', 'university']:
                return 'education'
            elif building in ['church', 'cathedral', 'mosque', 'temple', 'synagogue']:
                return 'religious'
            elif building in ['government', 'public']:
                return 'government'
            elif building in ['residential', 'apartments', 'house', 'detached']:
                return 'residential'
        
        # Default to residential
        return 'residential'
    
    def _fetch_landuse(self, polygon: Polygon) -> gpd.GeoDataFrame:
        """Fetch land use areas (parks, residential, commercial, etc.)."""
        try:
            tags = {'landuse': True}
            gdf = ox.features_from_polygon(polygon, tags=tags)
            
            # Filter to polygons
            gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            
            columns_to_keep = ['geometry', 'landuse', 'name']
            available_cols = [col for col in columns_to_keep if col in gdf.columns]
            gdf = gdf[available_cols]
            
            return gdf
            
        except Exception as e:
            logger.warning(f"Error fetching landuse: {e}")
            return gpd.GeoDataFrame()
    
    def _fetch_natural_features(self, polygon: Polygon) -> gpd.GeoDataFrame:
        """Fetch natural features (parks, water, trees, etc.)."""
        try:
            tags = {
                'leisure': ['park', 'garden', 'playground', 'pitch'],
                'natural': ['water', 'wood', 'tree_row'],
                'waterway': True
            }
            gdf = ox.features_from_polygon(polygon, tags=tags)
            
            # Filter to polygons
            gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon', 'LineString'])]
            
            columns_to_keep = ['geometry', 'leisure', 'natural', 'waterway', 'name']
            available_cols = [col for col in columns_to_keep if col in gdf.columns]
            gdf = gdf[available_cols]
            
            return gdf
            
        except Exception as e:
            logger.warning(f"Error fetching natural features: {e}")
            return gpd.GeoDataFrame()
    
    def _fetch_amenities(self, polygon: Polygon) -> gpd.GeoDataFrame:
        """Fetch amenities (parking, etc.)."""
        try:
            tags = {'amenity': ['parking', 'parking_space']}
            gdf = ox.features_from_polygon(polygon, tags=tags)
            
            columns_to_keep = ['geometry', 'amenity', 'name', 'capacity']
            available_cols = [col for col in columns_to_keep if col in gdf.columns]
            gdf = gdf[available_cols]
            
            return gdf
            
        except Exception as e:
            logger.warning(f"Error fetching amenities: {e}")
            return gpd.GeoDataFrame()
    
    def _process_and_normalize(
        self,
        data: Dict,
        center_lat: float,
        center_lon: float
    ) -> Dict:
        """
        Process and normalize geographic data to local coordinate system.
        Converts lat/lon to meters with origin at (0, 0).
        """
        # Create projection transformer
        # From WGS84 (lat/lon) to local UTM
        proj_wgs84 = pyproj.CRS('EPSG:4326')
        
        # Calculate UTM zone for Sri Lanka (typically zone 44N)
        utm_zone = int((center_lon + 180) / 6) + 1
        proj_utm = pyproj.CRS(f'EPSG:326{utm_zone}')  # Northern hemisphere
        
        transformer = pyproj.Transformer.from_crs(proj_wgs84, proj_utm, always_xy=True)
        
        # Transform center point to get local origin
        center_x, center_y = transformer.transform(center_lon, center_lat)
        
        def transform_geometry(geom):
            """Transform a geometry to local coordinates."""
            if geom is None or geom.is_empty:
                return geom
            
            # Transform to UTM
            geom_utm = transform(transformer.transform, geom)
            
            # Translate to local origin (0, 0)
            return shapely.affinity.translate(geom_utm, -center_x, -center_y)
        
        # Process each data layer
        processed = {
            'center': data['center'],
            'bounds': data['bounds'],
            'projection': {
                'utm_zone': utm_zone,
                'center_utm': {'x': center_x, 'y': center_y}
            }
        }
        
        for layer_name in ['roads', 'buildings', 'landuse', 'natural', 'amenities']:
            gdf = data[layer_name]
            
            if not gdf.empty:
                # Transform geometries
                gdf['geometry'] = gdf['geometry'].apply(transform_geometry)
                
                # Convert to GeoJSON-like structure
                features = []
                for idx, row in gdf.iterrows():
                    feature = {
                        'geometry': shapely.geometry.mapping(row['geometry']),
                        'properties': {}
                    }
                    
                    # Add properties
                    for col in gdf.columns:
                        if col != 'geometry':
                            val = row[col]
                            if pd.notna(val):
                                feature['properties'][col] = val
                    
                    features.append(feature)
                
                processed[layer_name] = features
            else:
                processed[layer_name] = []
        
        return processed
    
    def infer_city_blocks(self, roads_gdf: gpd.GeoDataFrame) -> List[Polygon]:
        """
        Infer city blocks from road network.
        Blocks are areas enclosed by roads.
        """
        try:
            # Union all road geometries
            roads_union = unary_union(roads_gdf.geometry.buffer(2))  # Small buffer for roads
            
            # Get the bounding box
            minx, miny, maxx, maxy = roads_union.bounds
            bbox = shapely.geometry.box(minx - 10, miny - 10, maxx + 10, maxy + 10)
            
            # Subtract roads from bbox to get blocks
            blocks = bbox.difference(roads_union)
            
            # Split into individual polygons
            if isinstance(blocks, MultiPolygon):
                block_list = list(blocks.geoms)
            elif isinstance(blocks, Polygon):
                block_list = [blocks]
            else:
                block_list = []
            
            # Filter out very small blocks
            min_area = 100  # square meters
            block_list = [b for b in block_list if b.area > min_area]
            
            return block_list
            
        except Exception as e:
            logger.error(f"Error inferring city blocks: {e}")
            return []
    
    def save_processed_data(self, data: Dict, filename: str) -> Path:
        """Save processed data to JSON file."""
        output_path = self.data_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved processed data to {output_path}")
        return output_path


# Global service instance
geo_data_service = GeoDataService()
