"""
Replicate Service - AI-powered image enhancement using Replicate API.

This service provides AI enhancement for Blender-generated city renders using
Stable Diffusion and ControlNet models via the Replicate API.
"""
import os
import logging
import replicate
from typing import Optional, List, Dict, Any
from pathlib import Path
import requests
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class ReplicateService:
    """Service for AI-powered image enhancement using Replicate API."""
    
    def __init__(self):
        """Initialize Replicate service with API token."""
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not set. AI enhancement will be disabled.")
        else:
            # Set the API token for replicate client
            os.environ['REPLICATE_API_TOKEN'] = self.api_token
    
    async def enhance_city_render(
        self,
        input_image_path: str,
        prompt: str = "photorealistic city aerial view, detailed buildings, realistic lighting, 8k, professional architecture photography",
        style: str = "photorealistic",
        strength: float = 0.7,
        guidance_scale: float = 7.5
    ) -> Optional[str]:
        """
        Enhance a Blender-generated city render using Stable Diffusion XL.
        
        Args:
            input_image_path: Path to the input Blender render
            prompt: Text prompt describing desired output
            style: Style preset (photorealistic, artistic, etc.)
            strength: How much to transform the image (0.0-1.0)
            guidance_scale: How closely to follow the prompt (1.0-20.0)
            
        Returns:
            Path to enhanced image, or None if enhancement fails
        """
        if not self.api_token:
            logger.warning("Replicate API not configured. Skipping enhancement.")
            return None
        
        try:
            logger.info(f"Enhancing city render: {input_image_path}")
            
            # Use Stable Diffusion XL for image-to-image
            # Model: stability-ai/sdxl
            # Open file as file object (Replicate expects file object, not bytes)
            with open(input_image_path, 'rb') as image_file:
                output = replicate.run(
                    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    input={
                        "image": image_file,
                        "prompt": prompt,
                        "negative_prompt": "blurry, low quality, distorted, unrealistic, cartoon, 3d render artifacts",
                        "num_inference_steps": 30,
                        "guidance_scale": guidance_scale,
                        "strength": strength,
                        "scheduler": "DPMSolverMultistep"
                    }
                )
            
            # Download enhanced image
            if output and len(output) > 0:
                enhanced_url = output[0]
                
                # Download the image
                response = requests.get(enhanced_url)
                if response.status_code == 200:
                    # Save enhanced image
                    output_path = input_image_path.replace('.png', '_enhanced.png')
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"Enhanced image saved to: {output_path}")
                    return output_path
                else:
                    logger.error(f"Failed to download enhanced image: {response.status_code}")
                    return None
            else:
                logger.error("No output from Replicate API")
                return None
                
        except Exception as e:
            logger.error(f"Error enhancing city render: {e}")
            return None
    
    async def enhance_with_controlnet(
        self,
        input_image_path: str,
        prompt: str,
        controlnet_type: str = "canny",
        strength: float = 0.8
    ) -> Optional[str]:
        """
        Enhance image using ControlNet to preserve structure.
        
        Args:
            input_image_path: Path to input image
            prompt: Text prompt
            controlnet_type: Type of ControlNet (canny, depth, etc.)
            strength: Enhancement strength
            
        Returns:
            Path to enhanced image
        """
        if not self.api_token:
            return None
        
        try:
            logger.info(f"Enhancing with ControlNet ({controlnet_type}): {input_image_path}")
            
            with open(input_image_path, 'rb') as f:
                input_image = f.read()
            
            # Use ControlNet model for structure-preserving enhancement
            output = replicate.run(
                "jagilley/controlnet-canny:aff48af9c68d162388d230a2ab003f68d2638d88307bdaf1c2f1ac95079c9613",
                input={
                    "image": input_image,
                    "prompt": prompt,
                    "num_samples": "1",
                    "image_resolution": "512",
                    "ddim_steps": 20,
                    "scale": 9.0,
                    "a_prompt": "best quality, extremely detailed, photorealistic",
                    "n_prompt": "longbody, lowres, bad anatomy, bad hands, missing fingers"
                }
            )
            
            if output and len(output) > 0:
                enhanced_url = output[0]
                response = requests.get(enhanced_url)
                
                if response.status_code == 200:
                    output_path = input_image_path.replace('.png', '_controlnet.png')
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"ControlNet enhanced image saved to: {output_path}")
                    return output_path
                    
            return None
            
        except Exception as e:
            logger.error(f"Error with ControlNet enhancement: {e}")
            return None
    
    async def generate_multiple_views(
        self,
        base_render_paths: List[str],
        prompt: str,
        batch_size: int = 4
    ) -> List[Dict[str, str]]:
        """
        Enhance multiple camera views of the city.
        
        Args:
            base_render_paths: List of paths to base renders
            prompt: Enhancement prompt
            batch_size: Number of images to process in parallel
            
        Returns:
            List of dicts with 'original' and 'enhanced' paths
        """
        results = []
        
        for i, render_path in enumerate(base_render_paths):
            logger.info(f"Processing view {i+1}/{len(base_render_paths)}")
            
            enhanced_path = await self.enhance_city_render(
                input_image_path=render_path,
                prompt=prompt
            )
            
            results.append({
                'original': render_path,
                'enhanced': enhanced_path,
                'view_name': f"view_{i+1}"
            })
        
        return results
    
    def estimate_cost(
        self,
        num_images: int,
        model: str = "sdxl"
    ) -> float:
        """
        Estimate cost for enhancing images.
        
        Args:
            num_images: Number of images to enhance
            model: Model to use (sdxl, controlnet)
            
        Returns:
            Estimated cost in USD
        """
        # Approximate costs (as of 2024)
        costs = {
            'sdxl': 0.0023,  # per image
            'controlnet': 0.0020  # per image
        }
        
        cost_per_image = costs.get(model, 0.0023)
        return num_images * cost_per_image
    
    def is_available(self) -> bool:
        """Check if Replicate service is available."""
        return self.api_token is not None


# Global service instance
replicate_service = ReplicateService()
