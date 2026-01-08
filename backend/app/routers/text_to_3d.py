from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.blender_house_service import BlenderHouseService
from typing import Dict
import logging

router = APIRouter()

# Debug endpoint to echo request body
@router.post("/text-to-3d-debug")
async def echo_text_to_3d(request: Request):
    data = await request.json()
    logging.info(f"Echo endpoint received: {data}")
    return {"received": data}

class TextTo3DRequest(BaseModel):
    prompt: str

@router.post("/text-to-3d")
async def generate_3d_from_prompt(request: TextTo3DRequest) -> Dict:
    """Generate a 3D house model from a text prompt using Blender."""
    logging.info(f"Received text-to-3d request: {request.prompt}")
    try:
        service = BlenderHouseService()
        result = service.generate_from_prompt(request.prompt)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("reason", "Unknown error"))
        
        logging.info(f"✅ Blender generation successful: {result.get('model_url')}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in text-to-3d endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Server error: {str(e)}")
