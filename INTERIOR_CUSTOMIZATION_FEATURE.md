# Interactive Interior Design Customization for 360° Tours

## 🎨 Feature Overview

Add real-time interior customization capabilities to your 360° virtual tours, allowing users to:
- Change furniture (sofa, chairs, tables, bed, etc.)
- Modify wall colors and materials
- Replace flooring types
- Adjust lighting conditions
- Add/remove decor items
- Change window treatments
- Customize kitchen cabinets
- Modify bathroom fixtures

---

## 🏗️ Implementation Approaches

### Approach 1: AI-Powered Image Inpainting (RECOMMENDED)
**Best for:** Real-time customization with minimal 3D complexity

**Technologies:**
- Stable Diffusion Inpainting
- ControlNet for structure preservation
- Segment Anything Model (SAM) for object detection
- GPT-4 Vision for object recognition

**How it works:**
```
1. User clicks on sofa in 360° image
2. SAM detects sofa boundaries
3. GPT-4 Vision identifies: "This is a gray fabric sofa"
4. User selects: "Replace with brown leather sofa"
5. Stable Diffusion inpaints new sofa while preserving room structure
6. Updated image replaces original in 360° viewer
```

### Approach 2: 3D Scene Editor (Advanced)
**Best for:** Full 3D control and manipulation

**Technologies:**
- Three.js for 3D rendering
- React Three Fiber
- Blender for asset library
- Real-time ray tracing

### Approach 3: Hybrid Approach (OPTIMAL)
**Combines:** AI inpainting for quick edits + 3D for major changes

---

## 📦 Implementation Plan

### Phase 1: AI Image Inpainting (Quick Win - 2-3 weeks)

#### Step 1: Add Segmentation Service

**File: `backend/app/services/segmentation_service.py`**

```python
"""
Image Segmentation Service using Segment Anything Model (SAM)
Detects objects in 360° tour images for editing
"""
import os
import numpy as np
from PIL import Image
import requests
import logging
from typing import List, Dict, Any, Tuple
import cv2

logger = logging.getLogger(__name__)

class SegmentationService:
    def __init__(self):
        # Using Replicate API for SAM (no local model needed)
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.sam_model = "zsxkib/segment-anything:c02c502a10a8fb0b6e46b8621c6bdb2f1ca2f7e064ba41db97df7d1d0f2e3bf3"
    
    def detect_objects_in_image(
        self, 
        image_path: str,
        click_point: Tuple[int, int] = None
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
                'object_type': detected object category
            }
        """
        try:
            import replicate
            
            # Upload image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Run SAM with point prompt
            output = replicate.run(
                self.sam_model,
                input={
                    "image": image_data,
                    "point_coords": f"[{click_point[0]}, {click_point[1]}]" if click_point else None,
                    "point_labels": "[1]",  # Foreground point
                    "multimask_output": False
                }
            )
            
            # Process mask
            mask_url = output['masks'][0]
            mask_response = requests.get(mask_url)
            mask_image = Image.open(mask_response.content)
            mask_array = np.array(mask_image)
            
            # Find bounding box
            coords = np.column_stack(np.where(mask_array > 0))
            y1, x1 = coords.min(axis=0)
            y2, x2 = coords.max(axis=0)
            
            return {
                'mask': mask_array,
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': 0.95,
                'mask_url': mask_url
            }
            
        except Exception as e:
            logger.error(f"Segmentation error: {e}")
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
            import base64
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Crop image to bounding box
            img = Image.open(image_path)
            x1, y1, x2, y2 = bbox
            cropped = img.crop((x1, y1, x2, y2))
            
            # Convert to base64
            import io
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
                            "text": """Analyze this furniture/interior item. Return ONLY valid JSON:
{
  "object_type": "sofa|chair|table|bed|cabinet|lamp|curtain|rug|plant|painting",
  "description": "detailed description",
  "style": "modern|traditional|minimalist|industrial|scandinavian",
  "color": "primary color",
  "material": "fabric|leather|wood|metal|glass"
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
                max_tokens=300
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            logger.info(f"Identified object: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Object identification error: {e}")
            return {
                'object_type': 'unknown',
                'description': 'unidentified item',
                'style': 'unknown',
                'color': 'unknown',
                'material': 'unknown'
            }
```

#### Step 2: Add Inpainting Service

**File: `backend/app/services/interior_inpainting_service.py`**

