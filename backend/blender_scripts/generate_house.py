#!/usr/bin/env python3
"""
Blender script for procedural house generation from floor plans.
Run headlessly: blender --background --python generate_house.py -- <params_json>
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
    
    # Remove orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def create_house(params: dict):
    """Generate house based on floor plan parameters."""
    # Extract parameters
    width = params.get('width', 12)
    depth = params.get('depth', 10)
    floor_count = params.get('floor_count', 2)
    floor_height = params.get('floor_height', 3.0)
    rooms = params.get('rooms', [])
    style = params.get('style', 'modern')
    
    total_height = floor_count * floor_height
    
    print(f"Creating {style} house: {width}x{depth}m, {floor_count} floors, height={total_height}m")
    print(f"Rooms detected: {len(rooms)}")
    
    # Create foundation
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.3))
    foundation = bpy.context.active_object
    foundation.scale = (width/2, depth/2, 0.3)
    foundation.name = "Foundation"
    
    # Foundation material
    foundation_mat = bpy.data.materials.new(name="Foundation_Material")
    foundation_mat.use_nodes = True
    foundation_bsdf = foundation_mat.node_tree.nodes["Principled BSDF"]
    foundation_bsdf.inputs['Base Color'].default_value = (0.4, 0.4, 0.4, 1.0)
    foundation_bsdf.inputs['Roughness'].default_value = 0.9
    foundation.data.materials.append(foundation_mat)
    
    # Create walls for each floor
    for floor in range(floor_count):
        floor_z = 0.6 + floor * floor_height + floor_height/2
        
        # Main walls
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, floor_z))
        walls = bpy.context.active_object
        walls.scale = (width/2, depth/2, floor_height/2)
        walls.name = f"Floor{floor+1}_Walls"
        
        # Wall material based on style
        wall_mat = bpy.data.materials.new(name=f"Wall_Material_F{floor+1}")
        wall_mat.use_nodes = True
        wall_bsdf = wall_mat.node_tree.nodes["Principled BSDF"]
        
        if style == 'modern':
            wall_bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
            wall_bsdf.inputs['Roughness'].default_value = 0.2
            wall_bsdf.inputs['Metallic'].default_value = 0.1
        elif style == 'traditional':
            wall_bsdf.inputs['Base Color'].default_value = (0.85, 0.75, 0.65, 1.0)
            wall_bsdf.inputs['Roughness'].default_value = 0.8
        else:  # contemporary
            wall_bsdf.inputs['Base Color'].default_value = (0.9, 0.88, 0.85, 1.0)
            wall_bsdf.inputs['Roughness'].default_value = 0.4
        
        walls.data.materials.append(wall_mat)
        
        # Add windows
        create_windows(walls, width, depth, floor_height, floor, style)
    
    # Create roof
    create_roof(width, depth, total_height, style)
    
    # Add door
    create_door(width, depth, style)
    
    # Add floor slabs
    for floor in range(floor_count + 1):
        floor_z = 0.6 + floor * floor_height
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, floor_z))
        slab = bpy.context.active_object
        slab.scale = (width/2 - 0.1, depth/2 - 0.1, 0.15)
        slab.name = f"Slab_Floor{floor}"
        
        # Slab material
        slab_mat = bpy.data.materials.new(name=f"Slab_Material_F{floor}")
        slab_mat.use_nodes = True
        slab_bsdf = slab_mat.node_tree.nodes["Principled BSDF"]
        slab_bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1.0)
        slab_bsdf.inputs['Roughness'].default_value = 0.7
        slab.data.materials.append(slab_mat)

def create_windows(wall_obj, width, depth, floor_height, floor, style):
    """Add windows to the house walls."""
    window_height = 1.5
    window_width = 1.2
    window_z_offset = floor_height * 0.4
    
    # Window material - updated for Blender 4.x compatibility
    window_mat = bpy.data.materials.new(name=f"Window_Material_F{floor}")
    window_mat.use_nodes = True
    window_bsdf = window_mat.node_tree.nodes["Principled BSDF"]
    window_bsdf.inputs['Base Color'].default_value = (0.7, 0.85, 0.95, 0.3)
    window_bsdf.inputs['Roughness'].default_value = 0.05
    # Use Alpha for transparency in Blender 4.x instead of Transmission
    window_bsdf.inputs['Alpha'].default_value = 0.3
    window_mat.blend_method = 'BLEND'
    
    window_count = 0
    
    # Front wall windows
    for i in range(int(width / 2.5)):
        x = -width/2 + 1.5 + i * 2.5
        y = depth/2 + 0.05
        z = 0.6 + floor * floor_height + window_z_offset
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        window = bpy.context.active_object
        window.scale = (window_width/2, 0.05, window_height/2)
        window.name = f"Window_Front_F{floor}_{i}"
        window.data.materials.append(window_mat)
        window_count += 1
    
    # Back wall windows
    for i in range(int(width / 2.5)):
        x = -width/2 + 1.5 + i * 2.5
        y = -depth/2 - 0.05
        z = 0.6 + floor * floor_height + window_z_offset
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        window = bpy.context.active_object
        window.scale = (window_width/2, 0.05, window_height/2)
        window.name = f"Window_Back_F{floor}_{i}"
        window.data.materials.append(window_mat)
        window_count += 1
    
    # Side windows
    for i in range(int(depth / 3)):
        x = width/2 + 0.05
        y = -depth/2 + 2 + i * 3
        z = 0.6 + floor * floor_height + window_z_offset
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        window = bpy.context.active_object
        window.scale = (0.05, window_width/2, window_height/2)
        window.name = f"Window_Side_F{floor}_{i}"
        window.data.materials.append(window_mat)
        window_count += 1
    
    print(f"Added {window_count} windows to floor {floor + 1}")

def create_roof(width, depth, height, style):
    """Create roof based on style."""
    if style == 'modern':
        # Flat roof with slight overhang
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height + 0.7))
        roof = bpy.context.active_object
        roof.scale = (width/2 + 0.3, depth/2 + 0.3, 0.2)
        roof.name = "Roof_Flat"
        
        roof_mat = bpy.data.materials.new(name="Roof_Material")
        roof_mat.use_nodes = True
        roof_bsdf = roof_mat.node_tree.nodes["Principled BSDF"]
        roof_bsdf.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1.0)
        roof_bsdf.inputs['Roughness'].default_value = 0.6
        roof.data.materials.append(roof_mat)
    else:
        # Pitched roof
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(width, depth)/1.4, depth=2, location=(0, 0, height + 1))
        roof = bpy.context.active_object
        roof.rotation_euler[2] = math.pi / 4
        roof.name = "Roof_Pitched"
        
        roof_mat = bpy.data.materials.new(name="Roof_Material")
        roof_mat.use_nodes = True
        roof_bsdf = roof_mat.node_tree.nodes["Principled BSDF"]
        roof_bsdf.inputs['Base Color'].default_value = (0.6, 0.3, 0.2, 1.0)
        roof_bsdf.inputs['Roughness'].default_value = 0.9
        roof.data.materials.append(roof_mat)

def create_door(width, depth, style):
    """Create entrance door."""
    door_width = 1.0
    door_height = 2.2
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, depth/2 + 0.05, 1.1))
    door = bpy.context.active_object
    door.scale = (door_width/2, 0.05, door_height/2)
    door.name = "Door_Main"
    
    # Door material
    door_mat = bpy.data.materials.new(name="Door_Material")
    door_mat.use_nodes = True
    door_bsdf = door_mat.node_tree.nodes["Principled BSDF"]
    
    if style == 'modern':
        door_bsdf.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1.0)
        door_bsdf.inputs['Metallic'].default_value = 0.8
        door_bsdf.inputs['Roughness'].default_value = 0.2
    else:
        door_bsdf.inputs['Base Color'].default_value = (0.4, 0.25, 0.15, 1.0)
        door_bsdf.inputs['Roughness'].default_value = 0.6
    
    door.data.materials.append(door_mat)

def setup_lighting():
    """Add realistic lighting."""
    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-8, 8, 15))
    fill = bpy.context.active_object
    fill.data.energy = 500
    fill.data.size = 10

def setup_camera(width, depth, height):
    """Position camera for good view."""
    # Calculate camera position
    distance = max(width, depth, height) * 2.5
    angle = math.radians(35)
    
    cam_x = distance * math.cos(angle)
    cam_y = -distance * math.sin(angle)
    cam_z = height * 0.8
    
    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(65), 0, math.radians(55))
    
    # Set as active camera
    bpy.context.scene.camera = camera

def main():
    """Main execution function."""
    # Get parameters from command line
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    
    if not argv:
        print("ERROR: No parameters provided")
        print("Usage: blender --background --python generate_house.py -- '{json_params}'")
        sys.exit(1)
    
    params = json.loads(argv[0])
    output_path = params.get('output_path', '/tmp/house.glb')
    
    print(f"Starting house generation with parameters: {params}")
    
    # Clear scene
    clear_scene()
    
    # Generate house
    create_house(params)
    
    # Setup scene
    setup_lighting()
    setup_camera(
        params.get('width', 12),
        params.get('depth', 10),
        params.get('floor_count', 2) * params.get('floor_height', 3.0)
    )
    
    # Export to GLB
    print(f"Exporting to {output_path}")
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_apply=True,
        export_materials='EXPORT'
    )
    
    print(f"✅ House generation complete: {output_path}")

if __name__ == "__main__":
    main()
