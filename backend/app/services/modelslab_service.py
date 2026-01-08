"""
ModelsLab API Service for 3D Floor Plan Generation

This service integrates with ModelsLab's API to generate:
- 3D GLB models from 2D floor plans
- 360° virtual tour panoramas
- Additional 2D renders with various styles
"""

import requests
import time
import base64
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class ModelsLabService:
    """Service for ModelsLab API integration"""
    
    def __init__(self):
        self.api_key = settings.MODELSLAB_API_KEY
        self.base_url = "https://modelslab.com/api/v6"
        self.max_poll_attempts = 60  # 2 minutes max wait time
        
        if self.api_key:
            logger.info(f"ModelsLab service initialized with API key (length: {len(self.api_key)})")
        
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Convert local image to base64 data URI"""
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
    
    def generate_3d_floor_plan(
        self, 
        floor_plan_path: str, 
        prompt: str = "modern interior design, photorealistic, professional architecture",
        include_360: bool = True
    ) -> Dict[str, Any]:
        """
        Generate 3D model from 2D floor plan using ModelsLab API
        
        Args:
            floor_plan_path: Path to the floor plan image
            prompt: Description of desired output
            include_360: Whether to generate 360° panoramic view
            
        Returns:
            {
                "success": bool,
                "model_url": str,  # GLB file URL
                "tour_360_url": str,  # 360° panorama URL (if requested)
                "render_images": List[str],  # Additional 2D renders
                "generation_time": float
            }
        """
        if not self.api_key:
            logger.warning("ModelsLab API key not configured, skipping 3D generation")
            return {
                "success": False,
                "reason": "ModelsLab API key not configured. Set MODELSLAB_API_KEY in .env"
            }
        
        try:
            start_time = time.time()
            
            # Upload floor plan to Cloudinary for public URL access
            import cloudinary
            import cloudinary.uploader
            from app.config import settings
            
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
            
            # Upload image to Cloudinary
            logger.info("Uploading floor plan to Cloudinary...")
            from pathlib import Path
            filename = Path(floor_plan_path).name
            
            upload_result = cloudinary.uploader.upload(
                floor_plan_path,
                folder="floor_plans",
                public_id=Path(floor_plan_path).stem,
                resource_type="image",
                overwrite=True
            )
            
            image_url = upload_result['secure_url']
            logger.info(f"✅ Cloudinary upload successful: {image_url}")
            
            # Generate 3D GLB model using Blender
            logger.info("Generating 3D GLB model with Blender...")
            
            try:
                from app.services.blender_house_service import BlenderHouseService
                blender_service = BlenderHouseService()
                
                # Extract dimensions from floor plan image or use defaults
                house_params = {
                    "width": 12.0,
                    "depth": 10.0,
                    "floor_count": 2,
                    "floor_height": 3.0,
                    "style": "modern"
                }
                
                # Generate 3D model with Blender
                blender_result = blender_service.generate_house_from_params(**house_params)
                
                if blender_result.get("success"):
                    logger.info(f"✅ 3D GLB generation complete!")
                    logger.info(f"   Model URL: {blender_result.get('model_url')}")
                    logger.info(f"   Model Size: {blender_result.get('model_size', 0)} bytes")
                    generation_time = time.time() - start_time
                    
                    return {
                        "success": True,
                        "model_url": blender_result.get("model_url"),
                        "tour_360_url": None,
                        "generation_time": generation_time,
                        "meta": {
                            "provider": "Blender (Procedural)",
                            "type": "3D GLB Mesh",
                            "model_size": blender_result.get("model_size", 0),
                            "parameters": house_params
                        }
                    }
                else:
                    logger.warning(f"Blender 3D generation failed: {blender_result.get('reason')}")
                    return {
                        "success": False,
                        "reason": f"3D generation failed: {blender_result.get('reason')}",
                        "note": "Make sure Blender is installed"
                    }
                
            except Exception as triposr_error:
                logger.error(f"TripoSR failed: {triposr_error}")
                return {
                    "success": False,
                    "reason": f"3D generation failed: {str(triposr_error)}",
                    "note": "Continuing with 2D renders"
                }
            
            # Prepare API request
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "key": self.api_key,
                "prompt": prompt,
                "init_image": image_url,
                "negative_prompt": "low quality, distorted, blurry, unrealistic, cartoon",
                "strength": 0.7,
                "num_inference_steps": 31,
                "guidance_scale": 7.5,
                "webhook": None,
                "track_id": None
            }
            
            # Submit generation request
            logger.info("Submitting 3D floor plan generation to ModelsLab...")
            response = requests.post(
                f"{self.base_url}/interior/floor_planning",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"ModelsLab API error: {response.text}")
                return {
                    "success": False,
                    "reason": f"API request failed: {response.status_code}"
                }
            
            result = response.json()
            logger.info(f"ModelsLab response: {result}")
            
            # Check if generation is async (status: processing)
            if result.get("status") == "processing":
                fetch_url = result.get("fetch_result")
                eta = result.get("eta", 45)
                
                if fetch_url:
                    logger.info(f"Generation queued. Polling {fetch_url} after {eta}s...")
                    time.sleep(eta + 5)  # Wait ETA + 5s buffer
                    
                    # Poll the fetch endpoint
                    for attempt in range(self.max_poll_attempts):
                        try:
                            fetch_response = requests.post(
                                fetch_url,
                                headers=headers,
                                json={"key": self.api_key},
                                timeout=30
                            )
                            
                            if fetch_response.status_code == 200:
                                fetch_result = fetch_response.json()
                                logger.info(f"Fetch attempt {attempt + 1}: {fetch_result.get('status')}")
                                
                                if fetch_result.get("status") == "success":
                                    result = fetch_result  # Use fetched result
                                    logger.info("✅ 3D generation complete!")
                                    break
                                elif fetch_result.get("status") == "error":
                                    logger.error(f"Generation failed: {fetch_result.get('message')}")
                                    return {
                                        "success": False,
                                        "reason": fetch_result.get("message", "Unknown error")
                                    }
                            
                            # Wait before retry
                            time.sleep(5)
                            
                        except Exception as e:
                            logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
                            time.sleep(5)
            
            # Check if generation was successful
            if result.get("status") == "error":
                return {
                    "success": False,
                    "reason": result.get("message", "Unknown error")
                }
            
            # Extract output URLs
            output = result.get("output", [])
            if isinstance(output, str):
                output = [output]
            
            generation_time = time.time() - start_time
            
            return {
                "success": True,
                "model_url": output[0] if len(output) > 0 else None,  # Primary 3D model
                "tour_360_url": output[1] if len(output) > 1 and include_360 else None,
                "render_images": output[2:] if len(output) > 2 else [],
                "generation_time": generation_time,
                "meta": result.get("meta", {})
            }
            
        except requests.exceptions.Timeout:
            logger.error("ModelsLab API request timed out")
            return {
                "success": False,
                "reason": "API request timed out after 30 seconds"
            }
        except Exception as e:
            logger.error(f"ModelsLab generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "reason": str(e)
            }
    
    def generate_360_tour(
        self, 
        floor_plan_path: str, 
        rooms: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate 360° panoramic views for each detected room
        
        Args:
            floor_plan_path: Path to floor plan image
            rooms: List of detected rooms from Vision AI
            
        Returns:
            {
                "success": bool,
                "panoramas": [
                    {
                        "room_type": str,
                        "panorama_url": str
                    }
                ]
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "reason": "ModelsLab API key not configured"
            }
        
        try:
            panoramas = []
            
            for room in rooms[:5]:  # Limit to 5 rooms to control costs
                room_type = room.get("type", "Room")
                
                # Generate 360° panorama for this room
                prompt = f"360 degree panoramic view of a {room_type}, photorealistic, modern interior, wide angle"
                
                result = self.generate_3d_floor_plan(
                    floor_plan_path,
                    prompt=prompt,
                    include_360=True
                )
                
                if result.get("success") and result.get("tour_360_url"):
                    panoramas.append({
                        "room_type": room_type,
                        "panorama_url": result["tour_360_url"]
                    })
                
                # Rate limiting: wait 2 seconds between requests
                time.sleep(2)
            
            return {
                "success": True,
                "panoramas": panoramas,
                "total_generated": len(panoramas)
            }
            
        except Exception as e:
            logger.error(f"360° tour generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "reason": str(e)
            }