```python
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

logger = logging.getLogger(__name__)

class InteriorInpaintingService:
    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        # Using Stable Diffusion XL Inpainting
        self.inpainting_model = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        # Using ControlNet for structure preservation
        self.controlnet_model = "jagilley/controlnet-canny:aff48af9c68d162388d230a2ab003f68d2638d88307bdaf1c2f1ac95079c9613"
    
    def replace_furniture(
        self,
        original_image_path: str,
        mask_array: 'np.ndarray',
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
            import replicate
            import numpy as np
            
            # Load original image
            original_img = Image.open(original_image_path)
            
            # Create mask image
            mask_img = Image.fromarray((mask_array * 255).astype('uint8'))
            
            # Resize to optimal size for SDXL (1024x1024 or closest)
            target_size = (1024, 1024)
            original_resized = original_img.resize(target_size, Image.LANCZOS)
            mask_resized = mask_img.resize(target_size, Image.NEAREST)
            
            # Save temporary files
            temp_dir = Path(output_path).parent
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
                
                output = replicate.run(
                    self.inpainting_model,
                    input={
                        "image": img_file,
                        "mask": mask_file,
                        "prompt": enhanced_prompt,
                        "negative_prompt": "low quality, blurry, distorted, unrealistic, bad furniture, deformed, ugly, inconsistent lighting, mismatched perspective",
                        "num_inference_steps": 50,
                        "guidance_scale": 7.5,
                        "strength": 0.99,  # High strength for complete replacement
                        "num_outputs": 1
                    }
                )
            
            # Download result
            result_url = output[0] if isinstance(output, list) else output
            result_response = requests.get(result_url)
            result_img = Image.open(io.BytesIO(result_response.content))
            
            # Resize back to original size
            final_img = result_img.resize(original_img.size, Image.LANCZOS)
            final_img.save(output_path)
            
            # Cleanup
            temp_original.unlink()
            temp_mask.unlink()
            
            logger.info(f"Inpainting successful: {output_path}")
            
            return {
                'success': True,
                'output_path': str(output_path),
                'preview_url': result_url
            }
            
        except Exception as e:
            logger.error(f"Inpainting error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
        
        # Build prompt
        prompt = f"{replacement_prompt}, {style} interior design, "
        prompt += "photorealistic, 8k, professional interior photography, "
        prompt += "natural lighting, sharp details, consistent perspective, "
        prompt += "high quality furniture, realistic materials, "
        prompt += "matching room aesthetics"
        
        return prompt
    
    def change_wall_color(
        self,
        original_image_path: str,
        new_color: str,
        wall_mask: 'np.ndarray',
        output_path: str
    ) -> Dict[str, Any]:
        """
        Change wall color while preserving texture and lighting.
        """
        try:
            from PIL import ImageEnhance
            import numpy as np
            
            # Load original
            img = Image.open(original_image_path)
            img_array = np.array(img)
            
            # Convert color name to RGB
            color_map = {
                'white': (255, 255, 255),
                'beige': (245, 245, 220),
                'gray': (128, 128, 128),
                'blue': (173, 216, 230),
                'green': (144, 238, 144),
                'yellow': (255, 255, 224),
                'pink': (255, 192, 203)
            }
            
            target_color = color_map.get(new_color.lower(), (255, 255, 255))
            
            # Apply color change only to masked area
            # This is a simple version - use AI for better results
            mask_3d = np.stack([wall_mask] * 3, axis=-1)
            colored = img_array.copy()
            colored[mask_3d > 0] = target_color
            
            # Blend with original for natural look
            alpha = 0.6
            result = (alpha * colored + (1 - alpha) * img_array).astype('uint8')
            
            result_img = Image.fromarray(result)
            result_img.save(output_path)
            
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
```

#### Step 3: Add API Endpoints

**File: `backend/app/routers/interior_customization.py`**

