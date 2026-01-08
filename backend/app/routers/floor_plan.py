from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from app.services.floor_plan_service import FloorPlanService
import shutil
import os
import logging
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/floor-plan/design")
async def generate_interior_design(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("modern interior design, photorealistic, 8k, unreal engine 5"),
    provider: Optional[str] = Form("replicate"),
    view_mode: Optional[str] = Form("birdseye") # New parameter
):
    """
    Convert a 2D floor plan into a 3D Interior Design visualization.
    """
    try:
        # Save uploaded file
        upload_dir = Path("./storage/uploads/floor_plans")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        service = FloorPlanService()
        service.set_provider(provider)
        
        result = service.generate_interior_design(str(file_path), prompt, view_mode)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("reason"))
            
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in floor-plan-design: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/floor-plan/room-tour")
async def generate_room_tour(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("modern photorealistic interior"),
    provider: Optional[str] = Form("replicate")
):
    """
    Generate a complete 3D room tour with individual views for each room.
    Analyzes the floor plan and creates focused views for bedrooms, living room, kitchen, etc.
    """
    try:
        # Save uploaded file
        upload_dir = Path("./storage/uploads/floor_plans")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        
        # Generate room tour with Vision AI detection
        # Pass empty list to trigger detect_rooms_with_vision in FloorPlanService
        service = FloorPlanService()
        service.set_provider(provider)
        
        logger.info(f"Generating room tour with Vision AI detection...")
        result = service.generate_room_tour(str(file_path), [], prompt)  # Empty list triggers Vision AI
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail="Room tour generation failed")
        
        return {
            "success": True,
            "message": f"Generated views for {result['total_rooms']} rooms",
            "overall_view": result.get("overall_view"),
            "rooms": result.get("rooms", []),
            "success_rate": result.get("success_rate"),
            "metadata": {
                "total_rooms": result["total_rooms"],
                "provider": provider,
                "prompt": prompt
            }
        }
        
    except Exception as e:
        logger.error(f"Error in room-tour generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/floor-plan/room-tour-video")
