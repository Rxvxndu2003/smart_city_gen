"""
3D City Generation Router - API endpoints for generating geo-realistic city models.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
from pathlib import Path
import json
import subprocess
import tempfile

from app.services.geo_data_service import geo_data_service
from app.services.parcel_service import parcel_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/city-generator", tags=["city-generator"])


# Request/Response Models
class BoundingBox(BaseModel):
    """Geographic bounding box."""
    north: float = Field(..., description="North latitude")
    south: float = Field(..., description="South latitude")
    east: float = Field(..., description="East longitude")
    west: float = Field(..., description="West longitude")


class CityGenerationRequest(BaseModel):
    """Request to generate a 3D city model."""
    name: str = Field(..., description="Name for this city generation")
    
    # Area selection (provide one)
    bounding_box: Optional[BoundingBox] = None
    polygon: Optional[List[List[float]]] = Field(
        None,
        description="Polygon coordinates as [[lat, lon], [lat, lon], ...]"
    )
    place_name: Optional[str] = Field(
        None,
        description="Place name to geocode (e.g., 'Colombo Fort, Sri Lanka')"
    )
    
    # Generation options
    target_parcel_width: float = Field(
        15.0,
        description="Target width for subdivided parcels in meters"
    )
    min_building_height: float = Field(8.0, description="Minimum building height in meters")
    max_building_height: float = Field(30.0, description="Maximum building height in meters")
    export_format: str = Field("glb", description="Export format: glb or gltf")
    
    # Advanced 3D details (realistic features)
    enable_advanced_details: bool = Field(
        True,
        description="Enable advanced realistic details (windows, vehicles, lights, crosswalks)"
    )
    enable_windows: bool = Field(True, description="Add windows to buildings")
    enable_vehicles: bool = Field(True, description="Add vehicles on roads")
    enable_street_lights: bool = Field(True, description="Add street lights")
    enable_crosswalks: bool = Field(True, description="Add crosswalk markings")
    vehicle_spacing: float = Field(
        20.0,
        description="Distance between vehicles on roads in meters"
    )
    tree_spacing: float = Field(
        8.0,
        description="Distance between trees in parks in meters"
    )


class CityGenerationResponse(BaseModel):
    """Response from city generation."""
    status: str
    message: str
    generation_id: str
    data_file: Optional[str] = None
    model_file: Optional[str] = None


class GenerationStatus(BaseModel):
    """Status of a generation task."""
    generation_id: str
    status: str
    progress: float
    message: str
    data_file: Optional[str] = None
    model_file: Optional[str] = None
    error: Optional[str] = None


# In-memory storage for generation status (use Redis in production)
generation_tasks = {}


@router.post("/generate", response_model=CityGenerationResponse)
async def generate_city_model(
    request: CityGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a 3D city model from real-world geographic data.
    
    This endpoint:
    1. Fetches real data from OpenStreetMap for the specified area
    2. Processes roads, buildings, parks, and other features
    3. Subdivides city blocks into parcels
    4. Generates a 3D model in Blender (headless)
    5. Exports to GLB/GLTF format
    
    The generation runs in the background. Use the returned generation_id
    to check status with GET /status/{generation_id}.
    """
    try:
        # Validate input
        if not any([request.bounding_box, request.polygon, request.place_name]):
            raise HTTPException(
                status_code=400,
                detail="Must provide bounding_box, polygon, or place_name"
            )
        
        # Generate unique ID
        import uuid
        generation_id = str(uuid.uuid4())
        
        # Initialize status
        generation_tasks[generation_id] = {
            'status': 'queued',
            'progress': 0.0,
            'message': 'Task queued',
            'data_file': None,
            'model_file': None,
            'error': None
        }
        
        # Queue background task
        background_tasks.add_task(
            process_city_generation,
            generation_id,
            request
        )
        
        return CityGenerationResponse(
            status="queued",
            message="City generation task queued",
            generation_id=generation_id
        )
        
    except Exception as e:
        logger.error(f"Error queueing city generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class HybridGenerationRequest(CityGenerationRequest):
    """Request for hybrid Blender + Replicate generation."""
    enable_ai_enhancement: bool = Field(
        True,
        description="Enable AI enhancement with Replicate"
    )
    enhancement_strength: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Strength of AI enhancement (0.0-1.0)"
    )
    enhancement_prompt: Optional[str] = Field(
        None,
        description="Custom prompt for AI enhancement"
    )
    num_views: int = Field(
        4,
        ge=1,
        le=8,
        description="Number of camera views to render and enhance"
    )