```python
"""
Interior Customization API
Allows users to edit 360° tour images in real-time
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Tuple
import logging
from pathlib import Path
import numpy as np

from app.services.segmentation_service import SegmentationService
from app.services.interior_inpainting_service import InteriorInpaintingService
from app.dependencies.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

class ObjectDetectionRequest(BaseModel):
    image_id: int
    click_x: int
    click_y: int

class ObjectDetectionResponse(BaseModel):
    object_type: str
    description: str
    style: str
    color: str
    material: str
    bbox: List[int]
    mask_id: str

class FurnitureReplacementRequest(BaseModel):
    image_id: int
    mask_id: str
    replacement_prompt: str
    # Examples:
    # "brown leather sofa"
    # "glass coffee table with gold legs"
    # "king size bed with white linen"

class WallColorChangeRequest(BaseModel):
    image_id: int
    new_color: str  # "white", "beige", "gray", "blue", etc.

@router.post("/detect-object", response_model=ObjectDetectionResponse)
async def detect_object_in_tour(
    request: ObjectDetectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Detect and identify an object in 360° tour image.
    User clicks on furniture, system identifies what it is.
    """
    try:
        # Get image path (you'll need to fetch from DB)
        # For now, assuming stored path
        image_path = f"storage/tours/{request.image_id}/front.png"
        
        if not Path(image_path).exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Initialize services
        segmentation_service = SegmentationService()
        
        # Detect object at click point
        seg_result = segmentation_service.detect_objects_in_image(
            image_path,
            click_point=(request.click_x, request.click_y)
        )
        
        # Identify what the object is
        object_info = segmentation_service.identify_object_type(
            image_path,
            seg_result['bbox']
        )
        
        # Save mask for later use
        mask_id = f"mask_{request.image_id}_{request.click_x}_{request.click_y}"
        mask_path = f"storage/temp/{mask_id}.npy"
        np.save(mask_path, seg_result['mask'])
        
        logger.info(f"Detected {object_info['object_type']} at ({request.click_x}, {request.click_y})")
        
        return ObjectDetectionResponse(
            object_type=object_info['object_type'],
            description=object_info['description'],
            style=object_info['style'],
            color=object_info['color'],
            material=object_info['material'],
            bbox=seg_result['bbox'],
            mask_id=mask_id
        )
        
    except Exception as e:
        logger.error(f"Object detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/replace-furniture")
async def replace_furniture_in_tour(
    request: FurnitureReplacementRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Replace detected furniture with AI-generated alternative.
    """
    try:
        # Get original image
        image_path = f"storage/tours/{request.image_id}/front.png"
        
        # Load saved mask
        mask_path = f"storage/temp/{request.mask_id}.npy"
        if not Path(mask_path).exists():
            raise HTTPException(status_code=404, detail="Mask not found. Please detect object first.")
        
        mask_array = np.load(mask_path)
        
        # Get original object info (could be cached or re-detected)
        segmentation_service = SegmentationService()
        object_info = segmentation_service.identify_object_type(
            image_path,
            [0, 0, 100, 100]  # Dummy bbox, we have mask
        )
        
        # Perform inpainting
        inpainting_service = InteriorInpaintingService()
        output_path = f"storage/tours/{request.image_id}/customized_{request.mask_id}.png"
        
        result = inpainting_service.replace_furniture(
            original_image_path=image_path,
            mask_array=mask_array,
            replacement_prompt=request.replacement_prompt,
            original_object_info=object_info,
            output_path=output_path
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Inpainting failed'))
        
        logger.info(f"Furniture replaced successfully: {output_path}")
        
        return {
            'success': True,
            'customized_image_url': f"/api/v1/tours/{request.image_id}/customized/{request.mask_id}",
            'preview_url': result['preview_url']
        }
        
    except Exception as e:
        logger.error(f"Furniture replacement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-wall-color")
async def change_wall_color_in_tour(
    request: WallColorChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Change wall color in 360° tour.
    """
    try:
        # Implementation similar to replace_furniture
        # But using wall detection and color change
        pass
    except Exception as e:
        logger.error(f"Wall color change error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customization-presets")
async def get_customization_presets():
    """
    Get predefined furniture and color options.
    """
    return {
        'furniture': {
            'sofas': [
                {'id': 1, 'name': 'Modern Gray Sectional', 'prompt': 'modern gray fabric sectional sofa'},
                {'id': 2, 'name': 'Brown Leather Sofa', 'prompt': 'brown leather 3-seater sofa'},
                {'id': 3, 'name': 'White Minimalist Sofa', 'prompt': 'white minimalist linen sofa'},
            ],
            'chairs': [
                {'id': 1, 'name': 'Eames Lounge Chair', 'prompt': 'eames style brown leather lounge chair'},
                {'id': 2, 'name': 'Scandinavian Armchair', 'prompt': 'scandinavian oak wood armchair with cushion'},
            ],
            'tables': [
                {'id': 1, 'name': 'Glass Coffee Table', 'prompt': 'modern glass coffee table with metal legs'},
                {'id': 2, 'name': 'Wooden Dining Table', 'prompt': 'oak wood dining table, rectangular'},
            ]
        },
        'wall_colors': [
            {'id': 1, 'name': 'Pure White', 'color': 'white'},
            {'id': 2, 'name': 'Warm Beige', 'color': 'beige'},
            {'id': 3, 'name': 'Light Gray', 'color': 'gray'},
            {'id': 4, 'name': 'Soft Blue', 'color': 'blue'},
        ],
        'flooring': [
            {'id': 1, 'name': 'Oak Hardwood', 'prompt': 'oak hardwood flooring'},
            {'id': 2, 'name': 'White Marble', 'prompt': 'white marble flooring with veins'},
            {'id': 3, 'name': 'Gray Carpet', 'prompt': 'plush gray carpet'},
        ]
    }
```

