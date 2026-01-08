"""
GetFloorPlan API Service

This service integrates with the GetFloorPlan AI API to generate
high-quality 3D renders and 360° virtual tours from 2D floor plans.

API Documentation: https://backend.estate.hart-digital.com/api/documentation
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


class GetFloorPlanService:
    """Service for interacting with GetFloorPlan AI API"""
    
    def __init__(self):
        self.auth_token = settings.GETFLOORPLAN_AUTH_TOKEN
        self.crm_tag_id = settings.GETFLOORPLAN_CRM_TAG_ID
        self.domain = settings.GETFLOORPLAN_DOMAIN
        self.upload_endpoint = f"{self.domain}/api/external/v1/plans/upload"
        self.check_endpoint = f"{self.domain}/api/external/v1/plans/check"
        
        # Default request headers
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
    
    async def upload_floorplan(
        self,
        file_path: str,
        use_3d: bool = True,
        language: str = "en"
    ) -> Optional[int]:
        """
        Upload a floor plan to GetFloorPlan API for processing.
        
        Args:
            file_path: Path to the floor plan image (PNG, JPG, etc.)
            use_3d: Whether to generate 3D renders and 360° tours (default: True)
            language: Language for generated content (default: "en")
        
        Returns:
            CRM Plan ID if successful, None otherwise
        """
        try:
            logger.info(f"Uploading floor plan to GetFloorPlan API: {file_path}")
            
            # Read file content into memory first
            file_content = None
            file_name = Path(file_path).name
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            logger.info(f"Read {len(file_content)} bytes from {file_name}")
            
            # Prepare multipart form data
            files = {
                'plan': (file_name, file_content, 'image/jpeg')
            }
            
            data = {
                'use_3d': '1' if use_3d else '0',
                'crm_tag_id': str(self.crm_tag_id)
            }
            
            # Use longer timeout for large file uploads (120 seconds)
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Sending POST request to {self.upload_endpoint}")
                response = await client.post(
                    self.upload_endpoint,
                    headers=self.headers,
                    files=files,
                    data=data
                )
                
                logger.info(f"Upload response status: {response.status_code}")
                
                if response.status_code == 200:
                    # API returns integer CRM Plan ID
                    plan_id = response.json()
                    logger.info(f"Floor plan uploaded successfully. CRM Plan ID: {plan_id}")
                    return plan_id
                else:
                    logger.error(f"Upload failed with status {response.status_code}: {response.text}")
                    return None
        
        except httpx.TimeoutException as e:
            logger.error(f"Upload timed out: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error uploading floor plan: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def check_plan_status(
        self,
        plan_ids: List[int],
        language: str = "en"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Check the processing status of one or more floor plans.
        
        Args:
            plan_ids: List of CRM Plan IDs to check
            language: Language for results (default: "en")
        
        Returns:
            List of plan results with status and generated assets:
            - status: 0 = not ready, 1 = ready
            - svg: List of SVG file URLs
            - jpg: List of JPG file URLs
            - widgetLink: Interactive 360° tour widget link
            - neuralJson: Neural network processing data
            - furnitureJson: Furniture placement data
            - unreal3d: Unreal Engine 3D assets
            - canvas: Canvas data
        """
        try:
            logger.info(f"Checking status for plan IDs: {plan_ids}")
            
            payload = {
                "planIds": plan_ids,
                "language": language
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.check_endpoint,
                    headers={**self.headers, "Content-Type": "application/json"},
                    json=payload
                )
                
                if response.status_code == 200:
                    results = response.json()
                    logger.info(f"Retrieved status for {len(results)} plans")
                    return results
                else:
                    logger.error(f"Status check failed with status {response.status_code}: {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Error checking plan status: {str(e)}")
            return None
    
    async def wait_for_plan_completion(
        self,
        plan_id: int,
        max_wait_time: int = 7200,  # 2 hours default
        poll_interval: int = 120,  # 2 minutes polling
        language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Poll the API until a plan is ready or timeout occurs.
        
        Args:
            plan_id: CRM Plan ID to monitor
            max_wait_time: Maximum time to wait in seconds (default: 2 hours)
            poll_interval: Polling interval in seconds (default: 2 minutes)
            language: Language for results
        
        Returns:
            Plan result data when ready, or None if timeout/error
        """
        elapsed_time = 0
        
        logger.info(f"Waiting for plan {plan_id} to complete (max {max_wait_time}s)...")
        
        while elapsed_time < max_wait_time:
            results = await self.check_plan_status([plan_id], language)
            
            if results and len(results) > 0:
                result = results[0]
                
                # Check if plan is ready (status = 1)
                if result.get('status') == 1:
                    logger.info(f"Plan {plan_id} is ready!")
                    return result
                elif result.get('status') == 0:
                    logger.info(f"Plan {plan_id} not ready yet. Waiting {poll_interval}s...")
                else:
                    logger.warning(f"Unknown status for plan {plan_id}: {result.get('status')}")
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval
        
        logger.error(f"Timeout waiting for plan {plan_id} after {max_wait_time}s")
        return None
    
    async def get_360_tour_url(
        self,
        plan_id: int,
        wait: bool = True,
        language: str = "en"
    ) -> Optional[str]:
        """
        Get the 360° virtual tour widget link for a floor plan.
        
        Args:
            plan_id: CRM Plan ID
            wait: Whether to wait for plan completion (default: True)
            language: Language for tour
        
        Returns:
            Widget link URL for 360° tour, or None if not ready
        """
        try:
            if wait:
                result = await self.wait_for_plan_completion(plan_id, language=language)
            else:
                results = await self.check_plan_status([plan_id], language)
                result = results[0] if results and len(results) > 0 else None
            
            if result and result.get('status') == 1:
                widget_link = result.get('widgetLink')
                logger.info(f"360° tour widget link: {widget_link}")
                return widget_link
            else:
                logger.warning(f"Plan {plan_id} not ready or no widget link available")
                return None
        
        except Exception as e:
            logger.error(f"Error getting 360° tour URL: {str(e)}")
            return None
    
    async def get_rendered_images(
        self,
        plan_id: int,
        wait: bool = True,
        language: str = "en"
    ) -> Dict[str, List[str]]:
        """
        Get all rendered image URLs for a floor plan.
        
        Args:
            plan_id: CRM Plan ID
            wait: Whether to wait for plan completion (default: True)
            language: Language for content
        
        Returns:
            Dictionary with 'svg' and 'jpg' lists of URLs
        """
        try:
            if wait:
                result = await self.wait_for_plan_completion(plan_id, language=language)
            else:
                results = await self.check_plan_status([plan_id], language)
                result = results[0] if results and len(results) > 0 else None
            
            if result and result.get('status') == 1:
                return {
                    'svg': result.get('svg', []),
                    'jpg': result.get('jpg', []),
                    'unreal3d': result.get('unreal3d', [])
                }
            else:
                logger.warning(f"Plan {plan_id} not ready")
                return {'svg': [], 'jpg': [], 'unreal3d': []}
        
        except Exception as e:
            logger.error(f"Error getting rendered images: {str(e)}")
            return {'svg': [], 'jpg': [], 'unreal3d': []}
    
    async def get_full_plan_data(
        self,
        plan_id: int,
        wait: bool = True,
        language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete plan data including all generated assets.
        
        Args:
            plan_id: CRM Plan ID
            wait: Whether to wait for plan completion (default: True)
            language: Language for content
        
        Returns:
            Complete plan data dictionary or None
        """
        try:
            if wait:
                return await self.wait_for_plan_completion(plan_id, language=language)
            else:
                results = await self.check_plan_status([plan_id], language)
                return results[0] if results and len(results) > 0 else None
        
        except Exception as e:
            logger.error(f"Error getting full plan data: {str(e)}")
            return None


# Global service instance
getfloorplan_service = GetFloorPlanService()
