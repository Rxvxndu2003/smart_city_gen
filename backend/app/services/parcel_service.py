"""
Parcel Subdivision Service - Divide city blocks into lots/parcels.
"""
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import split, unary_union
import shapely.affinity
from typing import List, Dict, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ParcelSubdivisionService:
    """Service for subdividing city blocks into parcels."""
    
    def __init__(self):
        """Initialize subdivision service."""
        self.min_parcel_area = 50  # square meters
        self.min_parcel_width = 5  # meters
        self.building_setback = 2  # meters from parcel edge
    
    def subdivide_block(
        self,
        block: Polygon,
        target_parcel_width: float = 15,
        street_frontage: LineString = None
    ) -> List[Dict]:
        """
        Subdivide a city block into parcels.
        
        Args:
            block: The block polygon to subdivide
            target_parcel_width: Target width for strip parcels (meters)
            street_frontage: Main street line for orientation (optional)
        
        Returns:
            List of parcel dictionaries with geometry and intended use
        """
        try:
            # Simple approach: create strip lots perpendicular to longest edge
            parcels = []
            
            # Get the longest edge as street frontage
            if street_frontage is None:
                street_frontage = self._get_longest_edge(block)
            
            # Create perpendicular division lines
            division_lines = self._create_division_lines(
                block,
                street_frontage,
                target_parcel_width
            )
            
            # Split block by division lines
            if division_lines:
                result = block
                for line in division_lines:
                    # Extend line to ensure it crosses the polygon
                    extended_line = self._extend_line(line, block.bounds)
                    parts = split(result, extended_line)
                    
                    if len(parts.geoms) > 0:
                        result = parts
                
                # Extract individual parcels
                if hasattr(result, 'geoms'):
                    parcel_polygons = list(result.geoms)
                else:
                    parcel_polygons = [result]
            else:
                # If division failed, use whole block
                parcel_polygons = [block]
            
            # Assign uses to parcels
            parcels = self._assign_parcel_uses(parcel_polygons, block)
            
            return parcels
            
        except Exception as e:
            logger.error(f"Error subdividing block: {e}")
            # Return whole block as single parcel
            return [{
                'geometry': block,
                'type': 'building',
                'area': block.area
            }]
    
    def _get_longest_edge(self, polygon: Polygon) -> LineString:
        """Get the longest edge of a polygon."""
        coords = list(polygon.exterior.coords)
        max_length = 0
        longest_edge = None
        
        for i in range(len(coords) - 1):
            edge = LineString([coords[i], coords[i + 1]])
            if edge.length > max_length:
                max_length = edge.length
                longest_edge = edge
        
        return longest_edge
    
    def _create_division_lines(
        self,
        block: Polygon,
        street_frontage: LineString,
        target_width: float
    ) -> List[LineString]:
        """Create perpendicular division lines along street frontage."""
        lines = []
        
        # Get frontage direction
        start, end = street_frontage.coords[0], street_frontage.coords[-1]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return lines
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Perpendicular direction
        perp_dx = -dy
        perp_dy = dx
        
        # Create division points along frontage
        num_divisions = int(length / target_width)
        
        for i in range(1, num_divisions):
            # Point on frontage
            t = i / num_divisions
            px = start[0] + t * dx * length
            py = start[1] + t * dy * length
            
            # Create perpendicular line
            line_length = max(block.bounds[2] - block.bounds[0],
                            block.bounds[3] - block.bounds[1]) * 2
            
            p1 = (px - perp_dx * line_length, py - perp_dy * line_length)
            p2 = (px + perp_dx * line_length, py + perp_dy * line_length)
            
            lines.append(LineString([p1, p2]))
        
        return lines
    
    def _extend_line(self, line: LineString, bounds: Tuple) -> LineString:
        """Extend a line to ensure it crosses bounding box."""
        minx, miny, maxx, maxy = bounds
        bbox_size = max(maxx - minx, maxy - miny) * 3
        
        start, end = line.coords[0], line.coords[-1]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return line
        
        dx /= length
        dy /= length
        
        p1 = (start[0] - dx * bbox_size, start[1] - dy * bbox_size)
        p2 = (end[0] + dx * bbox_size, end[1] + dy * bbox_size)
        
        return LineString([p1, p2])
    
    def _assign_parcel_uses(
        self,
        parcel_polygons: List[Polygon],
        original_block: Polygon
    ) -> List[Dict]:
        """Assign intended uses to parcels."""
        parcels = []
        
        # Filter out very small parcels
        valid_parcels = [p for p in parcel_polygons if p.area > self.min_parcel_area]
        
        if not valid_parcels:
            valid_parcels = parcel_polygons
        
        total_area = sum(p.area for p in valid_parcels)
        
        # Target ratios
        building_ratio = 0.7
        green_ratio = 0.2
        parking_ratio = 0.1
        
        # Sort by area (largest first)
        sorted_parcels = sorted(valid_parcels, key=lambda p: p.area, reverse=True)
        
        building_area = 0
        green_area = 0
        parking_area = 0
        
        for parcel in sorted_parcels:
            area = parcel.area
            
            # Decide use based on current ratios
            if building_area < total_area * building_ratio:
                use_type = 'building'
                building_area += area
            elif green_area < total_area * green_ratio:
                use_type = 'green'
                green_area += area
            elif parking_area < total_area * parking_ratio:
                use_type = 'parking'
                parking_area += area
            else:
                use_type = 'building'
            
            parcels.append({
                'geometry': parcel,
                'type': use_type,
                'area': area,
                'building_footprint': parcel.buffer(-self.building_setback) if use_type == 'building' else None
            })
        
        return parcels
    
    def create_building_footprint(self, parcel: Polygon, coverage_ratio: float = 0.6) -> Polygon:
        """Create a building footprint within a parcel."""
        # Apply setback
        footprint = parcel.buffer(-self.building_setback)
        
        # If coverage ratio < 1, further reduce
        if coverage_ratio < 1.0:
            # Scale from centroid
            centroid = footprint.centroid
            footprint = shapely.affinity.scale(
                footprint,
                xfact=coverage_ratio,
                yfact=coverage_ratio,
                origin=centroid
            )
        
        return footprint if footprint.is_valid and not footprint.is_empty else parcel


# Global service instance
parcel_service = ParcelSubdivisionService()
