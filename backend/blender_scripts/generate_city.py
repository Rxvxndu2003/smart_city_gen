"""
Smart City Full Layout Generator
Generates complete urban scenes with multiple buildings, roads, parks, vehicles
"""
import bpy
import json
import sys
import math
import random
from mathutils import Vector

def clear_scene():
    """Remove all existing objects"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_material(name, base_color, metallic=0.0, roughness=0.5):
    """Create a PBR material"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    
    # Blender 4.x compatibility
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metallic
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_building(x, y, width, depth, height, style='modern'):
    """Create a single building with details"""
    # Main building structure
    bpy.ops.mesh.primitive_cube_add(location=(x, y, height/2))
    building = bpy.context.active_object
    building.scale = (width/2, depth/2, height/2)
    bpy.ops.object.shade_smooth()
    
    # Material based on style
    colors = {
        'modern': (0.9, 0.9, 0.95),
        'glass': (0.7, 0.8, 0.9),
        'residential': (0.95, 0.9, 0.85),
        'commercial': (0.85, 0.85, 0.9)
    }
    mat = create_material(f"building_{style}", colors.get(style, (0.9, 0.9, 0.9)), roughness=0.3)
    building.data.materials.append(mat)
    
    # Add detailed windows for realistic buildings (optimized)
    window_mat = create_glass_material()
    
    floors = max(2, min(8, int(height / 3.5)))  # Limit max floors for performance
    windows_per_floor = max(2, min(4, int(width / 5)))  # Limit windows per floor
    
    # Only add front and back windows (skip sides for performance)
    for floor in range(1, floors):
        floor_height = (floor / floors) * height
        
        for win in range(windows_per_floor):
            # Calculate window position
            win_x_offset = -width/2 + (win + 0.5) * (width / windows_per_floor)
            
            # Front facade windows
            bpy.ops.mesh.primitive_cube_add(location=(x + win_x_offset, y + depth/2 + 0.1, floor_height))
            window = bpy.context.active_object
            window.scale = (0.9, 0.05, 1.2)  # Taller windows
            window.data.materials.append(window_mat)
            
            # Back facade windows
            bpy.ops.mesh.primitive_cube_add(location=(x + win_x_offset, y - depth/2 - 0.1, floor_height))
            window = bpy.context.active_object
            window.scale = (0.9, 0.05, 1.2)
            window.data.materials.append(window_mat)
    
    return building

def create_glass_material():
    """Create transparent glass material"""
    mat = bpy.data.materials.new(name="glass_window")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.7, 0.85, 0.95, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    
    # Blender 4.x compatibility for transparency
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = 0.9
    elif 'Transmission' in bsdf.inputs:
        bsdf.inputs['Transmission'].default_value = 0.9
    
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = 0.1
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_road(x1, y1, x2, y2, width=6):
    """Create a road segment"""
    length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    angle = math.atan2(y2-y1, x2-x1)
    
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    bpy.ops.mesh.primitive_cube_add(location=(center_x, center_y, 0.05))
    road = bpy.context.active_object
    road.scale = (length/2, width/2, 0.05)
    road.rotation_euler = (0, 0, angle)
    
    road_mat = create_material("asphalt", (0.2, 0.2, 0.2), roughness=0.8)
    road.data.materials.append(road_mat)
    
    # Add road markings - center line (dashed)
    marking_mat = create_material("road_marking", (0.95, 0.95, 0.0), roughness=0.4)  # Yellow center line
    dash_length = 3
    gap_length = 2
    
    for i in range(0, int(length), dash_length + gap_length):
        if i + dash_length > length:
            break
        
        t = i / length
        dash_x = x1 + (x2 - x1) * t
        dash_y = y1 + (y2 - y1) * t
        
        # Center dashed line
        bpy.ops.mesh.primitive_cube_add(location=(dash_x, dash_y, 0.11))
        marking = bpy.context.active_object
        marking.scale = (dash_length/2, 0.15, 0.01)
        marking.rotation_euler = (0, 0, angle)
        marking.data.materials.append(marking_mat)
    
    # Add edge lines (solid white)
    edge_mat = create_material("edge_line", (0.95, 0.95, 0.95), roughness=0.4)
    
    # Left edge line
    bpy.ops.mesh.primitive_cube_add(location=(center_x, center_y, 0.11))
    left_edge = bpy.context.active_object
    left_edge.scale = (length/2, 0.1, 0.01)
    left_edge.rotation_euler = (0, 0, angle)
    # Offset to left edge
    offset_dist = width/2 - 0.3
    left_edge.location.x += -offset_dist * math.sin(angle)
    left_edge.location.y += offset_dist * math.cos(angle)
    left_edge.data.materials.append(edge_mat)
    
    # Right edge line
    bpy.ops.mesh.primitive_cube_add(location=(center_x, center_y, 0.11))
    right_edge = bpy.context.active_object
    right_edge.scale = (length/2, 0.1, 0.01)
    right_edge.rotation_euler = (0, 0, angle)
    # Offset to right edge
    right_edge.location.x += offset_dist * math.sin(angle)
    right_edge.location.y += -offset_dist * math.cos(angle)
    right_edge.data.materials.append(edge_mat)
    
    return road