#### Step 4: Update Frontend - Interactive Editor

**File: `frontend/src/components/tours/InteriorCustomizer.tsx`**

```typescript
import React, { useState, useRef } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    Stack,
    TextField,
    CircularProgress,
    Alert
} from '@mui/material';
import { Brush, Palette, Sofa, Lamp, Image as ImageIcon } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface InteriorCustomizerProps {
    tourImageId: number;
    tourImageUrl: string;
    onImageUpdated: (newUrl: string) => void;
}

interface DetectedObject {
    object_type: string;
    description: string;
    style: string;
    color: string;
    material: string;
    bbox: number[];
    mask_id: string;
}

const InteriorCustomizer: React.FC<InteriorCustomizerProps> = ({
    tourImageId,
    tourImageUrl,
    onImageUpdated
}) => {
    const [editMode, setEditMode] = useState<'select' | 'replace' | 'color' | null>(null);
    const [detectedObject, setDetectedObject] = useState<DetectedObject | null>(null);
    const [loading, setLoading] = useState(false);
    const [replacementPrompt, setReplacementPrompt] = useState('');
    const [selectedPreset, setSelectedPreset] = useState('');
    const [presets, setPresets] = useState<any>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);

    // Load presets on mount
    React.useEffect(() => {
        loadPresets();
    }, []);

    const loadPresets = async () => {
        try {
            const response = await axios.get('/api/v1/interior/customization-presets');
            setPresets(response.data);
        } catch (error) {
            console.error('Failed to load presets:', error);
        }
    };

    const handleImageClick = async (event: React.MouseEvent<HTMLCanvasElement>) => {
        if (editMode !== 'select') return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = Math.floor(event.clientX - rect.left);
        const y = Math.floor(event.clientY - rect.top);

        setLoading(true);
        try {
            const response = await axios.post('/api/v1/interior/detect-object', {
                image_id: tourImageId,
                click_x: x,
                click_y: y
            });

            setDetectedObject(response.data);
            setEditMode('replace');
            
            // Draw bounding box
            drawBoundingBox(response.data.bbox);
            
            toast.success(`Detected: ${response.data.description}`);
        } catch (error) {
            toast.error('Failed to detect object');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const drawBoundingBox = (bbox: number[]) => {
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!ctx || !canvas) return;

        // Clear previous drawings
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw image
        if (imageRef.current) {
            ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);
        }

        // Draw bounding box
        const [x1, y1, x2, y2] = bbox;
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Draw label
        ctx.fillStyle = '#00ff00';
        ctx.fillRect(x1, y1 - 25, 200, 25);
        ctx.fillStyle = '#000';
        ctx.font = '14px Arial';
        ctx.fillText(detectedObject?.object_type || 'Object', x1 + 5, y1 - 8);
    };

    const handleReplaceFurniture = async () => {
        if (!detectedObject) return;

        setLoading(true);
        try {
            const response = await axios.post('/api/v1/interior/replace-furniture', {
                image_id: tourImageId,
                mask_id: detectedObject.mask_id,
                replacement_prompt: replacementPrompt || selectedPreset
            });

            toast.success('Furniture replaced! Generating new image...');
            
            // Update tour with new image
            onImageUpdated(response.data.customized_image_url);
            
            // Reset state
            setEditMode(null);
            setDetectedObject(null);
            setReplacementPrompt('');
        } catch (error) {
            toast.error('Failed to replace furniture');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handlePresetSelect = (preset: any) => {
        setSelectedPreset(preset.prompt);
        setReplacementPrompt(preset.prompt);
    };

    return (
        <Card sx={{ mt: 2 }}>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    🎨 Interior Customization
                </Typography>

                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                    <Button
                        variant={editMode === 'select' ? 'contained' : 'outlined'}
                        startIcon={<Brush />}
                        onClick={() => setEditMode('select')}
                    >
                        Select Furniture
                    </Button>
                    <Button
                        variant={editMode === 'color' ? 'contained' : 'outlined'}
                        startIcon={<Palette />}
                        onClick={() => setEditMode('color')}
                    >
                        Change Colors
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<ImageIcon />}
                        onClick={() => setEditMode(null)}
                    >
                        Reset
                    </Button>
                </Stack>

                {editMode === 'select' && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        Click on any furniture item in the image to select it for replacement
                    </Alert>
                )}

                {/* Canvas for interactive editing */}
                <Box sx={{ position: 'relative', mb: 2 }}>
                    <canvas
                        ref={canvasRef}
                        width={800}
                        height={600}
                        onClick={handleImageClick}
                        style={{
                            width: '100%',
                            maxWidth: 800,
                            border: '2px solid #ddd',
                            borderRadius: 8,
                            cursor: editMode === 'select' ? 'crosshair' : 'default'
                        }}
                    />
                    <img
                        ref={imageRef}
                        src={tourImageUrl}
                        alt="Tour"
                        style={{ display: 'none' }}
                        onLoad={() => {
                            const canvas = canvasRef.current;
                            const ctx = canvas?.getContext('2d');
                            if (ctx && imageRef.current && canvas) {
                                canvas.width = imageRef.current.width;
                                canvas.height = imageRef.current.height;
                                ctx.drawImage(imageRef.current, 0, 0);
                            }
                        }}
                    />
                    {loading && (
                        <Box
                            sx={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -50%)'
                            }}
                        >
                            <CircularProgress />
                        </Box>
                    )}
                </Box>

                {/* Detected Object Info */}
                {detectedObject && (
                    <Dialog open={editMode === 'replace'} onClose={() => setEditMode(null)} maxWidth="md" fullWidth>
                        <DialogTitle>
                            Replace {detectedObject.object_type}
                        </DialogTitle>
                        <DialogContent>
                            <Stack spacing={2} sx={{ mt: 2 }}>
                                <Box>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Current Item:
                                    </Typography>
                                    <Typography color="text.secondary">
                                        {detectedObject.description}
                                    </Typography>
                                    <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                        <Chip label={detectedObject.style} size="small" />
                                        <Chip label={detectedObject.color} size="small" />
                                        <Chip label={detectedObject.material} size="small" />
                                    </Stack>
                                </Box>

                                <Typography variant="subtitle2">
                                    Choose Replacement:
                                </Typography>

                                {/* Preset Options */}
                                {presets && presets.furniture[detectedObject.object_type + 's'] && (
                                    <Stack spacing={1}>
                                        {presets.furniture[detectedObject.object_type + 's'].map((preset: any) => (
                                            <Button
                                                key={preset.id}
                                                variant={selectedPreset === preset.prompt ? 'contained' : 'outlined'}
                                                onClick={() => handlePresetSelect(preset)}
                                                fullWidth
                                            >
                                                {preset.name}
                                            </Button>
                                        ))}
                                    </Stack>
                                )}

                                {/* Custom Prompt */}
                                <TextField
                                    fullWidth
                                    label="Or describe custom furniture"
                                    value={replacementPrompt}
                                    onChange={(e) => setReplacementPrompt(e.target.value)}
                                    placeholder="e.g., brown leather sofa with chrome legs"
                                    helperText="Describe the furniture you want to add"
                                    multiline
                                    rows={2}
                                />
                            </Stack>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setEditMode(null)}>Cancel</Button>
                            <Button
                                variant="contained"
                                onClick={handleReplaceFurniture}
                                disabled={!replacementPrompt && !selectedPreset}
                            >
                                Replace Furniture
                            </Button>
                        </DialogActions>
                    </Dialog>
                )}
            </CardContent>
        </Card>
    );
};

export default InteriorCustomizer;
```