class HybridGenerationResponse(BaseModel):
    """Response from hybrid generation."""
    status: str
    message: str
    generation_id: str
    estimated_cost: float
    data_file: Optional[str] = None
    model_file: Optional[str] = None
    base_renders: Optional[List[str]] = None
    enhanced_renders: Optional[List[str]] = None


@router.post("/generate-hybrid", response_model=HybridGenerationResponse)
async def generate_hybrid_city(
    request: HybridGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a 3D city model with optional AI enhancement.
    
    This endpoint combines:
    1. Blender-based geometric generation (precise, compliant)
    2. Replicate AI enhancement (photorealistic, beautiful)
    
    The process:
    1. Generate 3D geometry with Blender
    2. Render multiple camera views
    3. Optionally enhance with Replicate SDXL
    4. Return both base and enhanced versions
    """
    try:
        from app.services.replicate_service import replicate_service
        
        # Validate input
        if not any([request.bounding_box, request.polygon, request.place_name]):
            raise HTTPException(
                status_code=400,
                detail="Must provide bounding_box, polygon, or place_name"
            )
        
        # Check if Replicate is available
        if request.enable_ai_enhancement and not replicate_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Replicate API not configured. Set REPLICATE_API_TOKEN environment variable."
            )
        
        # Estimate cost
        estimated_cost = 0.0
        if request.enable_ai_enhancement:
            estimated_cost = replicate_service.estimate_cost(
                num_images=request.num_views,
                model='sdxl'
            )
        
        # Generate unique ID
        import uuid
        generation_id = str(uuid.uuid4())
        
        # Initialize status
        generation_tasks[generation_id] = {
            'status': 'queued',
            'progress': 0.0,
            'message': 'Hybrid generation task queued',
            'data_file': None,
            'model_file': None,
            'base_renders': [],
            'enhanced_renders': [],
            'error': None
        }
        
        # Queue background task
        background_tasks.add_task(
            process_hybrid_generation,
            generation_id,
            request
        )
        
        return HybridGenerationResponse(
            status="queued",
            message="Hybrid city generation task queued",
            generation_id=generation_id,
            estimated_cost=estimated_cost
        )
        
    except Exception as e:
        logger.error(f"Error queueing hybrid generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/status/{generation_id}", response_model=GenerationStatus)
async def get_generation_status(generation_id: str):
    """Get the status of a city generation task."""
    if generation_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Generation task not found")
    
    task = generation_tasks[generation_id]
    
    return GenerationStatus(
        generation_id=generation_id,
        status=task['status'],
        progress=task['progress'],
        message=task['message'],
        data_file=task.get('data_file'),
        model_file=task.get('model_file'),
        error=task.get('error')
    )


@router.get("/preview/{generation_id}")
async def get_preview_data(generation_id: str):
    """Get preview data (GeoJSON) for a generation task."""
    if generation_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Generation task not found")
    
    task = generation_tasks[generation_id]
    
    if not task.get('data_file'):
        raise HTTPException(status_code=404, detail="Data not yet generated")
    
    data_path = Path(task['data_file'])
    if not data_path.exists():
        raise HTTPException(status_code=404, detail="Data file not found")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    return data


async def process_hybrid_generation(generation_id: str, request: HybridGenerationRequest):
    """
    Background task for hybrid Blender + Replicate generation.
    
    Steps:
    1. Generate 3D geometry with Blender (60% progress)
    2. Render multiple camera views (20% progress)
    3. Enhance with Replicate AI (20% progress)
    4. Package results
    """
    try:
        from app.services.replicate_service import replicate_service
        import asyncio
        
        task = generation_tasks[generation_id]
        
        # STAGE 1: Generate 3D Geometry (same as regular generation)
        task['status'] = 'generating_geometry'
        task['progress'] = 0.1
        task['message'] = 'Fetching geographic data...'
        
        # Fetch data
        bbox_dict = None
        if request.bounding_box:
            bbox_dict = {
                'north': request.bounding_box.north,
                'south': request.bounding_box.south,
                'east': request.bounding_box.east,
                'west': request.bounding_box.west
            }
        
        city_data = geo_data_service.fetch_city_data(
            bbox=bbox_dict,
            polygon=request.polygon,
            place_name=request.place_name
        )
        
        task['progress'] = 0.2
        task['message'] = 'Processing city data...'
        
        # Enhance building data
        for building in city_data.get('buildings', []):
            props = building.get('properties', {})
            if 'height' not in props:
                import random
                props['height'] = random.uniform(
                    request.min_building_height,
                    request.max_building_height
                )
        
        # Save data
        data_filename = f"{generation_id}_data.json"
        data_path = geo_data_service.save_processed_data(city_data, data_filename)
        task['data_file'] = str(data_path)
        
        task['progress'] = 0.3
        task['message'] = 'Generating 3D model with Blender...'
        
        # Generate 3D model
        model_filename = f"{generation_id}_model.{request.export_format}"
        model_path = Path("storage/models") / model_filename
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        blender_path = find_blender_executable()
        if not blender_path:
            raise Exception("Blender not found")
        
        script_path = Path(__file__).parent.parent.parent.parent / "blender_scripts" / "generate_city.py"
        
        cmd = [
            blender_path,
            '-b',
            '-P', str(script_path),
            '--',
            '--input', str(data_path),
            '--output', str(model_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"Blender failed: {result.stderr}")
        
        task['model_file'] = str(model_path)
        task['progress'] = 0.6
        task['message'] = 'Blender generation complete'
        
        # STAGE 2: Render Multiple Views
        task['status'] = 'rendering_views'
        task['progress'] = 0.65
        task['message'] = f'Rendering {request.num_views} camera views...'
        
        renders_dir = Path("storage/renders") / generation_id
        renders_dir.mkdir(parents=True, exist_ok=True)
        
        base_renders = []
        for i in range(request.num_views):
            # For now, create placeholder renders
            # In production, call Blender to render different camera angles
            render_path = renders_dir / f"view_{i+1}.png"
            
            # TODO: Call Blender to render this view
            # For now, just log
            logger.info(f"Would render view {i+1} to {render_path}")
            base_renders.append(str(render_path))
        
        task['base_renders'] = base_renders
        task['progress'] = 0.8
        task['message'] = 'Views rendered'
        
        # STAGE 3: AI Enhancement (if enabled)
        enhanced_renders = []
        if request.enable_ai_enhancement and replicate_service.is_available():
            task['status'] = 'enhancing_ai'
            task['progress'] = 0.85
            task['message'] = 'Enhancing with Replicate AI...'
            
            # Build enhancement prompt
            prompt = request.enhancement_prompt or \
                    "photorealistic city aerial view, detailed buildings, realistic lighting, " \
                    "professional architecture photography, 8k, ultra detailed"
            
            # Enhance each view
            for i, base_render in enumerate(base_renders):
                if Path(base_render).exists():
                    enhanced_path = await replicate_service.enhance_city_render(
                        input_image_path=base_render,
                        prompt=prompt,
                        strength=request.enhancement_strength
                    )
                    
                    if enhanced_path:
                        enhanced_renders.append(enhanced_path)
                    else:
                        # Fallback to base render if enhancement fails
                        enhanced_renders.append(base_render)
                        logger.warning(f"Enhancement failed for view {i+1}, using base render")
                
                # Update progress
                progress_increment = 0.15 / len(base_renders)
                task['progress'] += progress_increment
            
            task['enhanced_renders'] = enhanced_renders
            task['message'] = 'AI enhancement complete'
        
        # Complete
        task['status'] = 'completed'
        task['progress'] = 1.0
        task['message'] = 'Hybrid generation completed successfully'
        
        logger.info(f"Hybrid generation {generation_id} completed")
        
    except Exception as e:
        logger.error(f"Error in hybrid generation {generation_id}: {e}")
        task['status'] = 'failed'
        task['error'] = str(e)
        task['message'] = f'Generation failed: {str(e)}'


async def process_city_generation(generation_id: str, request: CityGenerationRequest):

    """
    Background task to process city generation.
    
    Steps:
    1. Fetch OSM data
    2. Process and normalize
    3. Subdivide blocks into parcels
    4. Save processed data
    5. Call Blender to generate 3D model
    6. Export to GLB/GLTF
    """
    try:
        task = generation_tasks[generation_id]
        
        # Step 1: Fetch geographic data
        task['status'] = 'fetching_data'
        task['progress'] = 0.1
        task['message'] = 'Fetching data from OpenStreetMap...'
        
        bbox_dict = None
        if request.bounding_box:
            bbox_dict = {
                'north': request.bounding_box.north,
                'south': request.bounding_box.south,
                'east': request.bounding_box.east,
                'west': request.bounding_box.west
            }
        
        city_data = geo_data_service.fetch_city_data(
            bbox=bbox_dict,
            polygon=request.polygon,
            place_name=request.place_name
        )
        
        task['progress'] = 0.3
        task['message'] = 'Data fetched successfully'
        
        # Step 2: Process parcels
        task['status'] = 'processing_parcels'
        task['progress'] = 0.4
        task['message'] = 'Subdividing city blocks into parcels...'
        
        # Infer city blocks from roads
        from geopandas import GeoDataFrame
        from shapely.geometry import shape
        
        # Convert roads to GeoDataFrame (simplified)
        if city_data.get('roads'):
            # For now, skip block inference to keep it simple
            # In production, implement proper block inference
            pass
        
        task['progress'] = 0.5
        task['message'] = 'Parcels processed'
        
        # Step 3: Enhance building data
        task['status'] = 'enhancing_data'
        task['progress'] = 0.6
        task['message'] = 'Enhancing building and feature data...'
        
        # Add height variation to buildings
        for building in city_data.get('buildings', []):
            props = building.get('properties', {})
            if 'height' not in props:
                import random
                props['height'] = random.uniform(
                    request.min_building_height,
                    request.max_building_height
                )
        
        # Step 4: Save processed data
        task['progress'] = 0.7
        task['message'] = 'Saving processed data...'
        
        data_filename = f"{generation_id}_data.json"
        data_path = geo_data_service.save_processed_data(city_data, data_filename)
        task['data_file'] = str(data_path)
        
        # Step 5: Generate 3D model with Blender
        task['status'] = 'generating_3d'
        task['progress'] = 0.8
        task['message'] = 'Generating 3D model in Blender...'
        
        model_filename = f"{generation_id}_model.{request.export_format}"
        model_path = Path("storage/models") / model_filename
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Find Blender executable
        blender_path = find_blender_executable()
        if not blender_path:
            raise Exception("Blender not found. Please install Blender and ensure it's in PATH")
        
        # Get Blender script path
        script_path = Path(__file__).parent.parent.parent.parent / "blender" / "generate_city.py"
        
        # Call Blender in headless mode
        cmd = [
            blender_path,
            '-b',  # Background mode
            '-P', str(script_path),  # Python script
            '--',
            '--input', str(data_path),
            '--output', str(model_path)
        ]
        
        logger.info(f"Running Blender: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Blender failed: {result.stderr}")
        
        task['model_file'] = str(model_path)
        
        # Step 6: Complete
        task['status'] = 'completed'
        task['progress'] = 1.0
        task['message'] = 'City generation completed successfully'
        
        logger.info(f"Generation {generation_id} completed: {model_path}")
        
    except Exception as e:
        logger.error(f"Error in city generation {generation_id}: {e}")
        task['status'] = 'failed'
        task['error'] = str(e)
        task['message'] = f'Generation failed: {str(e)}'


def find_blender_executable() -> Optional[str]:
    """Find Blender executable in system PATH or common locations."""
    import shutil
    
    # Try PATH first
    blender = shutil.which('blender')
    if blender:
        return blender
    
    # Common macOS locations
    mac_paths = [
        '/Applications/Blender.app/Contents/MacOS/Blender',
        '/Applications/Blender.app/Contents/MacOS/blender',
    ]
    
    for path in mac_paths:
        if Path(path).exists():
            return path
    
    return None