def create_parking_lot(x, y, size=20, num_spaces=12):
    """Create a visible parking lot with marked spaces"""
    # Parking lot surface (slightly lighter than road)
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 0.06))
    parking = bpy.context.active_object
    parking.scale = (size/2, size/2, 0.06)
    
    parking_mat = create_material("parking_surface", (0.3, 0.3, 0.3), roughness=0.7)
    parking.data.materials.append(parking_mat)
    
    # Parking space markings (white lines)
    marking_mat = create_material("parking_line", (0.95, 0.95, 0.95), roughness=0.4)
    
    # Calculate parking space layout (2 rows)
    spaces_per_row = num_spaces // 2
    space_width = size / (spaces_per_row + 1)
    
    for row in range(2):
        y_offset = -size/4 if row == 0 else size/4
        
        for i in range(spaces_per_row + 1):
            x_pos = x - size/2 + i * space_width
            
            # Vertical line for parking space
            bpy.ops.mesh.primitive_cube_add(location=(x_pos, y + y_offset, 0.13))
            line = bpy.context.active_object
            line.scale = (0.08, size/4.5, 0.01)
            line.data.materials.append(marking_mat)
    
    # Horizontal separating line
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 0.13))
    center_line = bpy.context.active_object
    center_line.scale = (size/2, 0.08, 0.01)
    center_line.data.materials.append(marking_mat)
    
    # Add "P" parking sign
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 3))
    sign = bpy.context.active_object
    sign.scale = (1.5, 0.1, 2)
    sign_mat = create_material("parking_sign", (0.1, 0.3, 0.8), roughness=0.3)
    sign.data.materials.append(sign_mat)
    
    return parking

def create_park(x, y, size=20):
    """Create a park with grass and trees"""
    # Grass area
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 0.02))
    grass = bpy.context.active_object
    grass.scale = (size/2, size/2, 0.02)
    
    grass_mat = create_material("grass", (0.3, 0.6, 0.3), roughness=0.9)
    grass.data.materials.append(grass_mat)
    
    # Add just 2 simple trees for performance
    tree_mat = create_material("tree", (0.2, 0.5, 0.2), roughness=0.9)
    trunk_mat = create_material("trunk", (0.4, 0.3, 0.2), roughness=0.8)
    
    for _ in range(2):  # Only 2 trees per park
        tree_x = x + random.uniform(-size/3, size/3)
        tree_y = y + random.uniform(-size/3, size/3)
        
        # Trunk
        bpy.ops.mesh.primitive_cylinder_add(location=(tree_x, tree_y, 2), radius=0.3, depth=4)
        trunk = bpy.context.active_object
        trunk.data.materials.append(trunk_mat)
        
        # Foliage
        bpy.ops.mesh.primitive_uv_sphere_add(location=(tree_x, tree_y, 5), radius=2)
        foliage = bpy.context.active_object
        foliage.data.materials.append(tree_mat)
    
    return grass

