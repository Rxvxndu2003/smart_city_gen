#!/usr/bin/env python3
"""
Blender script for procedural building generation.
Run headlessly: blender --background --python generate_building.py -- <params_json>
"""
import bpy
import json
import sys
import math
from pathlib import Path

def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_building(params: dict):
    """Generate building based on parameters."""
    # Extract parameters
    width = params.get('width', 20)
    depth = params.get('depth', 15)
    height = params.get('height', 30)
    num_floors = params.get('num_floors', 10)
    floor_height = height / num_floors
    
    # ML-enhanced parameters
    window_size = params.get('window_size', 1.5)
    window_spacing = params.get('window_spacing', 3.0)
    facade_detail = params.get('facade_detail_level', 3)
    roof_type = params.get('roof_type', 'flat')
    balcony_enabled = params.get('balcony_enabled', True)
    entrance_width = params.get('entrance_width', 2.5)
    material_quality = params.get('material_quality', 0.8)
    architectural_style = params.get('architectural_style', 'contemporary')
    
    print(f"Creating {architectural_style} building: {width}x{depth}x{height}m with {num_floors} floors")
    print(f"ML Parameters: window_size={window_size}m, facade_detail={facade_detail}, balconies={balcony_enabled}")
    
    # Create base foundation
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    foundation = bpy.context.active_object
    foundation.scale = (width/2, depth/2, 0.5)
    foundation.name = "Foundation"
    
    # Foundation material (enhanced with material_quality)
    foundation_mat = bpy.data.materials.new(name="Foundation_Material")
    foundation_mat.use_nodes = True
    foundation_bsdf = foundation_mat.node_tree.nodes["Principled BSDF"]
    base_color = 0.3 * material_quality
    foundation_bsdf.inputs['Base Color'].default_value = (base_color, base_color, base_color, 1.0)
    foundation_bsdf.inputs['Roughness'].default_value = 0.8
    foundation.data.materials.append(foundation_mat)
    
    # Create main building
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height/2 + 0.5))
    building = bpy.context.active_object
    building.scale = (width/2 - 0.5, depth/2 - 0.5, height/2)
    building.name = "MainBuilding"
    
    # Building material (style-dependent)
    building_mat = bpy.data.materials.new(name="Building_Material")
    building_mat.use_nodes = True
    building_bsdf = building_mat.node_tree.nodes["Principled BSDF"]
    
    if architectural_style == 'modern':
        building_bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        building_bsdf.inputs['Roughness'].default_value = 0.2 * (1 - material_quality * 0.5)
        building_bsdf.inputs['Metallic'].default_value = 0.3 * material_quality
    elif architectural_style == 'contemporary':
        building_bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.9, 1.0)
        building_bsdf.inputs['Roughness'].default_value = 0.4
    elif architectural_style == 'traditional':
        building_bsdf.inputs['Base Color'].default_value = (0.8, 0.75, 0.7, 1.0)
        building_bsdf.inputs['Roughness'].default_value = 0.6
    else:  # corporate, mixed
        building_bsdf.inputs['Base Color'].default_value = (0.7, 0.75, 0.8, 1.0)
        building_bsdf.inputs['Roughness'].default_value = 0.3
    
    building.data.materials.append(building_mat)
    
    # Add windows with ML parameters - MORE WINDOWS for larger file
    window_count = 0
    for floor in range(num_floors):
        floor_z = 0.5 + floor_height * floor + floor_height/2
        
        # Windows on each side
        for side in range(4):
            angle = side * math.pi / 2
            
            # Calculate position based on building dimensions
            if side % 2 == 0:  # Front/Back
                x = (width/2 - 0.6) * math.cos(angle)
                y = (depth/2 - 0.6) * math.sin(angle)
                window_width = window_size
                window_depth = 0.2
                # Increase window count significantly
                num_windows = max(3, int((width - 2) / (window_spacing * 0.7)))
            else:  # Left/Right
                x = (width/2 - 0.6) * math.cos(angle)
                y = (depth/2 - 0.6) * math.sin(angle)
                window_width = window_size
                window_depth = 0.2
                num_windows = max(3, int((depth - 2) / (window_spacing * 0.7)))
            
            # Create windows based on facade detail level
            for w in range(min(num_windows, facade_detail)):
                offset = (w - num_windows/2 + 0.5) * window_spacing
                if side % 2 == 0:
                    wx, wy = x, y + offset
                else:
                    wx, wy = x + offset, y
                
                # Create window
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=(wx, wy, floor_z)
                )
                window = bpy.context.active_object
                
                if side % 2 == 0:
                    window.scale = (window_depth, window_width, 1.2)
                else:
                    window.scale = (window_width, window_depth, 1.2)
                
                window.name = f"Window_F{floor}_S{side}_W{w}"
                window_count += 1
                
                # Window material (glass)
                window_mat = bpy.data.materials.new(name=f"Glass_{floor}_{side}_{w}")
                window_mat.use_nodes = True
                window_bsdf = window_mat.node_tree.nodes["Principled BSDF"]
                window_bsdf.inputs['Base Color'].default_value = (0.4, 0.7, 1.0, 1.0)
                # Blender 4.x uses 'Transmission Weight' instead of 'Transmission'
                if 'Transmission Weight' in window_bsdf.inputs:
                    window_bsdf.inputs['Transmission Weight'].default_value = 0.95
                elif 'Transmission' in window_bsdf.inputs:
                    window_bsdf.inputs['Transmission'].default_value = 0.95
                window_bsdf.inputs['Roughness'].default_value = 0.05
                window_bsdf.inputs['IOR'].default_value = 1.45
                window.data.materials.append(window_mat)
    
    print(f"Created {window_count} windows")
    
    # Add balconies if enabled (increases geometry complexity)
    if balcony_enabled:
        balcony_count = 0
        for floor in range(1, num_floors):  # Skip ground floor
            floor_z = 0.5 + floor_height * floor
            # Add balconies on front side
            for b in range(max(1, int(width / 6))):
                offset = (b - int(width / 6)/2 + 0.5) * 5
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=(width/2 + 0.8, offset, floor_z)
                )
                balcony = bpy.context.active_object
                balcony.scale = (0.4, 2, 0.05)
                balcony.name = f"Balcony_F{floor}_B{b}"
                balcony_count += 1
                
                # Balcony material
                balcony_mat = bpy.data.materials.new(name=f"Balcony_{floor}_{b}")
                balcony_mat.use_nodes = True
                balcony_bsdf = balcony_mat.node_tree.nodes["Principled BSDF"]
                balcony_bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.7, 1.0)
                balcony_bsdf.inputs['Roughness'].default_value = 0.4
                # Blender 4.x compatible
                if 'Metallic' in balcony_bsdf.inputs:
                    balcony_bsdf.inputs['Metallic'].default_value = 0.5
                balcony.data.materials.append(balcony_mat)
        print(f"Created {balcony_count} balconies")
    
    # Add entrance door
    entrance_z = 0.5 + entrance_width / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(width/2 + 0.3, 0, entrance_z))
    door = bpy.context.active_object
    door.scale = (0.2, entrance_width/2, entrance_width/2)
    door.name = "Entrance_Door"
    door_mat = bpy.data.materials.new(name="Door_Material")
    door_mat.use_nodes = True
    door_bsdf = door_mat.node_tree.nodes["Principled BSDF"]
    door_bsdf.inputs['Base Color'].default_value = (0.3, 0.2, 0.15, 1.0)
    door_bsdf.inputs['Roughness'].default_value = 0.3
    door.data.materials.append(door_mat)
    
    # Add roof
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height + 0.75))
    roof = bpy.context.active_object
    roof.scale = (width/2, depth/2, 0.25)
    roof.name = "Roof"
    
    # Roof material
    roof_mat = bpy.data.materials.new(name="Roof_Material")
    roof_mat.use_nodes = True
    roof_bsdf = roof_mat.node_tree.nodes["Principled BSDF"]
    roof_bsdf.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1.0)
    roof_bsdf.inputs['Roughness'].default_value = 0.6
    roof.data.materials.append(roof_mat)
    
    # Add lighting
    bpy.ops.object.light_add(type='SUN', location=(20, 20, 30))
    sun = bpy.context.active_object
    sun.data.energy = 3
    sun.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    # Add ambient light
    bpy.ops.object.light_add(type='AREA', location=(0, 0, height + 10))
    area_light = bpy.context.active_object
    area_light.data.energy = 100
    area_light.scale = (20, 20, 1)
    
    return building

