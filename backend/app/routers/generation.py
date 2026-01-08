"""
3D Generation router - Blender generation endpoints with Celery task queue.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.services.ml_generation import get_ml_service
from app.services.drawing_to_3d_service import get_drawing_service
from app.services.uda_house_validator import get_uda_validator
from app.services.house_ml_service import get_house_ml_service
from app.services.image_to_floorplan_service import get_image_to_floorplan_service
from app.models.validation_report import ValidationReport, ReportType
from pydantic import BaseModel
from typing import Optional, List
import json
import subprocess
from pathlib import Path
import uuid
import os
import shutil

# Try to import replicate, but make it optional
try:
    from app.services.replicate_service import replicate_service
    REPLICATE_AVAILABLE = True
except Exception as e:
    print(f"⚠ Replicate service not available: {e}")
    replicate_service = None
    REPLICATE_AVAILABLE = False

router = APIRouter()

# In-memory storage for demo (replace with Redis/database in production)
generation_jobs = {}

class GenerationRequest(BaseModel):
    width: Optional[float] = 20
    depth: Optional[float] = 15
    height: Optional[float] = 30
    num_floors: Optional[int] = 10
    name: Optional[str] = "Generated Layout"

@router.post("/{project_id}")
async def start_generation(
    project_id: int,
    request: Optional[GenerationRequest] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start 3D generation job for a project."""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Prepare parameters from project
    params = {
        "width": request.width if request else 20,
        "depth": request.depth if request else 15,
        "height": project.building_height or 30,
        "num_floors": project.num_floors or 10,
        "site_area": float(project.site_area_m2) if project.site_area_m2 else 300,
        "building_coverage": float(project.building_coverage) if project.building_coverage else 60,
        "project_type": project.project_type
    }
    
    # Store job status
    generation_jobs[project_id] = {
        "job_id": job_id,
        "status": "queued",
        "project_id": project_id,
        "params": params
    }
    
    # Note: In production, this would queue a Celery task
    # For now, we'll simulate the process
    # background_tasks.add_task(run_blender_generation, project_id, params)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "3D generation started. Check status endpoint for updates."
    }