def create_vehicle(x, y, rotation=0):
    """Create a simple vehicle/car"""
    # Car body
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 0.8))
    body = bpy.context.active_object
    body.scale = (2, 1, 0.6)
    body.rotation_euler = (0, 0, rotation)
    
    car_colors = [(0.8, 0.1, 0.1), (0.1, 0.3, 0.8), (0.9, 0.9, 0.9), (0.2, 0.2, 0.2)]
    car_mat = create_material("car_body", random.choice(car_colors), metallic=0.7, roughness=0.2)
    body.data.materials.append(car_mat)
    
    # Windows (simple)
    window_mat = create_glass_material()
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 1.2))
    window = bpy.context.active_object
    window.scale = (1.2, 0.8, 0.4)
    window.rotation_euler = (0, 0, rotation)
    window.data.materials.append(window_mat)
    
    return body

def create_ground_plane(size=200):
    """Create large ground plane"""
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0), size=size)
    ground = bpy.context.active_object
    
    ground_mat = create_material("ground", (0.5, 0.5, 0.5), roughness=0.8)
    ground.data.materials.append(ground_mat)
    
    return ground

def create_city_layout(params):
    """Generate complete city layout based on project parameters"""
    print("\n" + "="*60)
    print("GENERATING SMART CITY LAYOUT")
    print("="*60)
    
    grid_size = params.get('grid_size', 10)
    block_size = params.get('block_size', 30)
    road_width = params.get('road_width', 6)
    
    # Project context for intelligent generation
    project_type = params.get('project_type', 'Mixed-Use')
    location_city = params.get('location_city', '')
    description = params.get('project_description', '')
    avg_building_height = params.get('building_height', 30.0)
    num_floors = params.get('num_floors', 10)
    parking_required = params.get('parking_spaces', 50)
    
    print(f"\nProject Context:")
    print(f"  Type: {project_type}")
    print(f"  Location: {location_city}")
    print(f"  Target Height: {avg_building_height}m ({num_floors} floors)")
    print(f"  Parking Needed: {parking_required} spaces")
    if description:
        print(f"  Description: {description[:100]}...")
    
    # Create ground
    create_ground_plane(size=grid_size * block_size * 2)
    
    # Create road grid
    print(f"\nCreating road network ({grid_size}x{grid_size} grid)...")
    for i in range(grid_size + 1):
        offset = i * block_size - (grid_size * block_size) / 2
        
        # Horizontal roads
        create_road(
            -(grid_size * block_size) / 2, offset,
            (grid_size * block_size) / 2, offset,
            road_width
        )
        
        # Vertical roads
        create_road(
            offset, -(grid_size * block_size) / 2,
            offset, (grid_size * block_size) / 2,
            road_width
        )
    
    print("✓ Road network created")
    
    # Generate buildings in blocks based on project type
    print(f"\nGenerating buildings for {project_type} project...")
    building_count = 0
    building_styles = ['modern', 'glass', 'residential', 'commercial']
    
    # Adjust building distribution based on project type
    if 'Residential' in project_type:
        building_prob = 0.55  # More open space
        park_prob = 0.20
        parking_prob = 0.15  # Dedicated parking areas
        height_range = (avg_building_height * 0.5, avg_building_height * 1.2)
        style_weights = {'residential': 0.6, 'modern': 0.3, 'glass': 0.1, 'commercial': 0.0}
    elif 'Commercial' in project_type:
        building_prob = 0.65  # Denser
        park_prob = 0.10
        parking_prob = 0.20  # More parking for commercial
        height_range = (avg_building_height * 0.7, avg_building_height * 1.5)
        style_weights = {'commercial': 0.5, 'glass': 0.3, 'modern': 0.2, 'residential': 0.0}
    else:  # Mixed-Use
        building_prob = 0.60
        park_prob = 0.15
        parking_prob = 0.18
        height_range = (avg_building_height * 0.6, avg_building_height * 1.3)
        style_weights = {'modern': 0.3, 'glass': 0.3, 'residential': 0.2, 'commercial': 0.2}
    
    parking_lot_count = 0
    
    for i in range(grid_size):
        for j in range(grid_size):
            # Calculate block center
            block_x = (i - grid_size/2 + 0.5) * block_size
            block_y = (j - grid_size/2 + 0.5) * block_size
            
            # Randomly decide what to place based on project type
            rand = random.random()
            
            if rand < park_prob:  # Parks
                create_park(block_x, block_y, block_size - road_width - 2)
            elif rand < (park_prob + parking_prob):  # Parking lots
                spaces = random.randint(8, 16)
                create_parking_lot(block_x, block_y, block_size - road_width - 2, spaces)
                parking_lot_count += 1
            elif rand < (park_prob + parking_prob + building_prob):  # Buildings
                # Building dimensions based on project parameters
                width = random.uniform(10, block_size - road_width - 5)
                depth = random.uniform(10, block_size - road_width - 5)
                height = random.uniform(*height_range)
                
                # Choose style based on project type
                styles_list = [s for s, w in style_weights.items() if w > 0]
                weights_list = [style_weights[s] for s in styles_list]
                style = random.choices(styles_list, weights=weights_list)[0]
                
                create_building(block_x, block_y, width, depth, height, style)
                building_count += 1
            # else: empty lots
    
    print(f"✓ Created {building_count} buildings")
    print(f"✓ Created {parking_lot_count} parking lots")
    
    # Add vehicles on roads based on parking requirements
    print(f"\nAdding vehicles (targeting {parking_required} parking spaces)...")
    vehicle_count = 0
    num_vehicles = min(parking_required, grid_size * grid_size * 3)  # Scale with city size
    
    for _ in range(num_vehicles):
        # Place on random road
        if random.random() < 0.5:
            # Horizontal road
            road_idx = random.randint(0, grid_size)
            x = random.uniform(-(grid_size * block_size) / 2 + 10, (grid_size * block_size) / 2 - 10)
            y = road_idx * block_size - (grid_size * block_size) / 2 + random.uniform(-1, 1)
            rotation = random.choice([0, math.pi])
        else:
            # Vertical road
            road_idx = random.randint(0, grid_size)
            x = road_idx * block_size - (grid_size * block_size) / 2 + random.uniform(-1, 1)
            y = random.uniform(-(grid_size * block_size) / 2 + 10, (grid_size * block_size) / 2 - 10)
            rotation = random.choice([math.pi/2, -math.pi/2])
        
        create_vehicle(x, y, rotation)
        vehicle_count += 1
    
    print(f"✓ Added {vehicle_count} vehicles")
    
    # Add lighting
    print("\nSetting up lighting...")
    bpy.ops.object.light_add(type='SUN', location=(50, 50, 100))
    sun = bpy.context.active_object
    sun.data.energy = 3
    sun.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    # Ambient light
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 150))
    ambient = bpy.context.active_object
    ambient.data.energy = 1000
    ambient.data.size = 200
    
    print("✓ Lighting configured")
    
    print("\n" + "="*60)
    print(f"CITY GENERATION COMPLETE!")
    print(f"  Buildings: {building_count}")
    print(f"  Vehicles: {vehicle_count}")
    print(f"  Grid: {grid_size}x{grid_size} blocks")
    print("="*60 + "\n")

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Error: No parameters provided")
        sys.exit(1)
    
    # Get parameters from command line
    params_json = sys.argv[-1]
    try:
        params = json.loads(params_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    output_path = params.get('output_path', 'city.glb')
    export_format = params.get('format', 'GLB')
    
    print("Starting city generation with parameters:")
    print(json.dumps(params, indent=2))
    
    # Clear scene and generate city
    clear_scene()
    create_city_layout(params)
    
    # Export
    print(f"\nExporting to {output_path} as {export_format}")
    
    if export_format == 'GLB':
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format='GLB',
            export_materials='EXPORT',
            export_apply=True
        )
    else:
        bpy.ops.export_scene.obj(
            filepath=output_path,
            use_materials=True,
            use_edges=True
        )
    
    print(f"✓ City exported successfully to {output_path}")

if __name__ == "__main__":
    main()