#### Step 5: Integration with Existing 360° Viewer

**Update: `frontend/src/pages/floorplan/FloorPlanGenerator.tsx`**

Add the customizer below the 360° viewer:

```typescript
import InteriorCustomizer from '../../components/tours/InteriorCustomizer';

// Inside your component where you show 360° tour:
{tour360 && (
    <>
        <Panorama360Viewer
            imageUrl={tour360.walkthrough_views[currentViewIndex].url}
            title={tour360.walkthrough_views[currentViewIndex].view}
        />
        
        <InteriorCustomizer
            tourImageId={tour360.id}
            tourImageUrl={tour360.walkthrough_views[currentViewIndex].url}
            onImageUpdated={(newUrl) => {
                // Update the tour with customized image
                const updatedViews = [...tour360.walkthrough_views];
                updatedViews[currentViewIndex].url = newUrl;
                setTour360({
                    ...tour360,
                    walkthrough_views: updatedViews
                });
            }}
        />
    </>
)}
```

---

## 📋 Required Dependencies

### Backend

```bash
pip install segment-anything-py  # For SAM
pip install replicate  # For Replicate API access
# OpenAI already installed
```

### Frontend

```bash
# Already have all required dependencies
```

---

## 🔑 Environment Variables

```env
# .env
OPENAI_API_KEY=sk-...                # For GPT-4 Vision
REPLICATE_API_TOKEN=r8_...           # For SAM and SDXL Inpainting
MESHY_API_KEY=msy_...                # Already have this
```