def export_model(output_path: str, format: str = 'GLB'):
    """Export the generated model."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Exporting to {output_path} as {format}")
    
    if format == 'GLB':
        bpy.ops.export_scene.gltf(
            filepath=str(output_path),
            export_format='GLB',
            export_materials='EXPORT',
            export_lights=True
        )
    elif format == 'FBX':
        bpy.ops.export_scene.fbx(filepath=str(output_path))
    elif format == 'OBJ':
        bpy.ops.export_scene.obj(filepath=str(output_path))
    
    print(f"✓ Model exported successfully to: {output_path}")

def main():
    """Main execution function."""
    print("=" * 60)
    print("Smart City - 3D Building Generator")
    print("=" * 60)
    
    # Get parameters from command line
    argv = sys.argv
    try:
        argv = argv[argv.index("--") + 1:]
    except ValueError:
        print("ERROR: No parameters provided after '--'")
        print("Usage: blender --background --python generate_building.py -- '{\"width\": 20, ...}'")
        sys.exit(1)
    
    if len(argv) < 1:
        print("ERROR: Parameters JSON not provided")
        print("Usage: blender --background --python generate_building.py -- '{\"width\": 20, ...}'")
        sys.exit(1)
    
    try:
        params = json.loads(argv[0])
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)
    
    output_path = params.get('output_path', '/tmp/building.glb')
    
    print(f"\nGenerating building with parameters:")
    print(json.dumps(params, indent=2))
    print()
    
    # Generate
    clear_scene()
    create_building(params)
    export_model(output_path, params.get('format', 'GLB'))
    
    print("\n" + "=" * 60)
    print("✓ Generation complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
