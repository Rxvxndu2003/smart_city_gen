"""
Image Segmentation Service using Segment Anything Model (SAM)
Detects objects in 360° tour images for editing
"""
import os
import numpy as np
from PIL import Image
import requests
import logging
from typing import List, Dict, Any, Tuple, Optional
import cv2
import base64
import io
import json

logger = logging.getLogger(__name__)


class SegmentationService:
    """Service for detecting and segmenting objects in images"""
    
    def __init__(self):
        # Using Replicate API for SAM (no local model needed)
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        # Segment Anything Model
        self.sam_model = "zsxkib/segment-anything:c02c502a10a8fb0b6e46b8621c6bdb2f1ca2f7e064ba41db97df7d1d0f2e3bf3"
    
    def detect_objects_in_image(
        self, 
        image_path: str,
        click_point: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Detect and segment objects in the image.
        
        Args:
            image_path: Path to 360° tour image
            click_point: (x, y) coordinates where user clicked
            
        Returns:
            {
                'mask': binary mask of detected object,
                'bbox': bounding box [x1, y1, x2, y2],
                'confidence': detection confidence,
                'mask_url': URL to mask image
            }
        """
        try:
            import replicate
            
            if not self.replicate_token:
                logger.warning("No Replicate API token found, using fallback method")
                return self._fallback_object_detection(image_path, click_point)
            
            # Load and encode image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Convert to base64 for API
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            image_uri = f"data:image/png;base64,{image_b64}"
            
            logger.info(f"Running SAM with click point: {click_point}")
            
            # Run SAM with point prompt
            output = replicate.run(
                self.sam_model,
                input={
                    "image": image_uri,
                    "point_coords": f"[{click_point[0]}, {click_point[1]}]" if click_point else None,
                    "point_labels": "[1]",  # Foreground point
                    "multimask_output": False
                }
            )
            
            # Process mask
            if isinstance(output, dict) and 'masks' in output:
                mask_url = output['masks'][0]
            elif isinstance(output, list):
                mask_url = output[0]
            else:
                mask_url = str(output)
            
            # Download mask
            mask_response = requests.get(mask_url)
            mask_image = Image.open(io.BytesIO(mask_response.content))
            mask_array = np.array(mask_image.convert('L')) > 128  # Binary mask
            
            # Find bounding box
            coords = np.column_stack(np.where(mask_array > 0))
            if len(coords) == 0:
                raise ValueError("No object detected at click point")
            
            y1, x1 = coords.min(axis=0)
            y2, x2 = coords.max(axis=0)
            
            logger.info(f"Object detected with bbox: [{x1}, {y1}, {x2}, {y2}]")
            
            return {
                'mask': mask_array,
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': 0.95,
                'mask_url': mask_url
            }
            
        except Exception as e:
            logger.error(f"Segmentation error: {e}")
            # Fallback to simple region detection
            return self._fallback_object_detection(image_path, click_point)
    
    def _fallback_object_detection(
        self, 
        image_path: str, 
        click_point: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Fallback object detection using OpenCV when SAM is not available.
        Creates a rectangular region around the click point.
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            h, w = img.shape[:2]
            
            if click_point:
                # Create region around click point
                x, y = click_point
                region_size = 200  # pixels
                x1 = max(0, x - region_size // 2)
                y1 = max(0, y - region_size // 2)
                x2 = min(w, x + region_size // 2)
                y2 = min(h, y + region_size // 2)
                
                # Create mask
                mask = np.zeros((h, w), dtype=bool)
                mask[y1:y2, x1:x2] = True
                
                return {
                    'mask': mask,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': 0.7,
                    'mask_url': None
                }
            else:
                # Default to center region
                x1, y1 = w // 4, h // 4
                x2, y2 = 3 * w // 4, 3 * h // 4
                mask = np.zeros((h, w), dtype=bool)
                mask[y1:y2, x1:x2] = True
                
                return {
                    'mask': mask,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': 0.5,
                    'mask_url': None
                }
                
        except Exception as e:
            logger.error(f"Fallback detection error: {e}")
            raise
    
    def identify_object_type(
        self, 
        image_path: str, 
        bbox: List[int]
    ) -> Dict[str, Any]:
        """
        Use GPT-4 Vision to identify what the object is.
        
        Args:
            image_path: Original image path
            bbox: Bounding box [x1, y1, x2, y2]
            
        Returns:
            {
                'object_type': 'sofa' | 'chair' | 'table' | 'bed' | etc.,
                'description': 'gray fabric sectional sofa',
                'style': 'modern',
                'color': 'gray',
                'material': 'fabric'
            }
        """
        try:
            from openai import OpenAI
            from app.config import settings
            
            openai_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
            
            if not openai_key:
                logger.warning("No OpenAI API key found, using fallback identification")
                return self._fallback_object_identification()
            
            client = OpenAI(api_key=openai_key)
            
            # Load and crop image to bounding box
            img = Image.open(image_path)
            x1, y1, x2, y2 = bbox
            
            # Ensure coordinates are within image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img.width, x2), min(img.height, y2)
            
            cropped = img.crop((x1, y1, x2, y2))
            
            # Convert to base64
            buffered = io.BytesIO()
            cropped.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # GPT-4 Vision analysis
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this furniture/interior item. Return ONLY valid JSON with no additional text:
{
  "object_type": "sofa|chair|table|bed|cabinet|lamp|curtain|rug|plant|painting|desk|shelf|decoration",
  "description": "detailed description of the item",
  "style": "modern|traditional|minimalist|industrial|scandinavian|contemporary|rustic|bohemian",
  "color": "primary color of the item",
  "material": "fabric|leather|wood|metal|glass|plastic|ceramic|stone"
}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }],
                max_tokens=300,
                temperature=0.3
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            result = json.loads(content.strip())
            logger.info(f"Identified object: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Object identification error: {e}")
            return self._fallback_object_identification()
    
    def _fallback_object_identification(self) -> Dict[str, Any]:
        """Fallback when GPT-4 Vision is not available"""
        return {
            'object_type': 'furniture',
            'description': 'furniture item',
            'style': 'modern',
            'color': 'neutral',
            'material': 'unknown'
        }
