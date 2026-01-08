"""
Interior Customization API
Allows users to edit 360° tour images in real-time
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from pathlib import Path
import numpy as np
import hashlib
import time
import httpx
import shutil

from app.services.segmentation_service import SegmentationService
from app.services.interior_inpainting_service import InteriorInpaintingService
from app.dependencies.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interior", tags=["interior-customization"])


class ObjectDetectionRequest(BaseModel):
    """Request to detect object in image"""
    image_id: int = Field(..., description="360° tour image ID")
    image_url: str = Field(..., description="URL of the 360° tour image")
    click_x: int = Field(..., description="X coordinate of click")
    click_y: int = Field(..., description="Y coordinate of click")


class ObjectDetectionResponse(BaseModel):
    """Response with detected object information"""
    object_type: str
    description: str
    style: str
    color: str
    material: str
    bbox: List[int]
    mask_id: str


class FurnitureReplacementRequest(BaseModel):
    """Request to replace furniture with AI-generated alternative"""
    image_id: int = Field(..., description="360° tour image ID")
    image_url: str = Field(..., description="URL of the 360° tour image")
    mask_id: str = Field(..., description="Mask ID from detection")
    replacement_prompt: str = Field(
        ..., 
        description="Description of new furniture",
        examples=["brown leather sofa", "glass coffee table with gold legs"]
    )


class WallColorChangeRequest(BaseModel):
    """Request to change wall color"""
    image_id: int = Field(..., description="360° tour image ID")
    new_color: str = Field(
        ..., 
        description="New wall color",
        examples=["white", "beige", "light gray", "blue"]
    )


class FurniturePreset(BaseModel):
    """Predefined furniture option"""
    id: int
    name: str
    prompt: str
    category: str


class ColorPreset(BaseModel):
    """Predefined color option"""
    id: int
    name: str
    color: str
    hex_code: str


@router.post("/detect-object", response_model=ObjectDetectionResponse)
async def detect_object_in_tour(
    request: ObjectDetectionRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Detect and identify an object in 360° tour image.
    User clicks on furniture, system identifies what it is.
    """
    try:
        # Download the tour image from URL
        temp_dir = Path("storage/temp/tour_images")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        image_filename = f"tour_{request.image_id}_{int(time.time())}.png"
        image_path = temp_dir / image_filename
        
        # Download image from URL
        logger.info(f"Downloading tour image from {request.image_url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(request.image_url)
            response.raise_for_status()
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
        
        logger.info(f"Detecting object at ({request.click_x}, {request.click_y}) in {image_path}")
        
        # Initialize services
        segmentation_service = SegmentationService()
        
        # Detect object at click point
        seg_result = segmentation_service.detect_objects_in_image(
            str(image_path),
            click_point=(request.click_x, request.click_y)
        )
        
        # Identify what the object is using GPT-4 Vision
        object_info = segmentation_service.identify_object_type(
            str(image_path),
            seg_result['bbox']
        )
        
        # Generate unique mask ID
        mask_id = f"mask_{request.image_id}_{request.click_x}_{request.click_y}_{int(time.time())}"
        
        # Save mask for later use
        mask_dir = Path("storage/temp/masks")
        mask_dir.mkdir(parents=True, exist_ok=True)
        mask_path = mask_dir / f"{mask_id}.npy"
        np.save(str(mask_path), seg_result['mask'])
        
        logger.info(f"Detected {object_info['object_type']}: {object_info['description']}")
        
        return ObjectDetectionResponse(
            object_type=object_info['object_type'],
            description=object_info['description'],
            style=object_info['style'],
            color=object_info['color'],
            material=object_info['material'],
            bbox=seg_result['bbox'],
            mask_id=mask_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Object detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")


@router.post("/replace-furniture")
async def replace_furniture_in_tour(
    request: FurnitureReplacementRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Replace detected furniture with AI-generated alternative.
    Uses Stable Diffusion XL for realistic inpainting.
    """
    try:
        # Download the tour image from URL
        temp_dir = Path("storage/temp/tour_images")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        image_filename = f"tour_{request.image_id}_{int(time.time())}.png"
        image_path = temp_dir / image_filename
        
        # Download image from URL
        logger.info(f"Downloading tour image from {request.image_url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(request.image_url)
            response.raise_for_status()
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
        
        # Load saved mask
        mask_path = Path(f"storage/temp/masks/{request.mask_id}.npy")
        if not mask_path.exists():
            raise HTTPException(
                status_code=404, 
                detail="Mask not found. Please detect object first using /detect-object endpoint."
            )
        
        mask_array = np.load(str(mask_path))
        
        # Get original object info (re-identify for context)
        segmentation_service = SegmentationService()
        
        # Find bbox from mask
        coords = np.column_stack(np.where(mask_array > 0))
        if len(coords) == 0:
            raise HTTPException(status_code=400, detail="Invalid mask - no object detected")
        
        y1, x1 = coords.min(axis=0)
        y2, x2 = coords.max(axis=0)
        bbox = [int(x1), int(y1), int(x2), int(y2)]
        
        object_info = segmentation_service.identify_object_type(
            str(image_path),
            bbox
        )
        
        # Extract only serializable string values from object_info
        clean_object_info = {
            'object_type': str(object_info.get('object_type', 'object')),
            'description': str(object_info.get('description', '')),
            'style': str(object_info.get('style', '')),
            'color': str(object_info.get('color', '')),
            'material': str(object_info.get('material', ''))
        }
        
        # Perform AI inpainting
        inpainting_service = InteriorInpaintingService()
        
        # Create output directory
        customized_dir = Path(f"storage/tours/{request.image_id}/customized")
        customized_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        filename_hash = hashlib.md5(
            f"{request.mask_id}_{request.replacement_prompt}".encode()
        ).hexdigest()[:8]
        output_path = customized_dir / f"custom_{filename_hash}.png"
        
        logger.info(f"Replacing {clean_object_info['object_type']} with: {request.replacement_prompt}")
        
        result = inpainting_service.replace_furniture(
            original_image_path=str(image_path),
            mask_array=mask_array,
            replacement_prompt=request.replacement_prompt,
            original_object_info=clean_object_info,
            output_path=str(output_path)
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=500, 
                detail=result.get('error', 'Furniture replacement failed')
            )
        
        logger.info(f"Furniture replaced successfully: {output_path}")
        
        # Use the Replicate URL directly instead of local path
        customized_url = str(result.get('preview_url', ''))
        
        return {
            'success': True,
            'customized_image_url': customized_url,
            'original_object': clean_object_info['object_type'],
            'replacement': str(request.replacement_prompt)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Furniture replacement error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Furniture replacement failed: {str(e)}")


@router.post("/change-wall-color")
async def change_wall_color_in_tour(
    request: WallColorChangeRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Change wall color in 360° tour.
    Note: This is a simplified version. For best results, user should first
    detect walls using the /detect-object endpoint.
    """
    try:
        # Get image path
        image_path = Path(f"storage/tours/{request.image_id}/front.png")
        
        if not image_path.exists():
            tour_dir = Path(f"storage/tours/{request.image_id}")
            if tour_dir.exists():
                image_files = list(tour_dir.glob("*.png")) + list(tour_dir.glob("*.jpg"))
                if image_files:
                    image_path = image_files[0]
                else:
                    raise HTTPException(status_code=404, detail="Image not found")
            else:
                raise HTTPException(status_code=404, detail="Tour directory not found")
        
        # For simplicity, create a mask for upper half of image (usually walls)
        from PIL import Image
        img = Image.open(image_path)
        w, h = img.size
        
        # Simple wall mask (upper 60% of image)
        wall_mask = np.zeros((h, w), dtype=bool)
        wall_mask[:int(h * 0.6), :] = True
        
        # Perform color change
        inpainting_service = InteriorInpaintingService()
        
        customized_dir = Path(f"storage/tours/{request.image_id}/customized")
        customized_dir.mkdir(parents=True, exist_ok=True)
        
        filename_hash = hashlib.md5(
            f"walls_{request.new_color}_{int(time.time())}".encode()
        ).hexdigest()[:8]
        output_path = customized_dir / f"walls_{filename_hash}.png"
        
        result = inpainting_service.change_wall_color(
            original_image_path=str(image_path),
            new_color=request.new_color,
            wall_mask=wall_mask,
            output_path=str(output_path)
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Wall color change failed'))
        
        customized_url = f"/api/v1/storage/tours/{request.image_id}/customized/walls_{filename_hash}.png"
        
        return {
            'success': True,
            'customized_image_url': customized_url,
            'new_color': request.new_color
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wall color change error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Wall color change failed: {str(e)}")


@router.get("/customization-presets")
async def get_customization_presets():
    """
    Get predefined furniture and color options for quick customization.
    No authentication required - public presets.
    """
    return {
        'furniture': {
            'sofas': [
                {'id': 1, 'name': 'Modern Gray Sectional', 'prompt': 'modern gray fabric sectional sofa', 'category': 'sofa'},
                {'id': 2, 'name': 'Brown Leather Sofa', 'prompt': 'brown leather 3-seater sofa with chrome legs', 'category': 'sofa'},
                {'id': 3, 'name': 'White Minimalist Sofa', 'prompt': 'white minimalist linen sofa, scandinavian style', 'category': 'sofa'},
                {'id': 4, 'name': 'Blue Velvet Sofa', 'prompt': 'blue velvet tufted sofa, contemporary design', 'category': 'sofa'},
                {'id': 5, 'name': 'Beige Fabric Loveseat', 'prompt': 'beige fabric loveseat, traditional style', 'category': 'sofa'},
            ],
            'chairs': [
                {'id': 1, 'name': 'Eames Lounge Chair', 'prompt': 'eames style brown leather lounge chair with ottoman', 'category': 'chair'},
                {'id': 2, 'name': 'Scandinavian Armchair', 'prompt': 'scandinavian oak wood armchair with gray cushion', 'category': 'chair'},
                {'id': 3, 'name': 'Modern Accent Chair', 'prompt': 'modern accent chair, yellow fabric, metal legs', 'category': 'chair'},
                {'id': 4, 'name': 'Recliner Chair', 'prompt': 'leather recliner chair, brown color, contemporary', 'category': 'chair'},
            ],
            'tables': [
                {'id': 1, 'name': 'Glass Coffee Table', 'prompt': 'modern glass coffee table with gold metal legs', 'category': 'table'},
                {'id': 2, 'name': 'Wooden Dining Table', 'prompt': 'oak wood dining table, rectangular, seats 6', 'category': 'table'},
                {'id': 3, 'name': 'Marble Side Table', 'prompt': 'white marble side table with brass base', 'category': 'table'},
                {'id': 4, 'name': 'Industrial Coffee Table', 'prompt': 'industrial style coffee table, wood and metal', 'category': 'table'},
            ],
            'beds': [
                {'id': 1, 'name': 'King Platform Bed', 'prompt': 'king size platform bed, white upholstered headboard', 'category': 'bed'},
                {'id': 2, 'name': 'Modern Wooden Bed', 'prompt': 'modern walnut wood bed frame, minimalist design', 'category': 'bed'},
                {'id': 3, 'name': 'Tufted Bed', 'prompt': 'queen size tufted bed, gray velvet, button tufted', 'category': 'bed'},
            ],
            'lamps': [
                {'id': 1, 'name': 'Modern Floor Lamp', 'prompt': 'modern arc floor lamp, black metal, white shade', 'category': 'lamp'},
                {'id': 2, 'name': 'Table Lamp', 'prompt': 'contemporary table lamp, ceramic base, linen shade', 'category': 'lamp'},
                {'id': 3, 'name': 'Industrial Pendant', 'prompt': 'industrial pendant light, black metal cage', 'category': 'lamp'},
            ],
            'decorations': [
                {'id': 1, 'name': 'Modern Art', 'prompt': 'modern abstract art painting on wall, colorful', 'category': 'decoration'},
                {'id': 2, 'name': 'Indoor Plant', 'prompt': 'large indoor plant in modern pot, monstera or fiddle leaf fig', 'category': 'decoration'},
                {'id': 3, 'name': 'Decorative Mirror', 'prompt': 'round decorative mirror, gold frame, on wall', 'category': 'decoration'},
            ]
        },
        'wall_colors': [
            {'id': 1, 'name': 'Pure White', 'color': 'white', 'hex_code': '#FFFFFF'},
            {'id': 2, 'name': 'Warm Beige', 'color': 'beige', 'hex_code': '#F5F5DC'},
            {'id': 3, 'name': 'Light Gray', 'color': 'light gray', 'hex_code': '#D3D3D3'},
            {'id': 4, 'name': 'Soft Blue', 'color': 'light blue', 'hex_code': '#ADD8E6'},
            {'id': 5, 'name': 'Sage Green', 'color': 'green', 'hex_code': '#90EE90'},
            {'id': 6, 'name': 'Pale Yellow', 'color': 'yellow', 'hex_code': '#FFFFE0'},
            {'id': 7, 'name': 'Blush Pink', 'color': 'pink', 'hex_code': '#FFC0CB'},
            {'id': 8, 'name': 'Cream', 'color': 'cream', 'hex_code': '#FFFDD0'},
        ],
        'flooring': [
            {'id': 1, 'name': 'Oak Hardwood', 'prompt': 'natural oak hardwood flooring, matte finish'},
            {'id': 2, 'name': 'White Marble', 'prompt': 'white marble flooring with gray veins, polished'},
            {'id': 3, 'name': 'Gray Carpet', 'prompt': 'plush gray carpet, soft texture'},
            {'id': 4, 'name': 'Dark Walnut', 'prompt': 'dark walnut hardwood flooring, glossy finish'},
        ]
    }


@router.delete("/cleanup-temp/{mask_id}")
async def cleanup_temporary_files(
    mask_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clean up temporary mask files after customization is complete.
    """
    try:
        mask_path = Path(f"storage/temp/masks/{mask_id}.npy")
        if mask_path.exists():
            mask_path.unlink()
            logger.info(f"Cleaned up temporary mask: {mask_id}")
            return {'success': True, 'message': 'Temporary files cleaned up'}
        else:
            return {'success': False, 'message': 'Mask file not found'}
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
