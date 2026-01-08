"""
Blender script to render multiple camera views of a generated city.
This script loads a city GLB file and renders it from multiple angles.
"""
import bpy
import sys
import json
import math
from pathlib import Path

def setup_camera(location, rotation, name="Camera"):
    """Set up camera at specific location and rotation."""
    # Get or create camera
    if "Camera" in bpy.data.objects:
        camera = bpy.data.objects["Camera"]
    else:
        camera_data = bpy.data.cameras.new(name="Camera")
        camera = bpy.data.objects.new("Camera", camera_data)
        bpy.context.scene.collection.objects.link(camera)
    
    camera.location = location
    camera.rotation_euler = rotation
    bpy.context.scene.camera = camera
    return camera

def setup_lighting():
    """Set up realistic lighting for the scene."""
    # Remove default lights
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete()
    
    # Add sun light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    # Add ambient light
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.8, 0.9, 1.0, 1.0)  # Sky blue
    bg.inputs[1].default_value = 0.3  # Strength

def setup_render_settings(output_path, resolution_x=1024, resolution_y=1024):
    """Configure render settings."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = output_path

def calculate_camera_positions(num_views, distance=100, height=50):
    """Calculate camera positions around the city."""
    positions = []
    
    for i in range(num_views):
        angle = (2 * math.pi * i) / num_views
        
        # Position camera in a circle around the city
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)
        z = height
        
        # Calculate rotation to look at center
        rot_z = angle + math.radians(90)
        rot_x = math.radians(60)  # Look down at 60 degrees
        rot_y = 0
        
        positions.append({
            'location': (x, y, z),
            'rotation': (rot_x, rot_y, rot_z),
            'name': f'view_{i+1}'
        })
    
    return positions

def render_views(glb_path, output_dir, num_views=4):
    """
    Render multiple views of the city.
    
    Args:
        glb_path: Path to the city GLB file
        output_dir: Directory to save rendered images
        num_views: Number of camera views to render
    """
    print(f"\n{'='*60}")
    print(f"RENDERING CITY VIEWS")
    print(f"{'='*60}")
    print(f"GLB File: {glb_path}")
    print(f"Output Directory: {output_dir}")
    print(f"Number of Views: {num_views}")
    print(f"{'='*60}\n")
    
    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Import GLB file
    print(f"Loading GLB file...")
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    print(f"✓ GLB loaded successfully")
    
    # Setup lighting
    print(f"Setting up lighting...")
    setup_lighting()
    print(f"✓ Lighting configured")
    
    # Calculate camera positions
    camera_positions = calculate_camera_positions(num_views)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Render each view
    rendered_files = []
    for i, cam_pos in enumerate(camera_positions):
        print(f"\nRendering view {i+1}/{num_views}...")
        
        # Setup camera
        setup_camera(
            location=cam_pos['location'],
            rotation=cam_pos['rotation'],
            name=cam_pos['name']
        )
        
        # Setup render output
        output_file = output_path / f"{cam_pos['name']}.png"
        setup_render_settings(str(output_file))
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        rendered_files.append(str(output_file))
        print(f"✓ View {i+1} rendered: {output_file}")
    
    print(f"\n{'='*60}")
    print(f"✓ All {num_views} views rendered successfully!")
    print(f"{'='*60}\n")
    
    return rendered_files

if __name__ == "__main__":
    # Get parameters from command line
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]  # Get args after --
    
    if len(argv) > 0:
        params = json.loads(argv[0])
        
        glb_path = params.get('glb_path')
        output_dir = params.get('output_dir')
        num_views = params.get('num_views', 4)
        
        if glb_path and output_dir:
            rendered_files = render_views(glb_path, output_dir, num_views)
            
            # Save list of rendered files
            manifest_path = Path(output_dir) / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump({'rendered_files': rendered_files}, f, indent=2)
            
            print(f"Manifest saved to: {manifest_path}")
        else:
            print("Error: glb_path and output_dir are required")
            sys.exit(1)
    else:
        print("Error: No parameters provided")
        sys.exit(1)