@router.get("/{project_id}/status")
async def get_generation_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get generation job status for a project."""
    if project_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="No generation job found for this project")
    
    job = generation_jobs[project_id]
    project = db.query(Project).filter(Project.id == project_id).first()
    
    # Auto-progress through states
    if job["status"] == "queued":
        # Move to processing and start generation
        job["status"] = "processing"
        generation_jobs[project_id] = job
        
        # Generate actual GLB file immediately with ML-enhanced parameters
        output_dir = Path("storage/3d_models") / str(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        glb_path = output_dir / "building.glb"
        
        try:
            # Get ML service and enhance parameters
            ml_service = get_ml_service()
            params = job["params"]
            
            # Use ML model to predict optimal parameters
            enhanced_params_json = ml_service.generate_blender_params(params)
            enhanced_params = json.loads(enhanced_params_json)
            enhanced_params['output_path'] = str(glb_path)
            enhanced_params['format'] = 'GLB'
            
            print(f"\n{'='*60}")
            print(f"ML-Enhanced 3D Generation for Project {project_id}")
            print(f"{'='*60}")
            print(f"Project Type: {params.get('project_type', 'UNKNOWN')}")
            print(f"Original Dimensions: {params.get('width')}x{params.get('depth')}x{params.get('height')}m")
            print(f"ML-Enhanced Parameters:")
            print(f"  - Window Size: {enhanced_params.get('window_size', 'N/A')}m")
            print(f"  - Window Spacing: {enhanced_params.get('window_spacing', 'N/A')}m")
            print(f"  - Facade Detail: Level {enhanced_params.get('facade_detail_level', 'N/A')}")
            print(f"  - Architectural Style: {enhanced_params.get('architectural_style', 'N/A')}")
            print(f"  - Balconies: {'Yes' if enhanced_params.get('balcony_enabled') else 'No'}")
            print(f"  - Material Quality: {enhanced_params.get('material_quality', 'N/A')}")
            print(f"{'='*60}\n")
            
            params_json = json.dumps(enhanced_params)
            
            # Run Blender script to generate building with ML parameters
            blender_script = Path("blender_scripts/generate_building.py")
            if blender_script.exists():
                # Use full path to Blender (Homebrew installation on macOS)
                blender_path = "/opt/homebrew/bin/blender"
                if Path(blender_path).exists():
                    print("Running Blender with ML-enhanced parameters...")
                    cmd = [blender_path, "--background", "--python", str(blender_script), "--", params_json]
                    result = subprocess.run(cmd, timeout=120, check=False, capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✓ Blender generation completed successfully")
                    else:
                        print(f"⚠ Blender exited with code {result.returncode}")
                        if result.stderr:
                            print(f"Blender stderr: {result.stderr[:500]}")
                        if result.stdout:
                            print(f"Blender stdout: {result.stdout[:500]}")
                else:
                    print("⚠ Blender not found at /opt/homebrew/bin/blender, creating placeholder")
            
            # If Blender generation failed or not available, create a placeholder GLB
            if not glb_path.exists():
                print("Creating placeholder GLB file...")
                # Create minimal valid GLB file (placeholder)
                import struct
                # GLB header: magic, version, length
                glb_data = struct.pack('<III', 0x46546C67, 2, 12)  # 'glTF' in little-endian
                glb_path.write_bytes(glb_data)
                print("✓ Placeholder GLB created")
        
        except Exception as e:
            print(f"✗ Generation error: {e}")
            import traceback
            traceback.print_exc()
            # Create placeholder file anyway
            if not glb_path.exists():
                glb_path.write_text("")
        
        # Update job status to completed
        job["status"] = "completed"
        model_url_path = f"/storage/3d_models/{project_id}/building.glb"
        job["model_url"] = model_url_path
        generation_jobs[project_id] = job
        
        # Save to database
        if project:
            project.model_url = model_url_path
            db.commit()
            db.refresh(project)
    
    return job

@router.get("/{project_id}/download")
async def download_model(
    project_id: int,
    token: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download generated 3D model."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.model_url:
        raise HTTPException(status_code=404, detail="No 3D model has been generated for this project")
    
    # Remove leading slash and construct file path
    file_path = project.model_url.lstrip('/')
    model_path = Path(file_path)
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model file not found")
    
    return FileResponse(
        path=str(model_path),
        media_type="model/gltf-binary",
        filename=f"project_{project_id}_building.glb"
    )

@router.delete("/{project_id}/delete")
async def delete_model(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete generated 3D model and clean up files."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.model_url:
        raise HTTPException(status_code=404, detail="No 3D model exists for this project")
    
    # Delete the file
    file_path = project.model_url.lstrip('/')
    model_path = Path(file_path)
    
    try:
        if model_path.exists():
            model_path.unlink()
            print(f"✓ Deleted model file: {model_path}")
            
            # Try to delete parent directory if empty
            try:
                model_path.parent.rmdir()
                print(f"✓ Deleted empty directory: {model_path.parent}")
            except OSError:
                pass  # Directory not empty or doesn't exist
        
        # Clear model_url from database
        project.model_url = None
        db.commit()
        db.refresh(project)
        
        # Remove from generation jobs
        if project_id in generation_jobs:
            del generation_jobs[project_id]
        
        return {
            "success": True,
            "message": "3D model deleted successfully"
        }
        
    except Exception as e:
        print(f"✗ Error deleting model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

def run_blender_generation(project_id: int, params: dict):
    """Run Blender generation (background task)."""
    try:
        output_dir = Path("storage/models") / str(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        glb_path = output_dir / "building.glb"
        
        params_json = json.dumps({
            **params,
            'output_path': str(glb_path),
            'format': 'GLB'
        })
        
        # This would run Blender in production
        # cmd = ["blender", "--background", "--python", "blender_scripts/generate_building.py", "--", params_json]
        # subprocess.run(cmd, timeout=300)
        
        generation_jobs[project_id]["status"] = "completed"
        generation_jobs[project_id]["model_url"] = str(glb_path)
        
    except Exception as e:
        generation_jobs[project_id]["status"] = "failed"
        generation_jobs[project_id]["error"] = str(e)


class CityGenerationRequest(BaseModel):
    grid_size: Optional[int] = 10  # 10x10 grid of city blocks
    block_size: Optional[int] = 30  # 30m x 30m blocks
    road_width: Optional[int] = 6   # 6m wide roads


@router.post("/{project_id}/city")
async def generate_city_layout(
    project_id: int,
    request: Optional[CityGenerationRequest] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a complete city layout with multiple buildings, roads, parks, and vehicles."""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Use request parameters or defaults
    if request is None:
        request = CityGenerationRequest()
    
    # Prepare output directory
    output_dir = Path("storage/3d_models") / str(project_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    glb_path = output_dir / "city.glb"
    
    # Prepare city generation parameters with project context
    city_params = {
        "grid_size": request.grid_size,
        "block_size": request.block_size,
        "road_width": request.road_width,
        "output_path": str(glb_path),
        "format": "GLB",
        # Project metadata for context-aware generation
        "project_name": project.name,
        "project_description": project.description or "",
        "project_type": project.project_type or "Mixed-Use",
        "location_city": project.location_city or "",
        "location_district": project.location_district or "",
        "num_floors": project.num_floors or 10,
        "building_height": float(project.building_height) if project.building_height else 30.0,
        "site_area_m2": float(project.site_area_m2) if project.site_area_m2 else 10000.0,
        "parking_spaces": project.parking_spaces or 50
    }
    
    print("\n" + "="*60)
    print(f"CITY LAYOUT GENERATION - Project {project_id}")
    print("="*60)
    print(f"Grid Size: {request.grid_size}x{request.grid_size}")
    print(f"Block Size: {request.block_size}m")
    print(f"Road Width: {request.road_width}m")
    print(f"Output: {glb_path}")
    print("="*60 + "\n")
    
    try:
        # Run Blender city generation
        blender_path = "/opt/homebrew/bin/blender"
        script_path = Path(__file__).parent.parent.parent / "blender_scripts" / "generate_city.py"
        
        params_json = json.dumps(city_params)
        
        print(f"Running Blender city generation...")
        result = subprocess.run(
            [
                blender_path,
                "--background",
                "--python", str(script_path),
                "--", params_json
            ],
            capture_output=True,
            text=True,
            timeout=1200  # 20 minute timeout for city generation
        )
        
        print("Blender output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"✗ Blender generation failed with code {result.returncode}")
            print(f"Error output: {result.stderr}")
            raise HTTPException(status_code=500, detail="City generation failed")
        
        # Verify GLB file was created
        if not glb_path.exists():
            raise HTTPException(status_code=500, detail="City GLB file was not created")
        
        file_size = glb_path.stat().st_size
        print(f"✓ City generated successfully: {file_size / (1024*1024):.2f} MB")
        
        # Update project with city model URL
        project.model_url = f"/storage/3d_models/{project_id}/city.glb"
        db.commit()
        db.refresh(project)
        
        return {
            "status": "completed",
            "message": "City layout generated successfully",
            "model_url": project.model_url,
            "file_size": file_size,
            "grid_size": request.grid_size,
            "project_id": project_id
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="City generation timed out")
    except Exception as e:
        print(f"✗ Error during city generation: {e}")
        raise HTTPException(status_code=500, detail=f"City generation failed: {str(e)}")


class HybridCityGenerationRequest(BaseModel):
    """Request for hybrid Blender + Replicate generation."""
    grid_size: Optional[int] = 10
    block_size: Optional[int] = 30
    road_width: Optional[int] = 6
    enable_ai_enhancement: Optional[bool] = False
    enhancement_strength: Optional[float] = 0.7
    num_views: Optional[int] = 4
    enable_advanced_details: Optional[bool] = True
    enable_windows: Optional[bool] = True
    enable_vehicles: Optional[bool] = True
    enable_street_lights: Optional[bool] = True
    enable_crosswalks: Optional[bool] = True
    vehicle_spacing: Optional[float] = 20.0
    tree_spacing: Optional[float] = 8.0


@router.post("/{project_id}/city-hybrid")
async def generate_hybrid_city_layout(
    project_id: int,
    request: Optional[HybridCityGenerationRequest] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a city layout with optional AI enhancement.
    
    This endpoint combines:
    1. Blender-based geometric generation (precise, compliant)
    2. Replicate AI enhancement (photorealistic, beautiful)
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Use request parameters or defaults
    if request is None:
        request = HybridCityGenerationRequest()
    
    # Only check Replicate if AI enhancement is explicitly requested
    if request.enable_ai_enhancement:
        if not REPLICATE_AVAILABLE or not replicate_service:
            # Disable AI enhancement but continue with Blender generation
            print("⚠ AI enhancement requested but Replicate not available (Python 3.14 compatibility issue)")
            print("  Continuing with Blender-only generation...")
            request.enable_ai_enhancement = False
        elif not replicate_service.is_available():
            print("⚠ AI enhancement requested but REPLICATE_API_TOKEN not set")
            print("  Continuing with Blender-only generation...")
            request.enable_ai_enhancement = False
    
    # Prepare output directory
    output_dir = Path("storage/3d_models") / str(project_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    glb_path = output_dir / "city.glb"
    
    # Prepare city generation parameters with FULL project context
    city_params = {
        # Grid parameters
        "grid_size": request.grid_size,
        "block_size": request.block_size,
        "road_width": request.road_width,
        "output_path": str(glb_path),
        "format": "GLB",
        
        # Advanced visual details
        "enable_advanced_details": request.enable_advanced_details,
        "enable_windows": request.enable_windows,
        "enable_vehicles": request.enable_vehicles,
        "enable_street_lights": request.enable_street_lights,
        "enable_crosswalks": request.enable_crosswalks,
        "vehicle_spacing": request.vehicle_spacing,
        "tree_spacing": request.tree_spacing,
        
        # Project metadata
        "project_name": project.name,
        "project_description": project.description or "",
        "project_type": project.project_type or "Mixed-Use",
        "location_city": project.location_city or "",
        "location_district": project.location_district or "",
        
        # Building specifications
        "num_floors": project.num_floors or 10,
        "building_height": float(project.building_height) if project.building_height else 30.0,
        "site_area_m2": float(project.site_area_m2) if project.site_area_m2 else 10000.0,
        "building_coverage": float(project.building_coverage) if project.building_coverage else 40.0,
        "floor_area_ratio": float(project.floor_area_ratio) if project.floor_area_ratio else 2.0,
        
        # Zoning distribution (CRITICAL for realistic cities)
        "residential_percentage": float(project.residential_percentage) if project.residential_percentage else 40.0,
        "commercial_percentage": float(project.commercial_percentage) if project.commercial_percentage else 30.0,
        "industrial_percentage": float(project.industrial_percentage) if project.industrial_percentage else 10.0,
        "green_space_percentage": float(project.green_space_percentage_plan) if project.green_space_percentage_plan else 20.0,
        
        # Road network specifications
        "road_network_type": project.road_network_type or "Grid",
        "main_road_width": float(project.main_road_width) if project.main_road_width else 8.0,
        "secondary_road_width": float(project.secondary_road_width) if project.secondary_road_width else 6.0,
        "pedestrian_path_width": float(project.pedestrian_path_width) if project.pedestrian_path_width else 2.0,
        
        # Population and density
        "target_population": project.target_population or 5000,
        "population_density": float(project.population_density) if project.population_density else 100.0,
        "average_household_size": float(project.average_household_size) if project.average_household_size else 3.0,
        
        # Parking and infrastructure
        "parking_spaces": project.parking_spaces or 50,
        "open_space_percentage": float(project.open_space_percentage) if project.open_space_percentage else 15.0,
        
        # Sustainability features
        "climate_zone": project.climate_zone or "Temperate",
        "sustainability_rating": project.sustainability_rating or "Standard",
        "renewable_energy_target": float(project.renewable_energy_target) if project.renewable_energy_target else 0.0,
    }
    
    print("\n" + "="*60)
    print(f"HYBRID CITY GENERATION - Project {project_id}")
    print("="*60)
    print(f"Mode: {'AI-Enhanced' if request.enable_ai_enhancement else 'Blender Only'}")
    print(f"Grid Size: {request.grid_size}x{request.grid_size}")
    if request.enable_ai_enhancement and replicate_service:
        print(f"Enhancement Strength: {request.enhancement_strength * 100}%")
        print(f"Number of Views: {request.num_views}")
        estimated_cost = replicate_service.estimate_cost(request.num_views, 'sdxl')
        print(f"Estimated Cost: ${estimated_cost:.4f} USD")
    print("="*60 + "\n")
    
    try:
        # STAGE 1: Generate 3D geometry with Blender
        blender_path = "/opt/homebrew/bin/blender"
        script_path = Path(__file__).parent.parent.parent / "blender_scripts" / "generate_city.py"
        
        params_json = json.dumps(city_params)
        
        print(f"Stage 1: Running Blender city generation...")
        result = subprocess.run(
            [
                blender_path,
                "--background",
                "--python", str(script_path),
                "--", params_json
            ],
            capture_output=True,
            text=True,
            timeout=1200
        )
        
        if result.returncode != 0:
            print(f"✗ Blender generation failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
            raise HTTPException(status_code=500, detail="Blender city generation failed")
        
        if not glb_path.exists():
            raise HTTPException(status_code=500, detail="City GLB file was not created")
        
        file_size = glb_path.stat().st_size
        print(f"✓ Blender generation complete: {file_size / (1024*1024):.2f} MB")
        
        # Update project with model URL
        project.model_url = f"/storage/3d_models/{project_id}/city.glb"
        db.commit()
        db.refresh(project)
        
        # STAGE 2: Render Multiple Views (if AI enhancement enabled)
        enhanced_renders = []
        if request.enable_ai_enhancement and replicate_service and replicate_service.is_available():
            print(f"\nStage 2: Rendering multiple camera views...")
            print(f"Number of views: {request.num_views}")
            
            try:
                # Create renders directory
                renders_dir = output_dir / "renders"
                renders_dir.mkdir(exist_ok=True)
                
                # Prepare rendering parameters
                render_params = {
                    'glb_path': str(glb_path),
                    'output_dir': str(renders_dir),
                    'num_views': request.num_views
                }
                
                render_params_json = json.dumps(render_params)
                
                # Run Blender rendering script
                render_script = Path(__file__).parent.parent.parent / "blender_scripts" / "render_city_views.py"
                
                print(f"Running Blender to render {request.num_views} views...")
                render_result = subprocess.run(
                    [
                        blender_path,
                        "--background",
                        "--python", str(render_script),
                        "--", render_params_json
                    ],
                    capture_output=True,
                    text=True,
                    timeout=900  # 15 minute timeout for rendering (increased from 5 min)
                )
                
                print(f"Blender rendering completed with return code: {render_result.returncode}")
                if render_result.stdout:
                    print(f"Rendering stdout:\n{render_result.stdout}")
                if render_result.stderr:
                    print(f"Rendering stderr:\n{render_result.stderr}")
                
                if render_result.returncode == 0:

                    # Read manifest to get rendered files
                    manifest_path = renders_dir / "manifest.json"
                    if manifest_path.exists():
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            rendered_files = manifest.get('rendered_files', [])
                        
                        print(f"✓ {len(rendered_files)} views rendered successfully")
                        
                        # STAGE 3: AI Enhancement with Replicate
                        print(f"\nStage 3: Enhancing views with Replicate AI...")
                        print(f"Enhancement strength: {request.enhancement_strength * 100}%")
                        
                        # Generate prompt based on project type
                        project_type = project.project_type or "Mixed-Use"
                        base_prompt = f"photorealistic aerial view of modern {project_type.lower()} city district, detailed buildings, realistic lighting, professional architecture photography, 8k, ultra detailed"
                        
                        for i, render_file in enumerate(rendered_files):
                            print(f"  Enhancing view {i+1}/{len(rendered_files)}...")
                            
                            try:
                                # Enhance with Replicate (use await, not asyncio.run)
                                enhanced_path = await replicate_service.enhance_city_render(
                                    input_image_path=render_file,
                                    prompt=base_prompt,
                                    strength=request.enhancement_strength
                                )
                                
                                if enhanced_path:
                                    enhanced_renders.append({
                                        'view_name': f'view_{i+1}',
                                        'original': render_file,
                                        'enhanced': enhanced_path,
                                        'status': 'completed'
                                    })
                                    print(f"    ✓ View {i+1} enhanced")
                                else:
                                    enhanced_renders.append({
                                        'view_name': f'view_{i+1}',
                                        'original': render_file,
                                        'enhanced': None,
                                        'status': 'failed'
                                    })
                                    
                            except Exception as e:
                                print(f"    ✗ Error enhancing view {i+1}: {e}")
                                enhanced_renders.append({
                                    'view_name': f'view_{i+1}',
                                    'original': render_file,
                                    'enhanced': None,
                                    'status': 'error'
                                })
                        
                        print(f"\n✓ AI enhancement complete! Enhanced {len([r for r in enhanced_renders if r['status'] == 'completed'])}/{len(enhanced_renders)} views")
                        
            except Exception as e:
                print(f"⚠ Error during rendering/enhancement: {e}")
                enhanced_renders = []
        
        # Save enhanced renders metadata to database for persistence
        if enhanced_renders:
            project.enhanced_renders_metadata = enhanced_renders
            db.commit()
            db.refresh(project)
            print(f"✓ Saved {len(enhanced_renders)} enhanced renders to database")
        
        return {
            "status": "completed",
            "message": "Hybrid city generation completed" + (f" with {len(enhanced_renders)} AI-enhanced views" if enhanced_renders else ""),
            "model_url": project.model_url,
            "file_size": file_size,
            "grid_size": request.grid_size,
            "project_id": project_id,
            "ai_enhanced": len(enhanced_renders) > 0,
            "enhanced_renders": enhanced_renders
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="City generation timed out")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Hybrid city generation failed: {str(e)}")



# ============================================================================
# 2D Drawing to 3D House Model Generation Endpoints
# ============================================================================

@router.post("/{project_id}/house/upload-drawing")
async def upload_2d_drawing(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a 2D drawing (PDF or DWG) and extract building information.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate file type
    file_extension = Path(file.filename).suffix.lower()
    allowed_extensions = ['.pdf', '.dwg', '.dxf']
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    upload_dir = Path("storage/drawings") / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"drawing_{uuid.uuid4()}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the drawing file
        drawing_service = get_drawing_service()
        extracted_data = drawing_service.process_drawing_file(
            file_path=file_path,
            file_type=file_extension.lstrip('.'),
            project_id=project_id
        )
        
        return {
            "success": True,
            "message": "2D drawing uploaded and processed successfully",
            "file_path": str(file_path),
            "file_type": file_extension,
            "extracted_data": extracted_data
        }
        
    except Exception as e:
        # Clean up file if processing failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process drawing: {str(e)}")


@router.post("/{project_id}/house/generate-from-drawing")
async def generate_house_from_drawing(
    project_id: int,
    extracted_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a 3D house model from extracted 2D drawing data.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Generate 3D model from drawing
        drawing_service = get_drawing_service()
        result = drawing_service.generate_3d_model_from_drawing(
            extracted_data=extracted_data,
            project_id=project_id
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Generation failed"))
        
        # Update project with house model URL
        model_url = result.get("model_url")
        if model_url:
            project.model_url = model_url
            db.commit()
            db.refresh(project)
        
        return {
            "success": True,
            "message": "3D house model generated successfully from 2D drawing",
            "model_url": result.get("model_url"),
            "building_params": result.get("building_params"),
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate 3D model: {str(e)}")


@router.post("/{project_id}/house/validate-uda")
async def validate_house_uda_regulations(
    project_id: int,
    building_data: dict,
    plot_data: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate a house design against UDA building regulations.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Validate against UDA regulations
        uda_validator = get_uda_validator()
        validation_report = uda_validator.validate_house_design(
            building_data=building_data,
            plot_data=plot_data
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "validation_report": validation_report,
            "message": f"UDA validation completed - {'Compliant' if validation_report['is_compliant'] else 'Non-compliant'}"
        }
        
        # Save report to database
        db_report = ValidationReport(
            project_id=project_id,
            report_type=ReportType.UDA_COMPLIANCE,
            is_compliant=validation_report['is_compliant'],
            compliance_score=validation_report['compliance_score'],
            rule_checks=validation_report['passed_checks'] + validation_report['violations'] + validation_report['warnings'],
            recommendations=validation_report['recommendations'],
            generated_by=current_user.id
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        return {
            "success": True,
            "project_id": project_id,
            "report_id": db_report.id,
            "validation_report": validation_report,
            "message": f"UDA validation completed & saved - {'Compliant' if validation_report['is_compliant'] else 'Non-compliant'}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"UDA validation failed: {str(e)}")


@router.get("/{project_id}/house/uda-regulations")
async def get_uda_regulations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get UDA house building regulations summary.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        uda_validator = get_uda_validator()
        regulations = uda_validator.get_regulations_summary()
        
        return {
            "success": True,
            "project_id": project_id,
            "regulations": regulations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch regulations: {str(e)}")


@router.get("/{project_id}/house/download")
async def download_house_model(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download generated 3D house model.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Look for house model in storage
    house_model_dir = Path("storage/house_models") / str(project_id)
    
    if not house_model_dir.exists():
        raise HTTPException(status_code=404, detail="No house model found for this project")
    
    # Find the GLB file
    glb_files = list(house_model_dir.glob("*.glb"))
    
    if not glb_files:
        raise HTTPException(status_code=404, detail="House model file not found")
    
    model_path = glb_files[0]
    
    return FileResponse(
        path=model_path,
        filename=f"house_model_{project_id}.glb",
        media_type="model/gltf-binary"
    )


# ============================================================
# ML TRAINING ENDPOINTS - Train models on 2D to 3D datasets
# ============================================================

class TrainingDataRequest(BaseModel):
    """Request to add training data to ML dataset."""
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor_area: Optional[float] = None
    style: Optional[str] = None
    description: Optional[str] = None


@router.post("/ml/dataset/add")
async def add_training_sample(
    floor_plan_image: UploadFile = File(...),
    model_3d_file: UploadFile = File(...),
    metadata: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a training sample to the ML dataset.
    Upload both 2D floor plan image and corresponding 3D model file.
    
    Args:
        floor_plan_image: 2D floor plan image (PNG/JPG)
        model_3d_file: 3D model file (GLB/OBJ)
        metadata: JSON string with additional metadata
    """
    try:
        ml_service = get_house_ml_service()
        
        # Save uploaded files temporarily
        temp_dir = Path("./storage/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save floor plan image
        floor_plan_path = temp_dir / f"fp_{uuid.uuid4()}{Path(floor_plan_image.filename).suffix}"
        with open(floor_plan_path, 'wb') as f:
            content = await floor_plan_image.read()
            f.write(content)
        
        # Save 3D model file
        model_path = temp_dir / f"model_{uuid.uuid4()}{Path(model_3d_file.filename).suffix}"
        with open(model_path, 'wb') as f:
            content = await model_3d_file.read()
            f.write(content)
        
        # Parse metadata
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except:
                meta_dict = {"description": metadata}
        
        # Add to dataset
        result = ml_service.add_training_data(
            floor_plan_image_path=floor_plan_path,
            house_3d_model_path=model_path,
            metadata=meta_dict
        )
        
        # Clean up temp files
        floor_plan_path.unlink()
        model_path.unlink()
        
        return {
            "success": True,
            "message": "Training sample added successfully",
            "sample_id": result["sample_id"],
            "dataset_info": ml_service.get_dataset_info()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add training data: {str(e)}")


@router.get("/ml/dataset/info")
async def get_dataset_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about the ML training dataset."""
    try:
        ml_service = get_house_ml_service()
        dataset_info = ml_service.get_dataset_info()
        
        return {
            "success": True,
            "dataset": dataset_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset info: {str(e)}")


class TrainModelRequest(BaseModel):
    """Request to train ML model."""
    epochs: int = 100
    batch_size: int = 16
    learning_rate: float = 0.001
    validation_split: float = 0.2


@router.post("/ml/train")
async def train_ml_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Train the ML model on the dataset.
    This trains a deep learning model to generate 3D house models from 2D floor plans.
    Training runs in background.
    """
    try:
        ml_service = get_house_ml_service()
        
        # Check dataset size
        dataset_info = ml_service.get_dataset_info()
        if dataset_info["total_samples"] < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient training data. Need at least 10 samples, got {dataset_info['total_samples']}"
            )
        
        # Start training in background
        def train_task():
            ml_service.train_model(
                epochs=request.epochs,
                batch_size=request.batch_size,
                learning_rate=request.learning_rate,
                validation_split=request.validation_split
            )
        
        background_tasks.add_task(train_task)
        
        return {
            "success": True,
            "message": "Training started in background",
            "config": {
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "learning_rate": request.learning_rate,
                "validation_split": request.validation_split,
                "training_samples": dataset_info["total_samples"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@router.get("/ml/model/info")
async def get_model_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about the trained ML model."""
    try:
        ml_service = get_house_ml_service()
        
        # Try to load current model
        model_loaded = ml_service.load_model()
        
        if not model_loaded:
            return {
                "success": True,
                "model_available": False,
                "message": "No trained model available. Please train a model first."
            }
        
        return {
            "success": True,
            "model_available": True,
            "model_metadata": ml_service.model_metadata,
            "model_info": ml_service.model
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/{project_id}/house/generate-ml")
async def generate_house_with_ml(
    project_id: int,
    floor_plan_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate 3D house model from 2D floor plan using trained ML model.
    This uses the deep learning model trained on your dataset.
    
    Args:
        project_id: Project ID
        floor_plan_image: 2D floor plan image (PNG/JPG)
    """
    try:
        # Check if project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        ml_service = get_house_ml_service()
        
        # Check if model is available
        if ml_service.model is None:
            if not ml_service.load_model():
                raise HTTPException(
                    status_code=400,
                    detail="No trained model available. Please train a model first or add training data."
                )
        
        # Save uploaded floor plan
        temp_dir = Path("./storage/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        floor_plan_path = temp_dir / f"input_{uuid.uuid4()}{Path(floor_plan_image.filename).suffix}"
        with open(floor_plan_path, 'wb') as f:
            content = await floor_plan_image.read()
            f.write(content)
        
        # Generate 3D model using ML
        output_dir = Path(f"./storage/house_models/project_{project_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "house_ml_generated.glb"
        
        result = ml_service.generate_3d_from_2d(
            floor_plan_image_path=floor_plan_path,
            output_path=output_path
        )
        
        # Clean up temp file
        floor_plan_path.unlink()
        
        return {
            "success": True,
            "message": "3D house model generated using ML",
            "model_path": str(output_path),
            "download_url": f"/api/v1/generation/{project_id}/house/download",
            "generation_info": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML generation failed: {str(e)}")


# ============================================================
# AUTO FLOOR PLAN GENERATION - For users who only have 3D images
# ============================================================

@router.post("/ml/generate-floorplan")
async def generate_floor_plan_from_3d(
    house_3d_image: UploadFile = File(...),
    floors: Optional[int] = 2,
    style: Optional[str] = "modern",
    current_user: User = Depends(get_current_user)
):
    """
    Auto-generate a floor plan from a 3D house image.
    
    This is useful when you have 3D house renders but no floor plans.
    The system will create a simplified floor plan based on:
    - Building dimensions estimated from image
    - Standard architectural layouts for the style
    - Typical room configurations
    
    Args:
        house_3d_image: 3D house render/image (PNG/JPG)
        floors: Number of floors (1-3)
        style: Architectural style (modern, traditional, contemporary)
    """
    try:
        floorplan_service = get_image_to_floorplan_service()
        
        # Save uploaded 3D image temporarily
        temp_dir = Path("./storage/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        house_path = temp_dir / f"house_3d_{uuid.uuid4()}{Path(house_3d_image.filename).suffix}"
        with open(house_path, 'wb') as f:
            content = await house_3d_image.read()
            f.write(content)
        
        # Generate floor plan
        output_path = temp_dir / f"generated_floorplan_{uuid.uuid4()}.png"
        
        result = floorplan_service.extract_floor_plan(
            house_image_path=house_path,
            output_path=output_path,
            floors=floors,
            style=style
        )
        
        # Read the generated floor plan to return
        with open(output_path, 'rb') as f:
            floorplan_data = f.read()
        
        # Save to permanent location
        output_dir = Path("./storage/generated_floorplans")
        output_dir.mkdir(parents=True, exist_ok=True)
        permanent_path = output_dir / f"floorplan_{uuid.uuid4()}.png"
        
        with open(permanent_path, 'wb') as f:
            f.write(floorplan_data)
        
        # Clean up temp files
        house_path.unlink()
        output_path.unlink()
        
        return {
            "success": True,
            "message": "Floor plan generated from 3D image",
            "floor_plan_path": str(permanent_path),
            "download_url": f"/api/v1/generation/download-floorplan/{permanent_path.name}",
            "dimensions": result.get("dimensions"),
            "style": style,
            "floors": floors,
            "note": "This is a simplified floor plan. You can now use this with the 3D image for ML training."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Floor plan generation failed: {str(e)}")


@router.get("/download-floorplan/{filename}")
async def download_generated_floorplan(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download a generated floor plan."""
    floorplan_path = Path(f"./storage/generated_floorplans/{filename}")
    
    if not floorplan_path.exists():
        raise HTTPException(status_code=404, detail="Floor plan not found")
    
    return FileResponse(
        path=floorplan_path,
        filename=filename,
        media_type="image/png"
    )


@router.post("/ml/dataset/add-with-auto-floorplan")
async def add_training_sample_auto_floorplan(
    house_3d_image: UploadFile = File(...),
    floors: Optional[int] = 2,
    style: Optional[str] = "modern",
    metadata: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add training sample with AUTO-GENERATED floor plan.
    
    Perfect for when you only have 3D house images!
    This will:
    1. Generate a floor plan from your 3D image
    2. Add both to the ML dataset
    3. Ready for training
    
    Args:
        house_3d_image: Your 3D house render (PNG/JPG)
        floors: Number of floors (estimated)
        style: House style (modern/traditional/contemporary)
        metadata: JSON string with house details
    """
    try:
        ml_service = get_house_ml_service()
        floorplan_service = get_image_to_floorplan_service()
        
        # Save uploaded 3D image temporarily
        temp_dir = Path("./storage/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        house_path = temp_dir / f"house_{uuid.uuid4()}{Path(house_3d_image.filename).suffix}"
        with open(house_path, 'wb') as f:
            content = await house_3d_image.read()
            f.write(content)
        
        # Auto-generate floor plan
        floorplan_path = temp_dir / f"auto_floorplan_{uuid.uuid4()}.png"
        
        floorplan_result = floorplan_service.extract_floor_plan(
            house_image_path=house_path,
            output_path=floorplan_path,
            floors=floors,
            style=style
        )
        
        # Parse metadata
        meta_dict = {"auto_generated_floorplan": True, "style": style, "floors": floors}
        if metadata:
            try:
                user_meta = json.loads(metadata)
                meta_dict.update(user_meta)
            except:
                meta_dict["description"] = metadata
        
        # Add to ML dataset
        result = ml_service.add_training_data(
            floor_plan_image_path=floorplan_path,
            house_3d_model_path=house_path,
            metadata=meta_dict
        )
        
        # Clean up temp files
        floorplan_path.unlink()
        house_path.unlink()
        
        return {
            "success": True,
            "message": "Training sample added with auto-generated floor plan!",
            "sample_id": result["sample_id"],
            "auto_floorplan": True,
            "floor_plan_info": floorplan_result,
            "dataset_info": ml_service.get_dataset_info(),
            "note": "Floor plan was automatically generated from your 3D image. You can train the model once you have 10+ samples."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add training data: {str(e)}")



# ============================================================================
# Text-to-City AI Generation Endpoints
# ============================================================================

class TextToCityRequest(BaseModel):
    prompt: str
    enable_ai_enhancement: bool = True
    grid_size_preset: Optional[str] = "medium"  # small (6x6), medium (8x8), large (10x10)


@router.post("/{project_id}/text-to-city")
async def generate_text_to_city_layout(
    project_id: int,
    request: TextToCityRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a city layout based on a natural language text prompt.
    Uses heuristic NLP to map "intent" to engineering parameters.
    """
    prompt = request.prompt.lower()
    
    # 1. Start with default parameters (Balanced/Mixed-Use)
    # Note: We must create the mapped request object
    params = HybridCityGenerationRequest(
        grid_size=10,
        block_size=30,
        road_width=6,
        # Default flags
        enable_ai_enhancement=request.enable_ai_enhancement,
        enable_vehicles=True,
        enable_street_lights=True,
        enable_advanced_details=True,
        num_views=4
    )
    
    # 2. Apply Grid Size Preset (if provided by user)
    # ---------------------------------------------------------
    preset_map = {
        "small": 6,   # ~2-3 min generation
        "medium": 8,  # ~4-6 min generation (default)
        "large": 10   # ~8-12 min generation
    }
    base_grid_size = preset_map.get(request.grid_size_preset, 8)
    params.grid_size = base_grid_size
    
    # 3. Heuristic "AI" Mapping Logic (can override preset)
    # ---------------------------------------------------------
    
    # DENSITY & SCALE
    if any(w in prompt for w in ["downtown", "metropolis", "dense", "high-rise", "city center", "skyscraper"]):
        params.grid_size = 8       # Reduced from 12 for faster generation
        params.block_size = 40
        params.road_width = 10     # Wider roads for traffic
        
    elif any(w in prompt for w in ["suburb", "village", "town", "quiet", "low density", "residential"]):
        params.grid_size = 6
        params.block_size = 50     # Larger blocks/lots
        params.road_width = 8      # Moderate roads
        params.vehicle_spacing = 50 # Fewer cars
        
    # NATURE & GREENERY
    if any(w in prompt for w in ["eco", "green", "forest", "nature", "park", "garden", "sustainable"]):
        params.tree_spacing = 4    # Very dense trees
        
    elif any(w in prompt for w in ["industrial", "factory", "warehouse", "concrete", "grey"]):
        params.tree_spacing = 20   # Sparse trees
    
    # INFRASTRUCTURE
    if any(w in prompt for w in ["pedestrian", "walkable", "car-free"]):
        params.road_width = 3      # Tiny roads
        params.enable_vehicles = False
        params.enable_crosswalks = True
        
    elif any(w in prompt for w in ["highway", "traffic", "busy"]):
        params.road_width = 12
        params.vehicle_spacing = 10 # Traffic jam
        
    # 3. Trigger Generation
    return await generate_hybrid_city_layout(
        project_id=project_id,
        request=params,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db
    )