async def generate_room_tour_video(
    rooms: list = Form(...),
    filename: Optional[str] = Form("room_tour.mp4")
):
    """
    Generate MP4 video from room tour data.
    Stitches individual room images into a video with transitions and labels.
    """
    from fastapi.responses import FileResponse
    from app.services.room_tour_video_service import RoomTourVideoService
    import json
    
    try:
        # Parse rooms data - FormData sends it as a string
        if isinstance(rooms, str):
            rooms_data = json.loads(rooms)
        elif isinstance(rooms, list) and len(rooms) > 0 and isinstance(rooms[0], str):
            # If it's a list with one string element (common with FormData)
            rooms_data = json.loads(rooms[0])
        else:
            rooms_data = rooms
        
        # Filter only completed rooms
        valid_rooms = [r for r in rooms_data if r.get('status') == 'completed' and r.get('image_url')]
        
        if not valid_rooms:
            raise HTTPException(status_code=400, detail="No valid room images to create video")
        
        logger.info(f"Generating video from {len(valid_rooms)} rooms")
        
        # Generate video
        video_service = RoomTourVideoService()
        video_path = await video_service.generate_video(valid_rooms, filename)
        
        # Return video file
        return FileResponse(
            str(video_path),
            media_type="video/mp4",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating room tour video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/floor-plan/edit-interior")
async def edit_interior_design(
    image_url: str = Form(...),
    instruction: str = Form(...),
    guidance_scale: float = Form(7.5),
    image_guidance_scale: float = Form(1.5),
    steps: int = Form(50)
):
    """
    Edit an interior design with natural language instruction.
    
    Example instructions:
    - "change wall color to navy blue"
    - "replace the sofa with a grey sectional"
    - "add hardwood flooring"
    - "make the room brighter"
    - "add indoor plants"
    """
    from app.services.interior_editor_service import InteriorEditorService
    
    try:
        logger.info(f"Editing interior: '{instruction}'")
        
        editor = InteriorEditorService()
        result = await editor.edit_interior(
            image_url,
            instruction,
            guidance_scale,
            image_guidance_scale,
            steps
        )
        
        return {
            "success": result.get("success"),
            "original_url": image_url,
            "edited_url": result.get("image_url"),
            "instruction": instruction,
            "reason": result.get("reason") if not result.get("success") else None
        }
        
    except Exception as e:
        logger.error(f"Error editing interior: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/floor-plan/edit-interior-batch")
async def batch_edit_interior(
    image_url: str = Form(...),
    instructions: str = Form(...)  # JSON array as string
):
    """
    Apply multiple edits sequentially.
    
    Instructions should be JSON array: ["change walls to blue", "add plants"]
    """
    from app.services.interior_editor_service import InteriorEditorService
    import json
    
    try:
        # Parse instructions
        if isinstance(instructions, str):
            instructions_list = json.loads(instructions)
        else:
            instructions_list = instructions
        
        logger.info(f"Batch editing interior with {len(instructions_list)} instructions")
        
        editor = InteriorEditorService()
        result = await editor.batch_edit(image_url, instructions_list)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch edit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/floor-plan/generate-complete")
async def generate_complete_floor_plan(
    file: UploadFile = File(...),
    include_3d_model: bool = Form(True),
    include_360_tour: bool = Form(True),
    include_2d_renders: bool = Form(True),
    prompt: Optional[str] = Form("modern photorealistic interior")
):
    """
    HYBRID APPROACH: Comprehensive floor plan generation
    
    Combines all features:
    1. Vision AI room detection (GPT-4)
    2. 3D GLB model generation (ModelsLab)
    3. 360° virtual tour (ModelsLab)
    4. 2D photorealistic room renders (ControlNet)
    
    Returns complete package for maximum visualization options
    """
    from app.services.modelslab_service import ModelsLabService
    import time
    
    try:
        start_time = time.time()
        
        # Save uploaded file
        upload_dir = Path("./storage/uploads/floor_plans")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"🚀 Starting HYBRID generation for {file.filename}")
        service = FloorPlanService()
        result = {
            "success": True,
            "timestamp": time.time(),
            "floor_plan_name": file.filename
        }
        
        # Step 1: Vision AI Room Detection
        logger.info("Step 1/4: Detecting rooms with Vision AI...")
        detected_rooms = service.detect_rooms_with_vision(str(file_path))
        result["detected_rooms"] = [room.get("type") for room in detected_rooms]
        result["total_rooms"] = len(detected_rooms)
        
        # Step 2: Generate 3D Model (ModelsLab)
        if include_3d_model:
            logger.info("Step 2/4: Generating 3D GLB model with ModelsLab...")
            modelslab = ModelsLabService()
            model_result = modelslab.generate_3d_floor_plan(
                str(file_path),
                prompt=f"3D architectural model, {prompt}, modern design",
                include_360=include_360_tour
            )
            
            if model_result.get("success"):
                result["model_3d"] = {
                    "glb_url": model_result.get("model_url"),
                    "generation_time": model_result.get("generation_time")
                }
                logger.info(f"✅ 3D Model generated: {model_result.get('model_url')}")
            else:
                result["model_3d"] = {
                    "error": model_result.get("reason"),
                    "note": "3D generation failed, but continuing with 2D"
                }
        
        
        # Step 3: Generate Virtual Walkthrough (if requested)
        if include_360_tour:
            logger.info("Step 3/4: Generating virtual walkthrough tour...")
            try:
                import replicate
                
                # Generate 4-view walkthrough sequence (entry, living, kitchen, bedroom)
                walkthrough_angles = [
                    {"view": "entrance", "prompt": f"modern house entrance foyer, {prompt}, welcoming hallway, front door visible, professional interior photography"},
                    {"view": "living_area", "prompt": f"spacious living room, {prompt}, comfortable seating, modern furniture, bright natural light"},
                    {"view": "kitchen", "prompt": f"contemporary kitchen interior, {prompt}, modern appliances, island counter, clean design"},
                    {"view": "bedroom", "prompt": f"cozy bedroom interior, {prompt}, comfortable bed, warm lighting, relaxing atmosphere"}
                ]
                
                walkthrough_views = []
                for angle in walkthrough_angles:
                    logger.info(f"Generating {angle['view']} view...")
                    view_output = replicate.run(
                        "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                        input={
                            "prompt": angle['prompt'],
                            "negative_prompt": "floor plan, blueprint, diagram, shadows, dark, low quality, blurry, distorted",
                            "width": 1024,
                            "height": 768,
                            "num_outputs": 1
                        }
                    )
                    
                    if view_output:
                        view_url = str(view_output[0]) if isinstance(view_output, list) else str(view_output)
                        walkthrough_views.append({
                            "view": angle['view'],
                            "url": view_url
                        })
                    
                    time.sleep(2)  # Rate limiting
                
                if walkthrough_views:
                    result["tour_360"] = {
                        "walkthrough_views": walkthrough_views,
                        "type": "virtual_walkthrough",
                        "total_views": len(walkthrough_views)
                    }
                    logger.info(f"✅ Virtual walkthrough generated: {len(walkthrough_views)} views")
            except Exception as e:
                logger.error(f"Walkthrough generation failed: {e}")
                logger.info("Continuing without walkthrough tour")
        
        # Step 4: Generate 2D Photorealistic Renders (ControlNet)
        if include_2d_renders:
            logger.info("Step 4/4: Generating 2D photorealistic interiors with ControlNet...")
            tour_result = service.generate_room_tour(
                str(file_path),
                detected_rooms,
                prompt
            )
            
            if tour_result.get("success"):
                result["renders_2d"] = {
                    "overall_view": tour_result.get("overall_view"),
                    "rooms": tour_result.get("rooms"),
                    "total_generated": tour_result.get("total_rooms"),
                    "success_rate": tour_result.get("success_rate")
                }
                logger.info(f"✅ Generated {tour_result.get('total_rooms')} 2D room renders")
            else:
                result["renders_2d"] = {
                    "error": "2D render generation failed"
                }
        
        # Calculate total generation time
        total_time = time.time() - start_time
        result["total_generation_time"] = round(total_time, 2)
        
        logger.info(f"🎉 HYBRID generation complete in {total_time:.2f}s")
        logger.info(f"   - Detected rooms: {len(detected_rooms)}")
        logger.info(f"   - 3D Model: {'✅' if result.get('model_3d', {}).get('glb_url') else '❌'}")
        logger.info(f"   - 360° Tour: {'✅' if result.get('tour_360') else '❌'}")
        logger.info(f"   - 2D Renders: {'✅' if result.get('renders_2d') else '❌'}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in complete floor plan generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
