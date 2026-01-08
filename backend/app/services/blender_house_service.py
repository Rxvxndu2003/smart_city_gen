"""
Blender House Generation Service
Generates 3D house models using Blender
"""
import subprocess
import json
import os
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BlenderHouseService:
    """Service for generating 3D houses using Blender"""
    
    def __init__(self):
        self.blender_path = self._find_blender()
        # Fix path - go up to backend folder, then to blender_scripts
        backend_dir = Path(__file__).parent.parent.parent
        self.script_path = backend_dir / "blender_scripts" / "generate_house.py"
        self.output_dir = Path("./storage/generated_3d_models")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.blender_path:
            logger.info(f"Blender found at: {self.blender_path}")
            logger.info(f"Script path: {self.script_path}")
            if not self.script_path.exists():
                logger.error(f"Script file not found at: {self.script_path}")
        else:
            logger.warning("Blender not found. Install Blender for 3D generation.")
    
    def _find_blender(self) -> Optional[str]:
        """Find Blender installation."""
        # Common Blender paths
        possible_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",  # macOS
            "/usr/bin/blender",  # Linux
            "/usr/local/bin/blender",  # Linux alternative
            "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",  # Windows
            shutil.which("blender")  # System PATH
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def generate_house_from_params(
        self,
        width: float = 12.0,
        depth: float = 10.0,
        floor_count: int = 2,
        floor_height: float = 3.0,
        rooms: list = None,
        style: str = "modern",
        output_filename: str = None
    ) -> Dict[str, Any]:
        """
        Generate 3D house model using Blender.
        
        Args:
            width: House width in meters
            depth: House depth in meters
            floor_count: Number of floors
            floor_height: Height of each floor in meters
            rooms: List of room dictionaries
            style: Architectural style (modern, traditional, contemporary)
            output_filename: Custom output filename
            
        Returns:
            {
                "success": bool,
                "model_url": str,
                "model_path": str,
                "model_size": int,
                "generation_time": float
            }
        """
        if not self.blender_path:
            return {
                "success": False,
                "reason": "Blender not installed. Please install Blender 3.0 or higher."
            }
        
        if not self.script_path.exists():
            return {
                "success": False,
                "reason": f"Blender script not found: {self.script_path}"
            }
        
        # Prepare parameters
        params = {
            "width": width,
            "depth": depth,
            "floor_count": floor_count,
            "floor_height": floor_height,
            "rooms": rooms or [],
            "style": style
        }
        
        # Generate output filename
        if not output_filename:
            output_filename = f"house_{style}_{floor_count}floor_{int(width)}x{int(depth)}.glb"
        
        output_path = self.output_dir / output_filename
        params["output_path"] = str(output_path.absolute())  # Use absolute path
        
        logger.info(f"Generating house with Blender: {params}")
        
        try:
            import time
            start_time = time.time()
            
            # Run Blender in headless mode
            cmd = [
                self.blender_path,
                "--background",
                "--python", str(self.script_path),
                "--",
                json.dumps(params)
            ]
            
            logger.info(f"Running command: {' '.join(cmd[:4])}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            generation_time = time.time() - start_time
            
            # Log Blender output for debugging
            if result.stdout:
                logger.info(f"Blender stdout: {result.stdout[-1000:]}")  # Last 1000 chars
            if result.stderr:
                logger.warning(f"Blender stderr: {result.stderr[-1000:]}")
            
            # Check for errors
            if result.returncode != 0:
                logger.error(f"Blender failed with return code {result.returncode}")
                return {
                    "success": False,
                    "reason": f"Blender generation failed (exit {result.returncode}): {result.stderr[:500]}"
                }
            
            # Verify file was created
            if not output_path.exists():
                logger.error(f"GLB file was not created at: {output_path}")
                logger.error(f"Expected directory exists: {output_path.parent.exists()}")
                logger.error(f"Files in directory: {list(output_path.parent.glob('*')) if output_path.parent.exists() else 'N/A'}")
                return {
                    "success": False,
                    "reason": f"GLB file was not generated at {output_path}"
                }
            
            file_size = output_path.stat().st_size
            logger.info(f"✅ House generated: {output_path} ({file_size} bytes) in {generation_time:.2f}s")
            
            # Generate web URL
            model_url = f"http://localhost:8000/storage/generated_3d_models/{output_filename}"
            
            return {
                "success": True,
                "model_url": model_url,
                "model_path": str(output_path),
                "model_size": file_size,
                "generation_time": generation_time,
                "method": "blender_procedural",
                "parameters": params
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Blender generation timed out")
            return {
                "success": False,
                "reason": "Generation timed out (>2 minutes)"
            }
        except Exception as e:
            logger.error(f"Blender generation error: {e}")
            return {
                "success": False,
                "reason": f"Generation error: {str(e)}"
            }
    
    def generate_from_floor_plan(self, floor_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate house from extracted floor plan data.
        
        Args:
            floor_plan_data: Dictionary with floor plan information
            
        Returns:
            Generation result dictionary
        """
        # Extract dimensions
        dimensions = floor_plan_data.get('dimensions', {})
        width = dimensions.get('width', 12.0)
        depth = dimensions.get('length', 10.0)
        
        # Floor information
        floor_count = floor_plan_data.get('floor_count', 2)
        total_floor_area = floor_plan_data.get('total_floor_area', width * depth)
        
        # Estimate floor height based on total area and floor count
        floor_height = 3.0  # Standard floor height
        
        # Get rooms
        rooms = floor_plan_data.get('rooms', [])
        
        # Determine style (default to modern)
        style = floor_plan_data.get('style', 'modern')
        
        logger.info(f"Generating house from floor plan: {width}x{depth}m, {floor_count} floors, {len(rooms)} rooms")
        
        return self.generate_house_from_params(
            width=width,
            depth=depth,
            floor_count=floor_count,
            floor_height=floor_height,
            rooms=rooms,
            style=style
        )
    
    def generate_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Generate house from text prompt (basic interpretation).
        
        Args:
            prompt: Text description of the house
            
        Returns:
            Generation result dictionary
        """
        # Simple prompt parsing
        prompt_lower = prompt.lower()
        
        # Determine floor count
        floor_count = 2  # default
        if 'single' in prompt_lower or 'one story' in prompt_lower or '1 floor' in prompt_lower:
            floor_count = 1
        elif 'three' in prompt_lower or '3 floor' in prompt_lower:
            floor_count = 3
        elif 'four' in prompt_lower or '4 floor' in prompt_lower:
            floor_count = 4
        
        # Determine style
        style = 'modern'
        if 'traditional' in prompt_lower or 'classic' in prompt_lower:
            style = 'traditional'
        elif 'contemporary' in prompt_lower:
            style = 'contemporary'
        
        # Estimate size
        width = 12.0
        depth = 10.0
        if 'large' in prompt_lower or 'big' in prompt_lower:
            width = 16.0
            depth = 14.0
        elif 'small' in prompt_lower or 'compact' in prompt_lower:
            width = 8.0
            depth = 7.0
        
        logger.info(f"Interpreted prompt: {floor_count} floors, {style} style, {width}x{depth}m")
        
        return self.generate_house_from_params(
            width=width,
            depth=depth,
            floor_count=floor_count,
            style=style
        )
