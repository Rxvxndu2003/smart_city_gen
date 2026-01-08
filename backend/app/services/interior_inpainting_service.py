"""
AI-Powered Interior Design Inpainting Service
Allows users to replace furniture and change interior elements
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import requests
from PIL import Image
import io
import numpy as np
import base64

logger = logging.getLogger(__name__)


class InteriorInpaintingService:
    """Service for AI-powered furniture replacement and interior design"""
    
    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        # Using Stable Diffusion XL Inpainting
        self.inpainting_model = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    
    def replace_furniture(
        self,
        original_image_path: str,
        mask_array: np.ndarray,
        replacement_prompt: str,
        original_object_info: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Replace furniture in the image using AI inpainting.
        
        Args:
            original_image_path: Path to original 360° image
            mask_array: Binary mask of object to replace
            replacement_prompt: Description of new furniture
            original_object_info: Info about original object (for context)
            output_path: Where to save result
            
        Returns:
            {
                'success': bool,
                'output_path': str,
                'preview_url': str
            }
        """
        try:
            if not self.replicate_token:
                logger.warning("No Replicate API token, using simple replacement")
                return self._simple_replacement(
                    original_image_path, 
                    mask_array, 
                    output_path
                )
            
            import replicate
            
            # Load original image
            original_img = Image.open(original_image_path)
            logger.info(f"Loaded image: {original_img.size}")
            
            # Create mask image (white = replace, black = keep)
            mask_img = Image.fromarray((mask_array * 255).astype('uint8'))
            
            # Resize to optimal size for SDXL (1024x1024 or maintain aspect ratio)
            max_size = 1024
            original_size = original_img.size
            
            # Calculate resize maintaining aspect ratio
            ratio = min(max_size / original_size[0], max_size / original_size[1])
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            
            original_resized = original_img.resize(new_size, Image.LANCZOS)
            mask_resized = mask_img.resize(new_size, Image.NEAREST)
            
            # Save temporary files
            temp_dir = Path(output_path).parent
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            temp_original = temp_dir / "temp_original.png"
            temp_mask = temp_dir / "temp_mask.png"
            
            original_resized.save(temp_original)
            mask_resized.save(temp_mask)
            
            # Build enhanced prompt
            enhanced_prompt = self._build_inpainting_prompt(
                replacement_prompt, 
                original_object_info
            )
            
            logger.info(f"Inpainting with prompt: {enhanced_prompt}")
            
            # Run SDXL Inpainting
            with open(temp_original, "rb") as img_file, \
                 open(temp_mask, "rb") as mask_file:
                
                # Convert to base64 data URIs
                img_b64 = base64.b64encode(img_file.read()).decode()
                mask_b64 = base64.b64encode(mask_file.read()).decode()
                
                output = replicate.run(
                    self.inpainting_model,
                    input={
                        "image": f"data:image/png;base64,{img_b64}",
                        "mask": f"data:image/png;base64,{mask_b64}",
                        "prompt": enhanced_prompt,
                        "negative_prompt": "low quality, blurry, distorted, unrealistic, bad furniture, deformed, ugly, inconsistent lighting, mismatched perspective, watermark, text",
                        "num_inference_steps": 30,
                        "guidance_scale": 7.5,
                        "strength": 0.99,
                        "num_outputs": 1
                    }
                )
            
            # Download result
            if isinstance(output, list):
                result_url = output[0]
            else:
                result_url = str(output)
            
            logger.info(f"Inpainting result URL: {result_url}")
            
            result_response = requests.get(result_url, timeout=30)
            result_response.raise_for_status()
            result_img = Image.open(io.BytesIO(result_response.content))
            
            # Resize back to original size
            final_img = result_img.resize(original_size, Image.LANCZOS)
            final_img.save(output_path)
            
            # Cleanup temporary files
            temp_original.unlink(missing_ok=True)
            temp_mask.unlink(missing_ok=True)
            
            logger.info(f"Inpainting successful: {output_path}")
            
            return {
                'success': True,
                'output_path': str(output_path),
                'preview_url': result_url
            }
            
        except Exception as e:
            logger.error(f"Inpainting error: {e}", exc_info=True)
            # Fallback to simple replacement
            return self._simple_replacement(
                original_image_path,
                mask_array,
                output_path
            )
    
    def _build_inpainting_prompt(
        self, 
        replacement_prompt: str, 
        original_object_info: Dict[str, Any]
    ) -> str:
        """
        Build an enhanced prompt for better inpainting results.
        """
        # Extract context from original object
        style = original_object_info.get('style', 'modern')
        
        # Build comprehensive prompt
        prompt = f"{replacement_prompt}, {style} interior design, "
        prompt += "photorealistic, 8k, professional interior photography, "
        prompt += "natural lighting, sharp details, consistent perspective, "
        prompt += "high quality furniture, realistic materials, "
        prompt += "matching room aesthetics, seamless integration"
        
        return prompt
    
    def _simple_replacement(
        self,
        original_image_path: str,
        mask_array: np.ndarray,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Simple replacement when AI is not available.
        Just blurs the masked region as a placeholder.
        """
        try:
            import cv2
            
            # Load image
            img = cv2.imread(original_image_path)
            if img is None:
                raise ValueError("Could not load image")
            
            # Apply blur to masked region
            blurred = cv2.GaussianBlur(img, (51, 51), 0)
            
            # Create 3-channel mask
            mask_3d = np.stack([mask_array] * 3, axis=-1)
            
            # Blend blurred region
            result = np.where(mask_3d, blurred, img)
            
            # Save
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(output_path, result)
            
            logger.info(f"Simple replacement saved: {output_path}")
            
            return {
                'success': True,
                'output_path': str(output_path),
                'preview_url': None,
                'note': 'AI inpainting not available, applied simple blur'
            }
            
        except Exception as e:
            logger.error(f"Simple replacement error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def change_wall_color(
        self,
        original_image_path: str,
        new_color: str,
        wall_mask: np.ndarray,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Change wall color while preserving texture and lighting.
        """
        try:
            import cv2
            
            # Load image
            img = cv2.imread(original_image_path)
            if img is None:
                raise ValueError("Could not load image")
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Color mapping
            color_map = {
                'white': (255, 255, 255),
                'beige': (245, 245, 220),
                'gray': (180, 180, 180),
                'light gray': (211, 211, 211),
                'blue': (173, 216, 230),
                'light blue': (173, 216, 230),
                'green': (144, 238, 144),
                'yellow': (255, 255, 224),
                'pink': (255, 192, 203),
                'cream': (255, 253, 208)
            }
            
            target_color = np.array(color_map.get(new_color.lower(), (255, 255, 255)))
            
            # Create colored version
            colored = img_rgb.copy()
            mask_3d = np.stack([wall_mask] * 3, axis=-1)
            
            # Apply color with blending to preserve shadows/highlights
            alpha = 0.6
            colored[wall_mask] = (
                alpha * target_color + 
                (1 - alpha) * img_rgb[wall_mask]
            ).astype('uint8')
            
            # Convert back to BGR
            result_bgr = cv2.cvtColor(colored, cv2.COLOR_RGB2BGR)
            
            # Save
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(output_path, result_bgr)
            
            logger.info(f"Wall color changed: {output_path}")
            
            return {
                'success': True,
                'output_path': str(output_path)
            }
            
        except Exception as e:
            logger.error(f"Wall color change error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
