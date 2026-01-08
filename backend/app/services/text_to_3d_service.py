"""
Text-to-3D House Generation Service for Meshy
"""
from typing import Dict, Any
import logging
import requests
import os
import time

logger = logging.getLogger(__name__)

class MeshyTextTo3DService:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.meshy_api_key = os.getenv("MESHY_API_KEY", "")
        self.meshy_text_api_url = "https://api.meshy.ai/openapi/v2/text-to-3d"
        if self.meshy_api_key:
            logger.info("Meshy Text-to-3D API enabled.")

    def generate_3d_from_prompt(self, prompt: str, output_dir: str = "./storage/generated_3d_models") -> Dict[str, Any]:
        if not self.meshy_api_key:
            raise ValueError("No Meshy API key configured")
        
        headers = {
            'Authorization': f'Bearer {self.meshy_api_key}',
            'Content-Type': 'application/json'
        }
        
        # --- Stage 1: Preview ---
        # Enhance prompt for better architectural results
        enhanced_prompt = f"{prompt}, architectural visualization, high quality, 8k resolution, photorealistic, PBR materials, unreal engine 5 render, sharp details"
        negative_prompt = "low quality, low resolution, blurry, distorted, messy, artifacts, deformed, ugly, bad geometry"
        
        preview_payload = {
            'mode': 'preview',
            'prompt': enhanced_prompt,
            'negative_prompt': negative_prompt,
            'art_style': 'realistic',
            'ai_model': 'latest', # Upgrade to Meshy-6 (latest)
            'topology': 'quad',
            'target_polycount': 30000,
            'should_remesh': True # Enable smart remeshing for better topology
        }
        
        logger.info(f"Starting Meshy v2 text-to-3d PREVIEW for prompt: {enhanced_prompt}")
        response = requests.post(self.meshy_text_api_url, headers=headers, json=preview_payload)
        
        if response.status_code not in (200, 201, 202):
            logger.error(f"Meshy Preview API error: {response.status_code} - {response.text}")
            return {"success": False, "reason": f"Preview API error: {response.status_code} - {response.text}"}
            
        preview_task_id = response.json().get('result')
        if not preview_task_id:
            return {"success": False, "reason": "No preview task ID received"}
            
        logger.info(f"Preview task {preview_task_id} created. Waiting for completion...")
        
        # Poll for Preview completion (Increased timeout for Meshy-6)
        if not self._poll_task(preview_task_id, headers, max_wait=300, context="Preview"):
             return {"success": False, "reason": "Preview generation timed out"}
             
        logger.info(f"Preview task {preview_task_id} completed. Starting refinement...")
        
        # --- Stage 2: Refine ---
        refine_payload = {
            'mode': 'refine',
            'preview_task_id': preview_task_id,
            'texture_richness': 'high' 
        }
        
        response = requests.post(self.meshy_text_api_url, headers=headers, json=refine_payload)
        
        if response.status_code not in (200, 201, 202):
            logger.error(f"Meshy Refine API error: {response.status_code} - {response.text}")
            return {"success": False, "reason": f"Refine API error: {response.status_code} - {response.text}"}
            
        refine_task_id = response.json().get('result')
        if not refine_task_id:
             return {"success": False, "reason": "No refine task ID received"}
             
        logger.info(f"Refine task {refine_task_id} created. Waiting for completion...")
        
        # Poll for Refine completion (Increased timeout)
        final_status = self._poll_task(refine_task_id, headers, max_wait=600, context="Refine", return_result=True)
        
        if not final_status:
            return {"success": False, "reason": "Refine generation timed out"}
            
        # --- Download Final Model ---
        model_urls = final_status.get('model_urls', {})
        glb_url = model_urls.get('glb')
        
        if not glb_url:
            logger.error(f"No GLB URL in response. Available URLs: {model_urls.keys()}")
            return {"success": False, "reason": "No GLB URL in refine response"}
            
        logger.info(f"Downloading refined model from {glb_url}")
        
        try:
            model_response = requests.get(glb_url, timeout=120)
            
            if model_response.status_code != 200:
                logger.error(f"Failed to download GLB: HTTP {model_response.status_code}")
                return {"success": False, "reason": f"Failed to download refined model: HTTP {model_response.status_code}"}
            
            content_length = len(model_response.content)
            logger.info(f"Downloaded model size: {content_length} bytes ({content_length / 1024:.2f} KB)")
            
            if content_length < 1000:  # Less than 1KB is suspicious
                logger.warning(f"Downloaded file is suspiciously small: {content_length} bytes")
                logger.warning(f"Response content: {model_response.content[:500]}")
            
            os.makedirs(output_dir, exist_ok=True)
            filename = f"meshy_text_refined_{refine_task_id}.glb"
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'wb') as f:
                f.write(model_response.content)
            
            # Verify file was written
            file_size = os.path.getsize(output_path)
            logger.info(f"Refined model saved to {output_path} (verified: {file_size} bytes)")
            
            # Web-accessible URL - use absolute path for backend server
            clean_dir = output_dir.lstrip("./")
            model_url = f"http://localhost:8000/{clean_dir}/{filename}"
            
            return {
                "success": True,
                "model_path": output_path,
                "model_url": model_url,
                "method": "meshy_text_to_3d_v2_refined",
                "task_id": refine_task_id,
                "model_size": content_length,
                "thumbnail_url": final_status.get('thumbnail_url')
            }
        except Exception as e:
            logger.error(f"Error downloading/saving GLB file: {e}")
            return {"success": False, "reason": f"Download error: {str(e)}"}

    def _poll_task(self, task_id: str, headers: Dict, max_wait: int, context: str, return_result: bool = False):
        start_time = time.time()
        while (time.time() - start_time) < max_wait:
            try:
                response = requests.get(f"{self.meshy_text_api_url}/{task_id}", headers=headers)
                if response.status_code != 200:
                    logger.warning(f"{context} task polling failed: {response.status_code}")
                    time.sleep(5)
                    continue
                    
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', 0)
                
                logger.info(f"[{context}] Task {task_id}: {status} - {progress}%")
                
                if status == 'SUCCEEDED':
                    return data if return_result else True
                elif status == 'FAILED':
                    error = data.get('task_error', {}).get('message', 'Unknown error')
                    logger.error(f"{context} task failed: {error}")
                    return False
                    
            except Exception as e:
                logger.error(f"Polling error: {e}")
                
            time.sleep(5)
            
        logger.error(f"{context} task timed out after {max_wait}s")
        return False
