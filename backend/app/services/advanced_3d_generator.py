"""
Advanced 3D House Generation Service
Uses trimesh for 3D modeling and integrates with AI generation APIs
"""
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
import requests
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class Advanced3DGenerator:
    """
    Advanced 3D house generator using real 3D modeling libraries
    and AI generation APIs.
    """
    
    def __init__(self):
        """Initialize the 3D generator."""
        from dotenv import load_dotenv
        load_dotenv()
        self.meshy_api_key = os.getenv("MESHY_API_KEY", "")
        self.meshy_api_url = "https://api.meshy.ai/openapi/v1/image-to-3d"
        self.use_ai_api = bool(self.meshy_api_key)
        
        if self.use_ai_api:
            logger.info("Meshy AI API enabled - will use AI generation when possible")
        
    def generate_house_from_floorplan(
        self,
        floor_plan_path: Path,
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate 3D house model from 2D floor plan.
        
        Args:
            floor_plan_path: Path to floor plan image
            output_path: Where to save the 3D model
            metadata: Optional metadata (rooms, style, dimensions)
            
        Returns:
            Generation results
        """
        try:
            # Load and analyze floor plan
            floor_plan = Image.open(floor_plan_path)
            analysis = self._analyze_floor_plan(floor_plan, metadata)
            
            # Try AI API first if available
            if self.use_ai_api:
                try:
                    result = self._generate_with_ai_api(floor_plan_path, analysis)
                    if result.get("success"):
                        return result
                except Exception as e:
                    logger.warning(f"AI API generation failed, falling back to procedural: {e}")
            
            # Fallback: Procedural generation with trimesh
            mesh = self._generate_procedural_house(analysis)
            
            # Export to GLB
            mesh.export(str(output_path))
            
            logger.info(f"Generated 3D house model at {output_path}")
            
            return {
                "success": True,
                "model_path": str(output_path),
                "method": "procedural_trimesh",
                "analysis": analysis,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"3D generation error: {str(e)}")
            raise
    
    def _analyze_floor_plan(
        self,
        floor_plan: Image.Image,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze floor plan to extract building parameters.
        
        Uses image processing to detect:
        - Building outline/footprint
        - Room divisions
        - Estimated dimensions
        """
        # Convert to numpy array
        img_array = np.array(floor_plan.convert('L'))
        
        # Estimate building dimensions from image
        height, width = img_array.shape
        aspect_ratio = width / height
        
        # Default dimensions (can be overridden by metadata)
        building_width = metadata.get("width", 12.0) if metadata else 12.0
        building_length = metadata.get("length", 15.0) if metadata else 15.0
        building_height = metadata.get("height", 9.0) if metadata else 9.0
        num_floors = metadata.get("floors", 2) if metadata else 2
        
        # Detect rooms from image (simplified - would use CV in production)
        rooms = metadata.get("rooms", 5) if metadata else 5
        bedrooms = metadata.get("bedrooms", 3) if metadata else 3
        
        style = metadata.get("style", "modern") if metadata else "modern"
        
        return {
            "building_width": building_width,
            "building_length": building_length,
            "building_height": building_height,
            "num_floors": num_floors,
            "rooms": rooms,
            "bedrooms": bedrooms,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "floor_plan_size": (width, height)
        }
    
    def _generate_procedural_house(self, analysis: Dict[str, Any]) -> trimesh.Trimesh:
        """
        Generate house mesh procedurally using trimesh.
        Creates a realistic house with walls, roof, windows, doors.
        """
        width = analysis["building_width"]
        length = analysis["building_length"]
        height = analysis["building_height"]
        num_floors = analysis["num_floors"]
        style = analysis["style"]
        
        # Create house components
        meshes = []
        
        # 1. Foundation/Base
        foundation = trimesh.creation.box(
            extents=[width, length, 0.5],
            transform=trimesh.transformations.translation_matrix([0, 0, 0.25])
        )
        # Foundation color - dark gray
        foundation_color = np.array([80, 80, 80, 255], dtype=np.uint8)
        foundation.visual.vertex_colors = np.tile(foundation_color, (len(foundation.vertices), 1))
        meshes.append(foundation)
        logger.info(f"Added foundation: {len(foundation.vertices)} vertices")
        
        # 2. Main building body (walls)
        wall_height = height * 0.6
        walls = self._create_walls(width, length, wall_height, num_floors)
        meshes.extend(walls)
        logger.info(f"Added {len(walls)} wall components")
        
        # 2.5. Interior floors and walls
        interior_elements = self._create_interior(width, length, wall_height, num_floors, analysis)
        meshes.extend(interior_elements)
        logger.info(f"Added {len(interior_elements)} interior elements (floors, walls, divisions)")
        
        # 3. Roof
        roof = self._create_roof(width, length, height, style)
        meshes.append(roof)
        logger.info(f"Added roof: {len(roof.vertices)} vertices")
        
        # 4. Windows
        windows = self._create_windows(width, length, wall_height, num_floors)
        meshes.extend(windows)
        logger.info(f"Added {len(windows)} windows")
        
        # 5. Door
        door = self._create_door(width, length)
        meshes.append(door)
        logger.info(f"Added door: {len(door.vertices)} vertices")
        
        # 6. Optional: Chimney for traditional style
        if style == "traditional":
            chimney = self._create_chimney(width, length, height)
            meshes.append(chimney)
            logger.info(f"Added chimney")
        
        # Combine all meshes with vertex colors
        logger.info(f"Combining {len(meshes)} mesh components...")
        combined = trimesh.util.concatenate(meshes)
        logger.info(f"Final model: {len(combined.vertices)} vertices, {len(combined.faces)} faces")
        
        return combined
    
    def _create_walls(
        self,
        width: float,
        length: float,
        height: float,
        num_floors: int
    ) -> list:
        """Create building walls."""
        wall_thickness = 0.3
        meshes = []
        
        # Wall color - beige/cream
        wall_color = np.array([220, 210, 190, 255], dtype=np.uint8)
        
        # Create hollow walls using individual wall panels instead of boolean operations
        # This is more reliable and doesn't require external engines
        
        # Front wall
        front_wall = trimesh.creation.box(
            extents=[width, wall_thickness, height],
            transform=trimesh.transformations.translation_matrix([0, -length/2 + wall_thickness/2, height/2 + 0.5])
        )
        front_wall.visual.vertex_colors = np.tile(wall_color, (len(front_wall.vertices), 1))
        meshes.append(front_wall)
        
        # Back wall
        back_wall = trimesh.creation.box(
            extents=[width, wall_thickness, height],
            transform=trimesh.transformations.translation_matrix([0, length/2 - wall_thickness/2, height/2 + 0.5])
        )
        back_wall.visual.vertex_colors = np.tile(wall_color, (len(back_wall.vertices), 1))
        meshes.append(back_wall)
        
        # Left wall
        left_wall = trimesh.creation.box(
            extents=[wall_thickness, length - 2*wall_thickness, height],
            transform=trimesh.transformations.translation_matrix([-width/2 + wall_thickness/2, 0, height/2 + 0.5])
        )
        left_wall.visual.vertex_colors = np.tile(wall_color, (len(left_wall.vertices), 1))
        meshes.append(left_wall)
        
        # Right wall
        right_wall = trimesh.creation.box(
            extents=[wall_thickness, length - 2*wall_thickness, height],
            transform=trimesh.transformations.translation_matrix([width/2 - wall_thickness/2, 0, height/2 + 0.5])
        )
        right_wall.visual.vertex_colors = np.tile(wall_color, (len(right_wall.vertices), 1))
        meshes.append(right_wall)
        
        # Floor divisions
        for i in range(1, num_floors):
            floor_z = (height / num_floors) * i + 0.5
            floor = trimesh.creation.box(
                extents=[width - wall_thickness, length - wall_thickness, 0.2],
                transform=trimesh.transformations.translation_matrix([0, 0, floor_z])
            )
            meshes.append(floor)
        
        return meshes
    
    def _create_interior(
        self,
        width: float,
        length: float,
        height: float,
        num_floors: int,
        analysis: Dict[str, Any]
    ) -> list:
        """Create interior elements - floors, room divisions, walls."""
        meshes = []
        wall_thickness = 0.15  # Thinner for interior walls
        floor_thickness = 0.2
        
        # Interior floor color - light wood
        floor_color = np.array([205, 170, 125, 255], dtype=np.uint8)
        # Interior wall color - white/off-white
        interior_wall_color = np.array([245, 245, 240, 255], dtype=np.uint8)
        
        # Create floor slabs for each floor
        for floor_num in range(num_floors):
            floor_z = (height / num_floors) * floor_num + 0.5
            
            # Floor slab (slightly smaller than exterior to sit inside walls)
            floor_slab = trimesh.creation.box(
                extents=[width - 0.6, length - 0.6, floor_thickness],
                transform=trimesh.transformations.translation_matrix([0, 0, floor_z + floor_thickness/2])
            )
            floor_slab.visual.vertex_colors = np.tile(floor_color, (len(floor_slab.vertices), 1))
            meshes.append(floor_slab)
        
        # Add interior room divisions based on floor plan
        # For a typical house, divide into rooms
        rooms = analysis.get("rooms", 5)
        
        # Horizontal division (separates front and back areas)
        if length > 8:
            # Central hallway/division wall
            division_y = 0  # Center of the house
            division_wall = trimesh.creation.box(
                extents=[width - 0.6, wall_thickness, height],
                transform=trimesh.transformations.translation_matrix([0, division_y, height/2 + 0.5])
            )
            division_wall.visual.vertex_colors = np.tile(interior_wall_color, (len(division_wall.vertices), 1))
            meshes.append(division_wall)
        
        # Vertical divisions (create separate rooms)
        if width > 8 and rooms >= 3:
            # Left room division
            division_x1 = -width/4
            left_division = trimesh.creation.box(
                extents=[wall_thickness, length/2 - 0.6, height],
                transform=trimesh.transformations.translation_matrix([division_x1, -length/4, height/2 + 0.5])
            )
            left_division.visual.vertex_colors = np.tile(interior_wall_color, (len(left_division.vertices), 1))
            meshes.append(left_division)
            
            # Right room division
            division_x2 = width/4
            right_division = trimesh.creation.box(
                extents=[wall_thickness, length/2 - 0.6, height],
                transform=trimesh.transformations.translation_matrix([division_x2, length/4, height/2 + 0.5])
            )
            right_division.visual.vertex_colors = np.tile(interior_wall_color, (len(right_division.vertices), 1))
            meshes.append(right_division)
        
        # Add stairs for multi-floor buildings
        if num_floors > 1:
            stairs = self._create_stairs(width, length, height, num_floors)
            meshes.extend(stairs)
        
        return meshes
    
    def _create_stairs(
        self,
        width: float,
        length: float,
        height: float,
        num_floors: int
    ) -> list:
        """Create stairs between floors."""
        meshes = []
        
        # Stair color - darker wood
        stair_color = np.array([139, 90, 60, 255], dtype=np.uint8)
        
        floor_height = height / num_floors
        num_steps = 12  # Steps per floor
        step_height = floor_height / num_steps
        step_depth = 0.3
        step_width = 1.5
        
        # Position stairs in corner of house
        stair_x = width/2 - 2
        stair_y = -length/2 + 2
        
        for floor in range(num_floors - 1):
            base_z = floor * floor_height + 0.5
            
            for step in range(num_steps):
                step_z = base_z + step * step_height
                step_y = stair_y + step * step_depth
                
                stair_step = trimesh.creation.box(
                    extents=[step_width, step_depth, step_height],
                    transform=trimesh.transformations.translation_matrix([stair_x, step_y, step_z + step_height/2])
                )
                stair_step.visual.vertex_colors = np.tile(stair_color, (len(stair_step.vertices), 1))
                meshes.append(stair_step)
        
        return meshes
    
    def _create_roof(
        self,
        width: float,
        length: float,
        total_height: float,
        style: str
    ) -> trimesh.Trimesh:
        """Create roof based on style."""
        wall_height = total_height * 0.6
        roof_height = total_height - wall_height
        roof_base_z = wall_height + 0.5
        
        if style == "modern":
            # Flat roof
            roof = trimesh.creation.box(
                extents=[width + 0.5, length + 0.5, 0.3],
                transform=trimesh.transformations.translation_matrix([0, 0, roof_base_z + roof_height - 0.15])
            )
        else:
            # Gabled roof (pyramid/tent shape)
            vertices = np.array([
                [-width/2 - 0.3, -length/2 - 0.3, roof_base_z],
                [width/2 + 0.3, -length/2 - 0.3, roof_base_z],
                [width/2 + 0.3, length/2 + 0.3, roof_base_z],
                [-width/2 - 0.3, length/2 + 0.3, roof_base_z],
                [0, 0, roof_base_z + roof_height]
            ])
            
            faces = np.array([
                [0, 1, 4],
                [1, 2, 4],
                [2, 3, 4],
                [3, 0, 4],
                [0, 3, 2],
                [0, 2, 1]
            ])
            
            roof = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Roof color - terracotta/brown for traditional, dark gray for modern
        if style == "modern":
            roof_color = np.array([70, 70, 70, 255], dtype=np.uint8)
        else:
            roof_color = np.array([156, 102, 68, 255], dtype=np.uint8)
        
        roof.visual.vertex_colors = np.tile(roof_color, (len(roof.vertices), 1))
        
        return roof
    
    def _create_windows(
        self,
        width: float,
        length: float,
        height: float,
        num_floors: int
    ) -> list:
        """Create windows on walls."""
        windows = []
        window_width = 1.2
        window_height = 1.5
        window_depth = 0.1
        
        # Window color - light blue/cyan (glass)
        window_color = np.array([135, 206, 235, 200], dtype=np.uint8)
        
        # Windows per floor
        for floor in range(num_floors):
            floor_z = (height / num_floors) * floor + (height / num_floors) / 2 + 0.5
            
            # Front wall windows (2-3 windows)
            num_windows = 2 if width < 10 else 3
            spacing = width / (num_windows + 1)
            
            for i in range(num_windows):
                x_pos = -width/2 + spacing * (i + 1)
                window = trimesh.creation.box(
                    extents=[window_width, window_depth, window_height],
                    transform=trimesh.transformations.translation_matrix([x_pos, -length/2, floor_z])
                )
                window.visual.vertex_colors = np.tile(window_color, (len(window.vertices), 1))
                windows.append(window)
            
            # Back wall windows
            for i in range(num_windows):
                x_pos = -width/2 + spacing * (i + 1)
                window = trimesh.creation.box(
                    extents=[window_width, window_depth, window_height],
                    transform=trimesh.transformations.translation_matrix([x_pos, length/2, floor_z])
                )
                window.visual.vertex_colors = np.tile(window_color, (len(window.vertices), 1))
                windows.append(window)
            
            # Side windows (1-2 per side)
            side_windows = 2
            side_spacing = length / (side_windows + 1)
            
            for i in range(side_windows):
                y_pos = -length/2 + side_spacing * (i + 1)
                window = trimesh.creation.box(
                    extents=[window_depth, window_width, window_height],
                    transform=trimesh.transformations.translation_matrix([-width/2, y_pos, floor_z])
                )
                window.visual.vertex_colors = np.tile(window_color, (len(window.vertices), 1))
                windows.append(window)
                
                window = trimesh.creation.box(
                    extents=[window_depth, window_width, window_height],
                    transform=trimesh.transformations.translation_matrix([width/2, y_pos, floor_z])
                )
                window.visual.vertex_colors = np.tile(window_color, (len(window.vertices), 1))
                windows.append(window)
        
        return windows
    
    def _create_door(self, width: float, length: float) -> trimesh.Trimesh:
        """Create front door."""
        door_width = 1.0
        door_height = 2.2
        door_depth = 0.15
        
        door = trimesh.creation.box(
            extents=[door_width, door_depth, door_height],
            transform=trimesh.transformations.translation_matrix([0, -length/2, 0.5 + door_height/2])
        )
        
        # Door color - dark brown
        door_color = np.array([101, 67, 33, 255], dtype=np.uint8)
        door.visual.vertex_colors = np.tile(door_color, (len(door.vertices), 1))
        
        return door
    
    def _create_chimney(self, width: float, length: float, height: float) -> trimesh.Trimesh:
        """Create chimney for traditional style."""
        chimney_width = 1.0
        chimney_height = height * 0.3
        
        chimney = trimesh.creation.box(
            extents=[chimney_width, chimney_width, chimney_height],
            transform=trimesh.transformations.translation_matrix([
                width/3, 
                length/3, 
                height + chimney_height/2
            ])
        )
        
        # Chimney color - brick red
        chimney_color = np.array([178, 34, 34, 255], dtype=np.uint8)
        chimney.visual.vertex_colors = np.tile(chimney_color, (len(chimney.vertices), 1))
        
        return chimney
    
    def _generate_with_ai_api(
        self,
        floor_plan_path: Path,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate 3D model using Meshy AI API.
        
        Converts floor plan image to base64 and sends to Meshy for AI generation.
        """
        if not self.meshy_api_key:
            raise ValueError("No AI API key configured")
        
        try:
            import base64
            import time
            
            logger.info(f"Starting Meshy AI generation for {floor_plan_path}")
            
            # Read and encode the floor plan image as base64
            with open(floor_plan_path, 'rb') as f:
                image_data = f.read()
            
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image format
            image_ext = floor_plan_path.suffix.lower()
            mime_type = 'image/png' if image_ext == '.png' else 'image/jpeg'
            
            # Create data URI
            data_uri = f"data:{mime_type};base64,{base64_image}"
            
            # Prepare API request
            headers = {
                'Authorization': f'Bearer {self.meshy_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'image_url': data_uri,
                'enable_pbr': True,
                'should_remesh': True,
                'should_texture': True,
                'ai_model': 'latest',  # Use Meshy-6 Preview
                'topology': 'quad',
                'target_polycount': 30000
            }
            
            # Create the task
            logger.info("Sending request to Meshy AI API...")
            response = requests.post(self.meshy_api_url, headers=headers, json=payload)
            
            if response.status_code not in (200, 202):
                logger.error(f"Meshy API error: {response.status_code} - {response.text}")
                return {"success": False, "reason": f"API error: {response.status_code}"}
            
            task_data = response.json()
            task_id = task_data.get('result')
            
            if not task_id:
                logger.error(f"No task ID in response: {task_data}")
                return {"success": False, "reason": "No task ID received"}
            
            logger.info(f"Task created: {task_id}, waiting for completion...")
            
            # Poll for task completion (max 5 minutes)
            max_wait = 300  # 5 minutes
            poll_interval = 5  # 5 seconds
            elapsed = 0
            
            retrieve_url = f"{self.meshy_api_url}/{task_id}"
            
            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                
                status_response = requests.get(retrieve_url, headers=headers)
                
                if status_response.status_code != 200:
                    logger.error(f"Status check failed: {status_response.status_code}")
                    continue
                
                status_data = status_response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                
                logger.info(f"Task {task_id}: {status} - {progress}% complete")
                
                if status == 'SUCCEEDED':
                    # Download the GLB file
                    model_urls = status_data.get('model_urls', {})
                    glb_url = model_urls.get('glb')
                    
                    if not glb_url:
                        return {"success": False, "reason": "No GLB URL in response"}
                    
                    logger.info(f"Downloading model from {glb_url}")
                    model_response = requests.get(glb_url)
                    
                    if model_response.status_code != 200:
                        return {"success": False, "reason": "Failed to download model"}
                    
                    # Save the downloaded model
                    output_dir = Path("./storage/generated_3d_models")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"meshy_{task_id}.glb"
                    
                    with open(output_path, 'wb') as f:
                        f.write(model_response.content)
                    
                    logger.info(f"AI-generated model saved to {output_path}")
                    
                    return {
                        "success": True,
                        "model_path": str(output_path),
                        "method": "meshy_ai_api",
                        "task_id": task_id,
                        "model_size": len(model_response.content),
                        "thumbnail_url": status_data.get('thumbnail_url'),
                        "texture_urls": status_data.get('texture_urls', [])
                    }
                
                elif status == 'FAILED':
                    error_msg = status_data.get('task_error', {}).get('message', 'Unknown error')
                    logger.error(f"Task failed: {error_msg}")
                    return {"success": False, "reason": f"Generation failed: {error_msg}"}
                
                elif status == 'PENDING' or status == 'IN_PROGRESS':
                    continue  # Keep waiting
                
            # Timeout
            logger.warning(f"Task {task_id} timed out after {max_wait} seconds")
            return {"success": False, "reason": "Generation timed out"}
            
        except Exception as e:
            logger.error(f"AI API error: {str(e)}")
            return {"success": False, "reason": str(e)}


# Singleton instance
_advanced_generator = None


def get_advanced_3d_generator() -> Advanced3DGenerator:
    """Get or create advanced 3D generator instance."""
    global _advanced_generator
    if _advanced_generator is None:
        _advanced_generator = Advanced3DGenerator()
    return _advanced_generator