---

## 🎯 User Flow

### Step 1: View 360° Tour
User navigates through 360° walkthrough as normal

### Step 2: Enter Edit Mode
User clicks "Select Furniture" button

### Step 3: Click on Object
User clicks on sofa in image

### Step 4: AI Detection
- SAM detects sofa boundaries
- GPT-4 Vision identifies: "Gray fabric sectional sofa"
- System shows bounding box + info

### Step 5: Choose Replacement
User either:
- Selects preset: "Brown Leather Sofa"
- Or types custom: "blue velvet tufted sofa"

### Step 6: AI Generation
- Stable Diffusion inpaints new sofa
- Preserves room structure, lighting, perspective
- Returns updated 360° image

### Step 7: View Result
- Updated image replaces original in 360° viewer
- User can continue editing other elements

---

## 💡 Advanced Features (Phase 2)

### 1. Lighting Adjustment
```python
# Change time of day
- "Morning sunlight"
- "Evening golden hour"
- "Night with lamps"
```

### 2. Style Transfer
```python
# Change entire room style
- "Make this room Scandinavian style"
- "Convert to industrial loft"
- "Add bohemian decor"
```

### 3. Virtual Staging
```python
# Add furniture to empty rooms
- "Add modern living room furniture"
- "Stage as home office"
```

### 4. Before/After Comparison
```python
# Slider to compare original vs customized
<ImageComparisonSlider
    before={originalUrl}
    after={customizedUrl}
/>
```

### 5. Save Design Variations
```python
# Let users save multiple design options
- "Living Room - Option A (Modern)"
- "Living Room - Option B (Traditional)"
- "Living Room - Option C (Minimalist)"
```

---

## 📊 Cost Estimation

### Per Customization Operation:

| Service | Cost per Request |
|---------|------------------|
| GPT-4 Vision (object detection) | $0.01 |
| Segment Anything (SAM) | $0.02 |
| SDXL Inpainting | $0.05 |
| **Total per edit** | **$0.08** |

### Monthly (for 1000 users):
- Average 5 edits per tour = $0.40/tour
- 1000 users × 2 tours/month = 2000 tours
- **Total: ~$800/month**

---

## 🚀 Quick Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1** | 1 week | Object detection + GPT-4 Vision |
| **Phase 2** | 1 week | Inpainting service + API |
| **Phase 3** | 1 week | Frontend UI + integration |
| **Phase 4** | 1 week | Testing + optimization |
| **Total** | **4 weeks** | **Full feature** |

---

## ✅ Summary

This feature adds **professional-grade interior design capabilities** to your 360° tours using:

✅ **AI Object Detection** - Click & identify furniture  
✅ **GPT-4 Vision** - Understand what objects are  
✅ **Stable Diffusion** - Generate realistic replacements  
✅ **Real-time Preview** - See changes instantly  
✅ **Preset Library** - Quick furniture options  
✅ **Custom Prompts** - Unlimited creativity  

**Result:** Users can fully customize interiors without manual photo editing or 3D modeling skills!

Would you like me to implement Phase 1 now?
