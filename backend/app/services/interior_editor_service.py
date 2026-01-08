"""
Interior Design Editor Service
Uses InstructPix2Pix AI model to edit interior designs with natural language instructions.
"""

import logging
import requests
import time
import base64
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class InteriorEditorService:
    """Service for editing interior designs using InstructPix2Pix."""
    
    def __init__(self):
        self.api_token = settings.REPLICATE_API_TOKEN
        # InstructPix2Pix model for image editing
        self.model_version = "30c1d0b916a6f8efce20493f5d61ee27491ab2a60437c13c588468b9810ec23f"
        self.max_retries = 60  # Max polling attempts
        self.retry_delay = 2  # Seconds between polls
    
    def _image_to_data_uri(self, image_path_or_url: str) -> str:
        """Convert image file or URL to data URI."""
        # If it's a URL, download first
        if image_path_or_url.startswith('http'):
            try:
                response = requests.get(image_path_or_url, timeout=30)
                response.raise_for_status()
                
                # Guess mime type from URL
                mime_type = response.headers.get('content-type', 'image/jpeg')
                encoded_string = base64.b64encode(response.content).decode('utf-8')
                
                return f"data:{mime_type};base64,{encoded_string}"
            except Exception as e:
                logger.error(f"Failed to download image from URL: {e}")
                raise
        else:
            # It's a file path
            mime_type, _ = mimetypes.guess_type(image_path_or_url)
            if not mime_type:
                mime_type = "image/jpeg"
            
            with open(image_path_or_url, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            return f"data:{mime_type};base64,{encoded_string}"
    
    def _poll_prediction(self, prediction_id: str) -> Dict[str, Any]:
        """Poll Replicate API until prediction completes."""
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers=headers
                )
                response.raise_for_status()
                prediction = response.json()
                
                status = prediction.get("status")
                
                if status == "succeeded":
                    output = prediction.get("output")
                    if output and len(output) > 0:
                        return {
                            "success": True,
                            "image_url": output[0] if isinstance(output, list) else output
                        }
                    else:
                        return {"success": False, "reason": "No output generated"}
                
                elif status == "failed":
                    error = prediction.get("error", "Unknown error")
                    logger.error(f"Prediction failed: {error}")
                    return {"success": False, "reason": error}
                
                elif status in ["starting", "processing"]:
                    logger.debug(f"Prediction {prediction_id} still {status}... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue
                
                else:
                    logger.warning(f"Unexpected status: {status}")
                    time.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                logger.error(f"Error polling prediction: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {"success": False, "reason": str(e)}
        
        return {"success": False, "reason": "Prediction timeout"}
    
    async def edit_interior(
        self,
        image_url: str,
        instruction: str,
        guidance_scale: float = 7.5,
        image_guidance_scale: float = 1.5,
        steps: int = 50
    ) -> Dict[str, Any]:
        """
        Edit interior design with natural language instruction.
        
        Args:
            image_url: URL or path to original interior image
            instruction: Edit instruction (e.g., "change wall to blue")
            guidance_scale: Text adherence (7.5 default, higher = follow instruction more)
            image_guidance_scale: Image preservation (1.5 default, higher = keep more original)
            steps: Inference steps (50 default, higher = better quality)
            
        Returns:
            Dict with success status and edited image URL
        """
        if not self.api_token:
            return {
                "success": False,
                "reason": "Replicate API Token is missing. Please set REPLICATE_API_TOKEN."
            }
        
        try:
            logger.info(f"Editing interior with instruction: '{instruction}'")
            
            # Convert image to data URI
            image_uri = self._image_to_data_uri(image_url)
            
            # Prepare API request
            headers = {
                "Authorization": f"Token {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": self.model_version,
                "input": {
                    "image": image_uri,
                    "prompt": instruction,
                    "num_inference_steps": steps,
                    "guidance_scale": guidance_scale,
                    "image_guidance_scale": image_guidance_scale,
                    "negative_prompt": "blurry, distorted, low quality, artifacts"
                }
            }
            
            # Start prediction
            logger.info("Sending edit request to Replicate (InstructPix2Pix)...")
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 201:
                error_msg = f"Replicate API Error: {response.text}"
                logger.error(error_msg)
                return {"success": False, "reason": error_msg}
            
            prediction_data = response.json()
            prediction_id = prediction_data.get("id")
            
            if not prediction_id:
                return {"success": False, "reason": "No prediction ID returned"}
            
            logger.info(f"Prediction started: {prediction_id}")
            
            # Poll for result
            result = self._poll_prediction(prediction_id)
            
            if result.get("success"):
                logger.info(f"Edit completed successfully: {result['image_url']}")
            else:
                logger.error(f"Edit failed: {result.get('reason')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in edit_interior: {e}", exc_info=True)
            return {"success": False, "reason": str(e)}
    
    async def batch_edit(
        self,
        image_url: str,
        instructions: list[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply multiple edits sequentially.
        
        Args:
            image_url: Original image URL
            instructions: List of edit instructions
            **kwargs: Additional parameters for edit_interior
            
        Returns:
            Dict with all edit results
        """
        current_image = image_url
        edits = []
        
        for idx, instruction in enumerate(instructions):
            logger.info(f"Applying edit {idx + 1}/{len(instructions)}: {instruction}")
            
            result = await self.edit_interior(current_image, instruction, **kwargs)
            
            if result.get("success"):
                current_image = result['image_url']
                edits.append({
                    "instruction": instruction,
                    "result_url": current_image,
                    "status": "completed"
                })
            else:
                edits.append({
                    "instruction": instruction,
                    "status": "failed",
                    "error": result.get("reason")
                })
                # Stop on first failure
                break
        
        return {
            "success": len([e for e in edits if e['status'] == 'completed']) == len(instructions),
            "original_url": image_url,
            "final_url": current_image,
            "edits": edits
        }
