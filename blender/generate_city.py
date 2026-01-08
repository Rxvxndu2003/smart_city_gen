"""
Blender City Generator - Generate 3D city models from geographic data.

This script can be run in Blender headless mode:
blender -b -P generate_city.py -- --input city_data.json --output city_scene.glb
"""

import bpy
import bmesh
import json
import sys
import os
import math
import random
from pathlib import Path
from typing import List, Dict, Tuple
import mathutils


class BlenderCityGenerator:
    """Generate 3D city models in Blender from geographic data."""
    
    def __init__(self):
        """Initialize the generator."""
        self.materials = {}
        self.collection = None
        self.scale_factor = 1.0  # 1 Blender unit = 1 meter
        
        # Advanced detail feature flags (configurable from command line)
        self.enable_advanced_details = True  # Master toggle for all realistic details
        self.enable_windows = True  # Add windows to buildings
        self.enable_vehicles = True  # Add vehicles on roads
        self.enable_street_lights = True  # Add street lights
        self.enable_crosswalks = True  # Add crosswalk markings
        self.vehicle_spacing = 20  # Place vehicle every 20m along roads
        self.tree_spacing = 8  # Place trees every 8m in parks
        
    def generate_city(self, data: Dict, output_path: str):
        """
        Main generation function.
        
        Args:
            data: Processed geographic data dictionary
            output_path: Path to save the GLB/GLTF file
        """
        print("Starting city generation...")
        
        # Clear existing scene
        self._clear_scene()
        
        # Create main collection
        self.collection = bpy.data.collections.new("City")
        bpy.context.scene.collection.children.link(self.collection)
        
        # Setup materials
        self._setup_materials()
        
        # Generate city elements
        self._generate_roads(data.get('roads', []))
        self._generate_buildings(data.get('buildings', []))
        self._generate_parks(data.get('natural', []))
        self._generate_parking(data.get('amenities', []))
        
        # Add advanced details if enabled
        if self.enable_advanced_details:
            print("Adding advanced details...")
            if self.enable_vehicles:
                self._add_vehicles_to_roads(data.get('roads', []))
            if self.enable_street_lights:
                self._add_street_lights(data.get('roads', []))
            if self.enable_crosswalks:
                self._add_crosswalks(data.get('roads', []))
        
        # Add lighting
        self._setup_lighting()
        
        # Add camera
        self._setup_camera(data)
        
        # Export
        self._export_scene(output_path)
        
        print(f"City generated and exported to {output_path}")
    
    def _clear_scene(self):
        """Clear all objects from the scene."""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Clear collections
        for collection in bpy.data.collections:
            bpy.data.collections.remove(collection)
    
    def _setup_materials(self):
        """Create materials for different city elements."""
        
        # Road material
        mat_road = bpy.data.materials.new(name="Road")
        mat_road.use_nodes = True
        bsdf = mat_road.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.2, 0.2, 0.22, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.8
        self.materials['road'] = mat_road
        
        # Sidewalk material
        mat_sidewalk = bpy.data.materials.new(name="Sidewalk")
        mat_sidewalk.use_nodes = True
        bsdf = mat_sidewalk.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1.0)
        self.materials['sidewalk'] = mat_sidewalk
        
        # Building type materials (color-coded by function)
        building_type_colors = {
            'bank': (0.95, 0.85, 0.3, 1.0),          # Gold - Banks and financial
            'government': (0.4, 0.5, 0.7, 1.0),      # Blue-gray - Government buildings
            'healthcare': (0.9, 0.3, 0.3, 1.0),      # Red - Hospitals and clinics
            'education': (0.95, 0.75, 0.4, 1.0),     # Orange - Schools and universities
            'religious': (0.85, 0.85, 0.95, 1.0),    # Light purple - Religious buildings
            'commercial': (0.95, 0.5, 0.5, 1.0),     # Pink - Restaurants, markets
            'retail_large': (0.8, 0.4, 0.8, 1.0),    # Purple - Shopping malls
            'shop': (0.95, 0.7, 0.5, 1.0),           # Coral - Small shops
            'office': (0.5, 0.6, 0.7, 1.0),          # Steel blue - Office buildings
            'hotel': (0.4, 0.7, 0.8, 1.0),           # Cyan - Hotels
            'cultural': (0.7, 0.5, 0.8, 1.0),        # Lavender - Museums, galleries
            'industrial': (0.5, 0.5, 0.5, 1.0),      # Gray - Industrial buildings
            'residential': (0.9, 0.9, 0.85, 1.0),    # Cream - Residential
        }
        
        for building_type, color in building_type_colors.items():
            mat = bpy.data.materials.new(name=f"Building_{building_type}")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Roughness'].default_value = 0.4
            bsdf.inputs['Metallic'].default_value = 0.1 if building_type != 'bank' else 0.3
            self.materials[f'building_{building_type}'] = mat
        
        # Grass material
        mat_grass = bpy.data.materials.new(name="Grass")
        mat_grass.use_nodes = True
        bsdf = mat_grass.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.2, 0.6, 0.2, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.9
        self.materials['grass'] = mat_grass
        
        # Tree material
        mat_tree = bpy.data.materials.new(name="Tree")
        mat_tree.use_nodes = True
        bsdf = mat_tree.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.1, 0.4, 0.1, 1.0)
        self.materials['tree'] = mat_tree
        
        # Parking material
        mat_parking = bpy.data.materials.new(name="Parking")
        mat_parking.use_nodes = True
        bsdf = mat_parking.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1.0)
        self.materials['parking'] = mat_parking
        
        # Road marking material (white lines)
        mat_marking = bpy.data.materials.new(name="RoadMarking")
        mat_marking.use_nodes = True
        bsdf = mat_marking.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.6
        bsdf.inputs['Emission'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 0.2
        self.materials['road_marking'] = mat_marking
        
        # Glass material for windows
        mat_glass = bpy.data.materials.new(name="Glass")
        mat_glass.use_nodes = True
        bsdf = mat_glass.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.6, 0.7, 0.8, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 0.0
        bsdf.inputs['Transmission'].default_value = 0.95
        bsdf.inputs['IOR'].default_value = 1.45
        self.materials['glass'] = mat_glass
        
        # Vehicle materials (varied colors)
        vehicle_colors = [
            ('red', (0.8, 0.1, 0.1, 1.0)),
            ('blue', (0.1, 0.3, 0.7, 1.0)),
            ('white', (0.9, 0.9, 0.9, 1.0)),
            ('black', (0.1, 0.1, 0.1, 1.0)),
            ('yellow', (0.9, 0.8, 0.1, 1.0)),
            ('green', (0.2, 0.6, 0.2, 1.0)),
            ('gray', (0.5, 0.5, 0.5, 1.0)),
        ]
        
        for color_name, color_value in vehicle_colors:
            mat = bpy.data.materials.new(name=f"Vehicle_{color_name}")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            bsdf.inputs['Base Color'].default_value = color_value
            bsdf.inputs['Metallic'].default_value = 0.7
            bsdf.inputs['Roughness'].default_value = 0.2
            self.materials[f'vehicle_{color_name}'] = mat
        
        # Street light material (emissive)
        mat_light = bpy.data.materials.new(name="StreetLight")
        mat_light.use_nodes = True
        bsdf = mat_light.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1.0)
        bsdf.inputs['Emission'].default_value = (1.0, 0.9, 0.7, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 5.0
        self.materials['street_light'] = mat_light
    
    def _generate_roads(self, roads: List[Dict]):
        """Generate 3D road meshes."""
        print(f"Generating {len(roads)} roads...")
        
        for i, road_data in enumerate(roads):
            try:
                geom = road_data['geometry']
                if geom['type'] != 'LineString':
                    continue
                
                coords = geom['coordinates']
                if len(coords) < 2:
                    continue
                
                # Get road properties
                props = road_data.get('properties', {})
                lanes = props.get('lanes', 2)
                if isinstance(lanes, str):
                    try:
                        lanes = int(lanes)
                    except:
                        lanes = 2
                
                # Road width based on lanes
                road_width = max(3.0, lanes * 3.0)
                
                # Create road mesh using curve
                curve_data = bpy.data.curves.new(name=f"Road_{i}", type='CURVE')
                curve_data.dimensions = '3D'
                
                # Create spline
                spline = curve_data.splines.new('POLY')
                spline.points.add(len(coords) - 1)
                
                for j, coord in enumerate(coords):
                    x, y = coord[0] * self.scale_factor, coord[1] * self.scale_factor
                    spline.points[j].co = (x, y, 0, 1)
                
                # Set curve properties
                curve_data.bevel_depth = road_width / 2
                curve_data.bevel_resolution = 2
                
                # Create object
                road_obj = bpy.data.objects.new(f"Road_{i}", curve_data)
                self.collection.objects.link(road_obj)
                
                # Apply material
                road_obj.data.materials.append(self.materials['road'])
                
                # Create sidewalks
                self._create_sidewalks(coords, road_width, i)
                
            except Exception as e:
                print(f"Error generating road {i}: {e}")
    
    def _create_sidewalks(self, road_coords: List, road_width: float, road_index: int):
        """Create sidewalks alongside roads."""
        sidewalk_width = 1.5
        sidewalk_height = 0.15
        offset = (road_width / 2) + (sidewalk_width / 2)
        
        # Left sidewalk
        self._create_sidewalk_curve(road_coords, offset, sidewalk_width, 
                                   sidewalk_height, f"Sidewalk_L_{road_index}")
        
        # Right sidewalk
        self._create_sidewalk_curve(road_coords, -offset, sidewalk_width, 
                                   sidewalk_height, f"Sidewalk_R_{road_index}")
    
    def _create_sidewalk_curve(self, coords: List, offset: float, width: float, 
                               height: float, name: str):
        """Create a single sidewalk curve."""
        try:
            curve_data = bpy.data.curves.new(name=name, type='CURVE')
            curve_data.dimensions = '3D'
            
            spline = curve_data.splines.new('POLY')
            spline.points.add(len(coords) - 1)
            
            # Calculate offset perpendicular to road direction
            for j, coord in enumerate(coords):
                x_base = coord[0] * self.scale_factor
                y_base = coord[1] * self.scale_factor
                
                # Simple offset (perpendicular approximation)
                # In production, calculate proper perpendicular offset
                x = x_base
                y = y_base + offset
                z = height
                
                spline.points[j].co = (x, y, z, 1)
            
            curve_data.bevel_depth = width / 2
            curve_data.bevel_resolution = 1
            
            sidewalk_obj = bpy.data.objects.new(name, curve_data)
            self.collection.objects.link(sidewalk_obj)
            sidewalk_obj.data.materials.append(self.materials['sidewalk'])
            
        except Exception as e:
            print(f"Error creating sidewalk {name}: {e}")
    
    def _generate_buildings(self, buildings: List[Dict]):
        """Generate 3D buildings from footprints."""
        print(f"Generating {len(buildings)} buildings...")
        
        for i, building_data in enumerate(buildings):
            try:
                geom = building_data['geometry']
                if geom['type'] not in ['Polygon', 'MultiPolygon']:
                    continue
                
                # Get building properties
                props = building_data.get('properties', {})
                height = self._parse_building_height(props)
                building_type = props.get('building_type', 'residential')
                
                # Process polygon(s)
                polygons = []
                if geom['type'] == 'Polygon':
                    polygons = [geom['coordinates']]
                else:  # MultiPolygon
                    polygons = geom['coordinates']
                
                for poly_coords in polygons:
                    if not poly_coords or len(poly_coords) == 0:
                        continue
                    
                    # Use exterior ring
                    exterior = poly_coords[0]
                    if len(exterior) < 3:
                        continue
                    
                    # Create building mesh with type-specific material
                    self._create_building_mesh(exterior, height, building_type, i)
                    
            except Exception as e:
                print(f"Error generating building {i}: {e}")
    
    def _parse_building_height(self, props: Dict) -> float:
        """Parse building height from properties."""
        # Try explicit height
        if 'height' in props:
            try:
                return float(props['height'])
            except:
                pass
        
        # Try building:levels
        if 'building:levels' in props:
            try:
                levels = float(props['building:levels'])
                return levels * 3.5  # Assume 3.5m per floor
            except:
                pass
        
        # Random height for variation
        return random.uniform(8, 30)
    
    def _create_building_mesh(self, coords: List, height: float, building_type: str, index: int):
        """Create a 3D building mesh from footprint coordinates with type-specific material."""
        try:
            # Create mesh
            mesh = bpy.data.meshes.new(f"Building_{index}")
            obj = bpy.data.objects.new(f"Building_{index}", mesh)
            self.collection.objects.link(obj)
            
            # Create bmesh
            bm = bmesh.new()
            
            # Create vertices for base
            base_verts = []
            for coord in coords[:-1]:  # Skip last coord (same as first)
                x = coord[0] * self.scale_factor
                y = coord[1] * self.scale_factor
                v = bm.verts.new((x, y, 0))
                base_verts.append(v)
            
            # Create base face
            if len(base_verts) >= 3:
                bm.faces.new(base_verts)
            
            # Extrude upward
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            
            geom = bm.faces[:] + bm.edges[:] + bm.verts[:]
            result = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
            
            # Move extruded vertices up
            extruded_verts = [v for v in result['geom'] if isinstance(v, bmesh.types.BMVert)]
            for v in extruded_verts:
                v.co.z = height
            
            # Update mesh
            bm.to_mesh(mesh)
            bm.free()
            
            # Apply building type-specific material
            mat_key = f'building_{building_type}'
            if mat_key in self.materials:
                obj.data.materials.append(self.materials[mat_key])
            else:
                # Fallback to residential if type not found
                obj.data.materials.append(self.materials['building_residential'])
            
            # Add roof (optional - simple flat roof)
            self._add_roof_detail(obj, height)
            
            # Add windows if advanced details and windows both enabled
            if self.enable_advanced_details and self.enable_windows and height > 6:
                self._add_windows_to_building(obj, height, coords)
            
        except Exception as e:
            print(f"Error creating building mesh {index}: {e}")
    
    def _add_roof_detail(self, building_obj, height: float):
        """Add simple roof detail to building."""
        # Could add parapet, mechanical equipment, etc.
        # For now, just ensure top face exists
        pass
    
    def _generate_parks(self, natural_features: List[Dict]):
        """Generate parks and green spaces."""
        print(f"Generating {len(natural_features)} natural features...")
        
        for i, feature_data in enumerate(natural_features):
            try:
                geom = feature_data['geometry']
                props = feature_data.get('properties', {})
                
                # Check if it's a park or green space
                leisure = props.get('leisure', '')
                natural = props.get('natural', '')
                
                if leisure in ['park', 'garden', 'playground'] or natural in ['wood']:
                    if geom['type'] in ['Polygon', 'MultiPolygon']:
                        self._create_park(geom, i)
                        
            except Exception as e:
                print(f"Error generating park {i}: {e}")
    
    def _create_park(self, geom: Dict, index: int):
        """Create a park with grass and trees."""
        try:
            polygons = []
            if geom['type'] == 'Polygon':
                polygons = [geom['coordinates']]
            else:
                polygons = geom['coordinates']
            
            for poly_coords in polygons:
                if not poly_coords or len(poly_coords) == 0:
                    continue
                
                exterior = poly_coords[0]
                if len(exterior) < 3:
                    continue
                
                # Create grass plane
                self._create_grass_plane(exterior, index)
                
                # Add some trees
                self._add_trees_to_park(exterior, index)
                
        except Exception as e:
            print(f"Error creating park {index}: {e}")
    
    def _create_grass_plane(self, coords: List, index: int):
        """Create a grass plane from polygon coordinates."""
        try:
            mesh = bpy.data.meshes.new(f"Park_{index}")
            obj = bpy.data.objects.new(f"Park_{index}", mesh)
            self.collection.objects.link(obj)
            
            bm = bmesh.new()
            
            # Create vertices
            verts = []
            for coord in coords[:-1]:
                x = coord[0] * self.scale_factor
                y = coord[1] * self.scale_factor
                v = bm.verts.new((x, y, 0.05))  # Slightly above ground
                verts.append(v)
            
            # Create face
            if len(verts) >= 3:
                bm.faces.new(verts)
            
            bm.to_mesh(mesh)
            bm.free()
            
            obj.data.materials.append(self.materials['grass'])
            
        except Exception as e:
            print(f"Error creating grass plane {index}: {e}")
    
    def _add_trees_to_park(self, coords: List, park_index: int):
        """Add simple tree objects to park."""
        try:
            # Calculate park bounds
            xs = [c[0] * self.scale_factor for c in coords]
            ys = [c[1] * self.scale_factor for c in coords]
            
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            
            # Add random trees
            num_trees = random.randint(5, 15)
            
            for i in range(num_trees):
                x = random.uniform(minx, maxx)
                y = random.uniform(miny, maxy)
                
                self._create_simple_tree(x, y, f"Tree_{park_index}_{i}")
                
        except Exception as e:
            print(f"Error adding trees to park {park_index}: {e}")
    
    def _create_simple_tree(self, x: float, y: float, name: str):
        """Create a simple tree (cone on cylinder)."""
        try:
            # Trunk
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.3,
                depth=3,
                location=(x, y, 1.5)
            )
            trunk = bpy.context.active_object
            trunk.name = f"{name}_trunk"
            self.collection.objects.link(trunk)
            bpy.context.scene.collection.objects.unlink(trunk)
            
            # Foliage
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=2.5,
                location=(x, y, 4)
            )
            foliage = bpy.context.active_object
            foliage.name = f"{name}_foliage"
            foliage.data.materials.append(self.materials['tree'])
            self.collection.objects.link(foliage)
            bpy.context.scene.collection.objects.unlink(foliage)
            
        except Exception as e:
            print(f"Error creating tree {name}: {e}")
    
    def _generate_parking(self, amenities: List[Dict]):
        """Generate parking lots."""
        print(f"Generating parking from {len(amenities)} amenities...")
        
        for i, amenity_data in enumerate(amenities):
            try:
                props = amenity_data.get('properties', {})
                if props.get('amenity') in ['parking', 'parking_space']:
                    geom = amenity_data['geometry']
                    
                    if geom['type'] in ['Polygon', 'MultiPolygon']:
                        self._create_parking_lot(geom, i)
                        
            except Exception as e:
                print(f"Error generating parking {i}: {e}")
    
    def _create_parking_lot(self, geom: Dict, index: int):
        """Create a parking lot mesh."""
        try:
            polygons = []
            if geom['type'] == 'Polygon':
                polygons = [geom['coordinates']]
            else:
                polygons = geom['coordinates']
            
            for poly_coords in polygons:
                if not poly_coords or len(poly_coords) == 0:
                    continue
                
                exterior = poly_coords[0]
                if len(exterior) < 3:
                    continue
                
                # Create parking surface
                mesh = bpy.data.meshes.new(f"Parking_{index}")
                obj = bpy.data.objects.new(f"Parking_{index}", mesh)
                self.collection.objects.link(obj)
                
                bm = bmesh.new()
                
                verts = []
                for coord in exterior[:-1]:
                    x = coord[0] * self.scale_factor
                    y = coord[1] * self.scale_factor
                    v = bm.verts.new((x, y, 0.02))
                    verts.append(v)
                
                if len(verts) >= 3:
                    bm.faces.new(verts)
                
                bm.to_mesh(mesh)
                bm.free()
                
                obj.data.materials.append(self.materials['parking'])
                
        except Exception as e:
            print(f"Error creating parking lot {index}: {e}")
    
    def _setup_lighting(self):
        """Add lighting to the scene."""
        # Sun light
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
        sun = bpy.context.active_object
        sun.name = "Sun"
        sun.data.energy = 2.0
        sun.rotation_euler = (math.radians(60), 0, math.radians(45))
        
        # Ambient light
        bpy.context.scene.world.use_nodes = True
        world_nodes = bpy.context.scene.world.node_tree.nodes
        world_nodes["Background"].inputs['Color'].default_value = (0.5, 0.7, 1.0, 1.0)
        world_nodes["Background"].inputs['Strength'].default_value = 0.3
    
    def _setup_camera(self, data: Dict):
        """Add camera to the scene."""
        # Calculate scene bounds
        # For now, use a default aerial view
        bpy.ops.object.camera_add(location=(0, -100, 80))
        camera = bpy.context.active_object
        camera.name = "Camera"
        camera.rotation_euler = (math.radians(60), 0, 0)
        
        bpy.context.scene.camera = camera
    
    def _add_windows_to_building(self, building_obj, height: float, coords: List):
        """Add windows to building facades."""
        try:
            # Calculate number of floors (3.5m per floor)
            num_floors = max(1, int(height / 3.5))
            window_height = 2.0
            window_width = 1.5
            floor_height = height / num_floors
            
            # Get building edges to place windows
            for i in range(len(coords) - 1):
                x1, y1 = coords[i][0] * self.scale_factor, coords[i][1] * self.scale_factor
                x2, y2 = coords[i+1][0] * self.scale_factor, coords[i+1][1] * self.scale_factor
                
                edge_length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                num_windows = max(1, int(edge_length / 3.0))  # Window every 3m
                
                # Place windows along this edge
                for floor in range(1, num_floors + 1):
                    z = (floor - 0.5) * floor_height
                    
                    for win in range(num_windows):
                        t = (win + 0.5) / num_windows
                        x = x1 + t * (x2 - x1)
                        y = y1 + t * (y2 - y1)
                        
                        # Create window (simple cube)
                        bpy.ops.mesh.primitive_cube_add(
                            size=1,
                            location=(x, y, z)
                        )
                        window = bpy.context.active_object
                        window.scale = (window_width/2, 0.2, window_height/2)
                        window.data.materials.append(self.materials['glass'])
                        self.collection.objects.link(window)
                        bpy.context.scene.collection.objects.unlink(window)
                        
        except Exception as e:
            print(f"Error adding windows: {e}")
    
    def _add_vehicles_to_roads(self, roads: List[Dict]):
        """Add vehicles along roads for realism."""
        print("Adding vehicles to roads...")
        vehicle_count = 0
        
        for road_data in roads:
            try:
                geom = road_data['geometry']
                if geom['type'] != 'LineString':
                    continue
                
                coords = geom['coordinates']
                if len(coords) < 2:
                    continue
                
                # Calculate road length
                total_length = 0
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i][0], coords[i][1]
                    x2, y2 = coords[i+1][0], coords[i+1][1]
                    segment_length = math.sqrt((x2-x1)**2 + (y2-y1)**2) * self.scale_factor
                    total_length += segment_length
                
                # Place vehicles along road
                num_vehicles = max(1, int(total_length / self.vehicle_spacing))
                
                for v in range(num_vehicles):
                    # Find position along road
                    target_dist = (v / num_vehicles) * total_length
                    current_dist = 0
                    
                    for i in range(len(coords) - 1):
                        x1, y1 = coords[i][0] * self.scale_factor, coords[i][1] * self.scale_factor
                        x2, y2 = coords[i+1][0] * self.scale_factor, coords[i+1][1] * self.scale_factor
                        segment_length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                        
                        if current_dist + segment_length >= target_dist:
                            # Place vehicle here
                            t = (target_dist - current_dist) / segment_length
                            x = x1 + t * (x2 - x1)
                            y = y1 + t * (y2 - y1)
                            
                            # Calculate rotation from road direction
                            angle = math.atan2(y2 - y1, x2 - x1)
                            
                            self._create_vehicle(x, y, 0.5, angle)
                            vehicle_count += 1
                            break
                        
                        current_dist += segment_length
                
            except Exception as e:
                print(f"Error adding vehicles to road: {e}")
        
        print(f"Added {vehicle_count} vehicles")
    
    def _create_vehicle(self, x: float, y: float, z: float, rotation: float):
        """Create a simple vehicle model."""
        try:
            # Random vehicle color
            color_names = ['red', 'blue', 'white', 'black', 'yellow', 'green', 'gray']
            color = random.choice(color_names)
            
            # Create vehicle body (box)
            bpy.ops.mesh.primitive_cube_add(location=(x, y, z + 0.8))
            body = bpy.context.active_object
            body.scale = (2.0, 1.0, 0.6)  # Car-like proportions
            body.rotation_euler = (0, 0, rotation)
            body.data.materials.append(self.materials[f'vehicle_{color}'])
            self.collection.objects.link(body)
            bpy.context.scene.collection.objects.unlink(body)
            
            # Create cabin (smaller box on top)
            bpy.ops.mesh.primitive_cube_add(location=(x, y, z + 1.5))
            cabin = bpy.context.active_object
            cabin.scale = (1.2, 0.9, 0.4)
            cabin.rotation_euler = (0, 0, rotation)
            cabin.data.materials.append(self.materials['glass'])
            self.collection.objects.link(cabin)
            bpy.context.scene.collection.objects.unlink(cabin)
            
            # Add wheels (simple cylinders)
            wheel_positions = [
                (math.cos(rotation) * 1.2 + math.cos(rotation + math.pi/2) * 0.8,
                 math.sin(rotation) * 1.2 + math.sin(rotation + math.pi/2) * 0.8),
                (math.cos(rotation) * 1.2 - math.cos(rotation + math.pi/2) * 0.8,
                 math.sin(rotation) * 1.2 - math.sin(rotation + math.pi/2) * 0.8),
                (-math.cos(rotation) * 1.2 + math.cos(rotation + math.pi/2) * 0.8,
                 -math.sin(rotation) * 1.2 + math.sin(rotation + math.pi/2) * 0.8),
                (-math.cos(rotation) * 1.2 - math.cos(rotation + math.pi/2) * 0.8,
                 -math.sin(rotation) * 1.2 - math.sin(rotation + math.pi/2) * 0.8),
            ]
            
            for wx, wy in wheel_positions:
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=0.3,
                    depth=0.2,
                    location=(x + wx, y + wy, z + 0.3)
                )
                wheel = bpy.context.active_object
                wheel.rotation_euler = (0, math.pi/2, rotation)
                wheel.data.materials.append(self.materials['vehicle_black'])
                self.collection.objects.link(wheel)
                bpy.context.scene.collection.objects.unlink(wheel)
                
        except Exception as e:
            print(f"Error creating vehicle: {e}")
    
    def _add_street_lights(self, roads: List[Dict]):
        """Add street lights along roads."""
        print("Adding street lights...")
        light_count = 0
        
        for road_data in roads:
            try:
                geom = road_data['geometry']
                if geom['type'] != 'LineString':
                    continue
                
                coords = geom['coordinates']
                props = road_data.get('properties', {})
                
                # Only add lights to main roads
                road_type = props.get('highway', 'residential')
                if road_type not in ['primary', 'secondary', 'tertiary']:
                    continue
                
                # Place lights every 25m
                for i in range(0, len(coords) - 1):
                    if i % 3 == 0:  # Every 3rd point
                        x = coords[i][0] * self.scale_factor
                        y = coords[i][1] * self.scale_factor
                        
                        # Offset to side of road
                        if i < len(coords) - 1:
                            dx = coords[i+1][0] - coords[i][0]
                            dy = coords[i+1][1] - coords[i][1]
                            length = math.sqrt(dx**2 + dy**2)
                            if length > 0:
                                # Perpendicular offset
                                offset_x = -dy / length * 4
                                offset_y = dx / length * 4
                                
                                self._create_street_light(
                                    x + offset_x * self.scale_factor,
                                    y + offset_y * self.scale_factor
                                )
                                light_count += 1
                
            except Exception as e:
                print(f"Error adding street lights: {e}")
        
        print(f"Added {light_count} street lights")
    
    def _create_street_light(self, x: float, y: float):
        """Create a street light pole."""
        try:
            # Pole
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.15,
                depth=6,
                location=(x, y, 3)
            )
            pole = bpy.context.active_object
            pole.data.materials.append(self.materials['vehicle_gray'])
            self.collection.objects.link(pole)
            bpy.context.scene.collection.objects.unlink(pole)
            
            # Light fixture
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=0.4,
                location=(x, y, 6)
            )
            light_obj = bpy.context.active_object
            light_obj.data.materials.append(self.materials['street_light'])
            self.collection.objects.link(light_obj)
            bpy.context.scene.collection.objects.unlink(light_obj)
            
            # Add point light
            bpy.ops.object.light_add(type='POINT', location=(x, y, 5.5))
            light = bpy.context.active_object
            light.data.energy = 50
            light.data.color = (1.0, 0.9, 0.7)
            self.collection.objects.link(light)
            bpy.context.scene.collection.objects.unlink(light)
            
        except Exception as e:
            print(f"Error creating street light: {e}")
    
    def _add_crosswalks(self, roads: List[Dict]):
        """Add crosswalk markings at intersections."""
        print("Adding crosswalk markings...")
        
        # Find road intersections (simplified - use road endpoints)
        intersections = []
        for road_data in roads:
            try:
                geom = road_data['geometry']
                if geom['type'] != 'LineString':
                    continue
                
                coords = geom['coordinates']
                if len(coords) >= 2:
                    # Start and end points
                    start = (coords[0][0] * self.scale_factor, coords[0][1] * self.scale_factor)
                    end = (coords[-1][0] * self.scale_factor, coords[-1][1] * self.scale_factor)
                    intersections.append(start)
                    intersections.append(end)
            except:
                pass
        
        # Create crosswalks at intersections
        added = 0
        for x, y in intersections[:50]:  # Limit to 50 crosswalks
            try:
                # Create crosswalk stripes (white rectangles)
                for i in range(5):
                    offset = (i - 2) * 0.8
                    bpy.ops.mesh.primitive_plane_add(
                        size=1,
                        location=(x + offset, y, 0.02)
                    )
                    stripe = bpy.context.active_object
                    stripe.scale = (0.3, 2.0, 1.0)
                    stripe.data.materials.append(self.materials['road_marking'])
                    self.collection.objects.link(stripe)
                    bpy.context.scene.collection.objects.unlink(stripe)
                
                added += 1
            except Exception as e:
                print(f"Error creating crosswalk: {e}")
        
        print(f"Added {added} crosswalks")
    
    def _export_scene(self, output_path: str):
        """Export scene to GLB/GLTF."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine format
        if output_path.suffix.lower() == '.glb':
            export_format = 'GLB'
        else:
            export_format = 'GLTF_SEPARATE'
        
        # Export
        bpy.ops.export_scene.gltf(
            filepath=str(output_path),
            export_format=export_format,
            export_apply=True,
            export_materials='EXPORT',
            export_colors=True,
            export_cameras=True,
            export_lights=True
        )


def main():
    """Main function for command-line usage."""
    # Parse command line arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        print("Usage: blender -b -P generate_city.py -- --input <input.json> --output <output.glb>")
        return
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input JSON file with city data')
    parser.add_argument('--output', required=True, help='Output GLB/GLTF file path')
    parser.add_argument('--format', default='glb', help='Export format (glb or gltf)')
    
    # Advanced detail options
    parser.add_argument('--enable-advanced-details', action='store_true', help='Enable advanced realistic details')
    parser.add_argument('--enable-windows', action='store_true', help='Add windows to buildings')
    parser.add_argument('--enable-vehicles', action='store_true', help='Add vehicles on roads')
    parser.add_argument('--enable-street-lights', action='store_true', help='Add street lights')
    parser.add_argument('--enable-crosswalks', action='store_true', help='Add crosswalk markings')
    parser.add_argument('--vehicle-spacing', type=float, default=20.0, help='Distance between vehicles (meters)')
    parser.add_argument('--tree-spacing', type=float, default=8.0, help='Distance between trees (meters)')
    
    args = parser.parse_args(argv)
    
    # Load input data
    print(f"Loading data from {args.input}")
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    # Generate city with advanced detail options
    generator = BlenderCityGenerator()
    generator.enable_advanced_details = args.enable_advanced_details
    generator.enable_windows = args.enable_windows
    generator.enable_vehicles = args.enable_vehicles
    generator.enable_street_lights = args.enable_street_lights
    generator.enable_crosswalks = args.enable_crosswalks
    generator.vehicle_spacing = args.vehicle_spacing
    generator.tree_spacing = args.tree_spacing
    generator.generate_city(data, args.output)
    
    print("Done!")


if __name__ == "__main__":
    main()
