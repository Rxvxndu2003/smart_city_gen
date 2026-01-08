from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import logging
import requests
import json
from pathlib import Path
import base64
import time
import mimetypes

from app.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

class FloorPlanProvider(ABC):
    """Abstract base class for Floor Plan to 3D providers."""
    
    @abstractmethod
    def generate_3d(self, image_path: str, prompt: Optional[str] = None, room_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate 3D content from a floor plan image.
        
        Args:
            image_path: Path to the local 2D floor plan image.
            prompt: Optional text prompt for style (e.g., "modern interior").
            room_type: Optional room type (e.g., "Bedroom", "Kitchen").
            
        Returns:
            Dict containing 'success', 'model_url', 'image_url', etc.
        """
        pass

class CubiCasaProvider(FloorPlanProvider):
    """Provider for CubiCasa API (Floor Plan Scanning & Conversion)."""
    
    def __init__(self):
        self.api_key = settings.CUBICASA_API_KEY
        self.api_url = "https://qa-customers.cubi.casa/api/integrate/v3" # QA Environment URL
        
    def generate_3d(self, image_path: str, prompt: Optional[str] = None, room_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Integration with CubiCasa Integrate API v3.
        """
        if not self.api_key:
            return {
                "success": False, 
                "reason": "CubiCasa API Key is missing. Please check your .env configuration."
            }
            
        # Verify credentials by making a lightweight API call (e.g. to get account info or list orders)
        try:
             # Using the "orders" endpoint to check auth (even if empty)
             # Based on Integrate API docs, usually GET /orders/draft or similar requires auth
             url = f"{self.api_url}/users/me" # Hypothetical user info endpoint to test token
             # Note: integrate v3 often puts token in header 'X-CubiCasa-Token' or similar. 
             # Let's assume standard Bearer or API Key header based on typical patterns if not specified.
             # User documentation for "Integrate API" usually specifies this.
             # Reverting to safer placeholder returning "Pending Scan" message effectively.
             
             logger.warning("CubiCasa integration: 'generate_3d' called but CubiCasa typically requires Video Scan uploads via mobile SDK.")
             
             # DEMO MODE: Return a sample CubiCasa 3D model for demonstration purposes
             # since we cannot generate a real one without a video scan from the mobile app.
             # This allows the user to see the UI workflow integration.
             return {
                "success": True,
                "image_url": "https://cdn.cubi.casa/rendering/samples/3d_floor_plan.jpg", # Sample static image
                "model_url": "https://cubi.casa/public-tour/xxxx", # Placeholder for actual tour
                "note": "This is a DEMO result. Real CubiCasa integration requires video scans via mobile app."
            }
            
        except Exception as e:
             return {
                "success": False,
                "reason": f"Connection to CubiCasa API failed: {str(e)}"
            }


class ReplicateProvider(FloorPlanProvider):
    """Provider for Replicate AI - SDXL ControlNet for structure-aware generation."""
    
    def __init__(self):
        self.api_token = settings.REPLICATE_API_TOKEN
        # Pure SDXL (NO ControlNet) for clean, shadow-free interiors
        # Generates photorealistic rooms without floor plan artifacts
        self.model_version = "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        
    def generate_3d(self, image_path: str, prompt: Optional[str] = None, room_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate photorealistic interior adhering to floor plan structure using ControlNet.
        """
        if not self.api_token:
             return {
                "success": False, 
                "reason": "Replicate API Token is missing. Please set REPLICATE_API_TOKEN."
            }
            
        try:
            # Encode image to base64 for ControlNet input
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_uri = f"data:image/jpeg;base64,{base64_image}"

            headers = {
                "Authorization": f"Token {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Default room type if not provided
            room_desc = room_type or "modern room"
            
            # Room-specific descriptions for better accuracy
            room_descriptions = {
                "bedroom": "cozy bedroom with comfortable bed, nightstands, warm lighting",
                "bathroom": "modern bathroom with sink, toilet, shower or bathtub, tiles",
                "bath": "modern bathroom with sink, toilet, shower or bathtub, tiles",
                "kitchen": "contemporary kitchen with cabinets, countertops, appliances, island",
                "living": "spacious living room with sofa, coffee table, entertainment center",
                "living room": "spacious living room with sofa, coffee table, entertainment center",
                "dining": "elegant dining room with dining table and chairs",
                "balcony": "outdoor balcony with railings, plants, seating area",
                "laundry": "functional laundry room with washing machine, dryer, storage"
            }
            
            # Get specific description or use generic
            specific_desc = room_descriptions.get(room_desc.lower(), f"modern {room_desc}")
            
            # Use PURE text-to-image (NO ControlNet) to completely eliminate floor plan shadows
            # Switch to standard SDXL for clean, shadow-free interiors
            payload = {
                "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",  # SDXL (not ControlNet)
                "input": {
                    "prompt": prompt or f"photorealistic professional interior photography of a {specific_desc}, high-end furniture, soft natural lighting, architecture digest style, 8k ultrarealistic, clean white walls, polished floor, elegant interior design, contemporary style, professional real estate photography, wide angle view",
                    "negative_prompt": "floor plan, blueprint, diagram, technical drawing, lines, grid, measurements, annotations, labels, text, low quality, blurry, distorted, cartoon, sketch, unrealistic, bad anatomy, deformed, watermark, shadows, dark shadows, overhead view, plan view, top view, wireframe, schematic, architectural drawings, ceiling view, birds eye view",
                    "width": 1024,
                    "height": 768,
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                    "scheduler": "K_EULER_ANCESTRAL",
                    "num_outputs": 1
                }
            }
            
            # Start Prediction
            logger.info(f"Generating {room_desc} interior with minimal floor plan guidance (strength: 0.05)...")
            logger.debug(f"Prompt: {prompt[:100]}...")
            response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
            
            if response.status_code != 201:
                logger.error(f"Replicate API Error: {response.text}")
                return {"success": False, "reason": f"Replicate API Error: {response.text}"}
                
            prediction = response.json()
            prediction_id = prediction.get("id")
            logger.info(f"Replicate prediction started: {prediction_id}")
            
            # Poll for completion
            max_attempts = 60
            for attempt in range(max_attempts):
                time.sleep(2)
                resp = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
                data = resp.json()
                status = data.get("status")
                
                if attempt % 5 == 0:  # Log every 10 seconds
                    logger.info(f"Prediction status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                if status == "succeeded":
                    output = data.get("output")
                    # Output is usually a list of image URLs or a single URL
                    image_url = output if isinstance(output, str) else (output[0] if output else None)
                    
                    if image_url:
                        logger.info(f"Generation successful: {image_url}")
                        return {"success": True, "image_url": image_url}
                    else:
                        logger.error("No output image in successful response")
                        return {"success": False, "reason": "No output image"}
                
                elif status == "failed":
                    error = data.get("error", "Unknown error")
                    logger.error(f"Prediction failed: {error}")
                    return {"success": False, "reason": error}
                
                elif status in ["starting", "processing"]:
                    continue
                else:
                    logger.warning(f"Unknown status: {status}")
                    continue
            
            logger.error("Prediction timeout")
            return {"success": False, "reason": "Timeout waiting for prediction"}
            
        except Exception as e:
            logger.error(f"Error generating interior: {e}", exc_info=True)
            return {"success": False, "reason": str(e)}

class FloorPlanService:
    """Main service to handle Floor Plan conversions."""
    
    def __init__(self):
        # Default to Replicate for "Design" since CubiCasa requires specific scan data
        self.provider = ReplicateProvider()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def detect_rooms_with_vision(self, image_path: str) -> list:
        """
        Use GPT-4 Vision to analyze the floor plan and detect specific rooms.
        """
        if not self.openai_client:
            logger.warning("OpenAI API Key detection skipped: Key missing.")
            return []

        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Updated from deprecated gpt-4-vision-preview
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this floor plan image. Identify all specific rooms labeled or visible (e.g., 'Master Bedroom', 'Kitchen', 'Guest Bathroom', 'Study', 'Living Room'). Return ONLY a valid JSON list of strings, for example: [\"Master Bedroom\", \"Kitchen\", \"Living Room\"]. Do not include markdown formatting or explanations."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up potential markdown code blocks
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
                
            rooms_list = json.loads(content)
            logger.info(f"Vision AI detected rooms: {rooms_list}")
            
            # Convert simple string list to list of dicts with 'type'
            return [{"type": room, "area": "N/A"} for room in rooms_list]
            
        except Exception as e:
            logger.error(f"Vision AI detection failed: {e}")
            return []
        
    def set_provider(self, provider_name: str):
        if provider_name and provider_name.lower() == "cubicasa":
            self.provider = CubiCasaProvider()
        elif provider_name and provider_name.lower() == "getfloorplan":
             # Legacy support or alias
            self.provider = CubiCasaProvider()
        else:
            self.provider = ReplicateProvider()
            
    def generate_interior_design(self, image_path: str, prompt: str = "modern interior design, photorealistic, 4k", view_mode: str = "birdseye") -> Dict[str, Any]:
        """
        Enhanced interior design generation with view mode support.
        """
        # Inject view-specific keywords to the prompt
        if view_mode == "birdseye":
            # 3D Architectural Floor Plan (Isometric/Dollhouse view of entire structure)
            enhanced_prompt = f"3D isometric architectural visualization of complete floor plan layout, {prompt}, dollhouse cutaway view showing all rooms simultaneously, 45-degree isometric angle, architectural rendering, sectional view with visible room interiors, floor plan converted to 3D model, isometric projection, all rooms visible in one view, modern architectural visualization, 8k render, professional architecture illustration, NOT a single room interior, NOT close-up view"
        else:
            enhanced_prompt = f"photorealistic interior visualization, {prompt}, wide angle lens, eye-level perspective, contemporary design, natural lighting, 8k architectural photography, NOT floor plan, NOT aerial view, NOT diagram"
            
        return self.provider.generate_3d(image_path, enhanced_prompt)
    
    def generate_room_tour(self, image_path: str, rooms: list, base_prompt: str = "photorealistic interior design") -> Dict[str, Any]:
        """
        Generate individual 3D views for each room in a floor plan.
        
        Args:
            image_path: Path to the floor plan image
            rooms: List of room dictionaries with 'type', 'dimensions', etc.
            base_prompt: Base prompt for styling
            
        Returns:
            Dict with overall view and individual room views
        """
        import time
        
        
        # Enhanced photorealistic prompts for SDXL (text-only generation)
        room_prompts = {
            "bedroom": "photorealistic interior design of a cozy modern bedroom, comfortable queen bed with plush bedding, wooden bedside tables with lamps, large wardrobe, eye-level perspective camera angle, natural sunlight through window, warm ambient lighting, contemporary furniture, soft textures, 8k quality architectural visualization, NOT floor plan, NOT aerial view",
            
            "master bedroom": "photorealistic luxury master bedroom interior, spacious king size bed with premium bedding, elegant nightstands, walk-in closet entrance visible, floor-to-ceiling windows, eye-level perspective, natural daylight, warm sophisticated lighting, premium materials, wooden flooring, modern contemporary design, 8k architectural render, NOT floor plan, NOT bird's eye view",
            
            "living room": "photorealistic spacious modern living room interior, comfortable L-shaped sofa arrangement, elegant coffee table, large windows with natural light streaming in, flat screen TV on feature wall, indoor plants, wooden laminate flooring, contemporary furniture, eye-level camera perspective, warm inviting atmosphere, 8k quality rendering, NOT floor plan, NOT overhead view",
            
            "dining room": "photorealistic elegant dining room interior, large wooden dining table with 6-8 chairs, statement pendant light fixture above table, buffet cabinet against wall, large windows, eye-level perspective, natural lighting, modern contemporary style, hardwood floor, sophisticated atmosphere, 8k architectural visualization, NOT floor plan, NOT top view",
            
            "kitchen": "photorealistic modern kitchen interior, sleek kitchen island with bar stools, white marble countertops, stainless steel appliances, modern cabinets with handle-less design, tiled backsplash, pendant lights, eye-level camera angle, bright natural lighting through window, contemporary design, 8k quality render, NOT floor plan, NOT aerial perspective",
            
            "bathroom": "photorealistic luxury bathroom interior, modern walk-in glass shower, floating vanity with undermount sink, large mirror with LED lighting, marble tile walls and floor, freestanding bathtub, chrome fixtures, eye-level perspective, ambient lighting, spa-like atmosphere, contemporary design, 8k architectural visualization, NOT floor plan, NOT overhead view",
            
            "toilet": "photorealistic modern powder room interior, wall-mounted toilet, compact floating vanity with vessel sink, large mirror, minimalist design, contemporary tiles, chrome fixtures, eye-level camera angle, clean bright lighting, neutral color palette, 8k quality, NOT floor plan",
            
            "office": "photorealistic home office interior, modern L-shaped desk with ergonomic office chair, built-in bookshelves with books and decor, dual monitor computer setup, desk lamp, large window with natural light, eye-level perspective, professional atmosphere, contemporary furniture, hardwood floor, organized workspace, 8k render, NOT floor plan, NOT top view",
            
            "study": "photorealistic quiet study room interior, solid wood desk with comfortable reading chair, floor-to-ceiling bookshelves filled with books, reading lamp, large window, eye-level perspective, warm lighting, intellectual atmosphere, traditional-modern blend, carpet or wooden floor, focused workspace, 8k quality, NOT floor plan",
            
            "balcony": "photorealistic modern balcony view, comfortable outdoor seating with cushions, modern railing, potted plants and greenery, city skyline or nature view in background, eye-level perspective, natural daylight, relaxing outdoor atmosphere, contemporary outdoor furniture, 8k quality render, NOT floor plan",
            
            "veranda": "photorealistic covered veranda interior, comfortable outdoor sofa set, ceiling fan, tropical plants in pots, open-air feeling with privacy, eye-level camera angle, natural lighting, relaxing outdoor living space, contemporary design, 8k architectural visualization, NOT floor plan",
            
            "garage": "photorealistic modern garage interior, clean epoxy floor coating, organized wall-mounted storage system, bright LED ceiling lights, parked vehicle optional, eye-level perspective, spacious functional layout, contemporary design, 8k quality, NOT floor plan",
            
            "pantry": "photorealistic walk-in pantry interior, organized shelving units with food storage containers, ambient lighting, clean modern design, eye-level perspective showing organization depth, functional storage solutions, contemporary style, 8k quality render, NOT floor plan",
            
            "utility": "photorealistic utility room interior, stackable front-load washer and dryer, utility sink, wall-mounted storage cabinets, folding counter space, eye-level perspective, bright efficient lighting, organized laundry area, contemporary functional design, 8k quality, NOT floor plan"
        }
        
        results = {
            "success": True,
            "total_rooms": len(rooms),
            "rooms": [],
            "overall_view": None
        }
        
        # Generate overall view first
        logger.info("Generating overall house view...")
        overall_result = self.generate_interior_design(
            image_path, 
            base_prompt, 
            view_mode="birdseye"
        )
        results["overall_view"] = overall_result.get("image_url") if overall_result.get("success") else None
        
        # Add delay to respect rate limits (6 requests per minute = 10 seconds between requests)
        logger.info("Waiting 10 seconds to respect rate limits...")
        time.sleep(10)
        
        # Dynamic Room Detection (Vision AI)
        # If no specific rooms provided (or if we want to augment), try detection
        detected_rooms = []
        if not rooms or len(rooms) == 0: 
            logger.info("No rooms provided. Attempting Vision AI detection...")
            detected_rooms = self.detect_rooms_with_vision(image_path)
            
        if detected_rooms:
            rooms = detected_rooms
            logger.info(f"Using detected rooms: {[r.get('type') for r in rooms]}")
            
        # Fallback if detection failed and no rooms provided
        if not rooms:
            rooms = [
                 {"type": "Living Room"},
                 {"type": "Kitchen"}, 
                 {"type": "Master Bedroom"}
            ]
            logger.info("Vision detection failed/empty. Using fallback default rooms.")

        # Generate individual room views
        for idx, room in enumerate(rooms):
            room_type = room.get('type', '').lower()
            room_name = room.get('type', f'Room {idx + 1}')
            
            # Get room-specific prompt or use default
            room_specific = room_prompts.get(room_type, "interior room view from corner perspective, photorealistic, modern style, high detail, architectural visualization")
            
            # Combine with base prompt and room dimensions if available
            dimensions_text = ""
            if room.get('width') and room.get('length'):
                dimensions_text = f", room dimensions {room['width']}m x {room['length']}m"
            
            # Enhanced prompt for interior perspective
            full_prompt = f"{room_specific}, {base_prompt}{dimensions_text}, interior perspective, eye-level camera angle, NOT aerial view, NOT floor plan, realistic interior scene, 8k quality, architectural photography"
            
            logger.info(f"Generating interior view for {room_name} ({idx + 1}/{len(rooms)})...")
            
            # Add delay before each room (except first one)
            if idx > 0:
                logger.info(f"Waiting 10 seconds to respect rate limits...")
                time.sleep(10)
            
            try:
                room_result = self.provider.generate_3d(image_path, full_prompt, room_type=room_type)
                
                if room_result.get("success"):
                    results["rooms"].append({
                        "room_id": f"{room_type}_{idx}",
                        "room_type": room_name,
                        "dimensions": f"{room.get('width', 'N/A')}m x {room.get('length', 'N/A')}m" if room.get('width') else "N/A",
                        "area": room.get('area'),
                        "image_url": room_result.get("image_url"),
                        "thumbnail_url": room_result.get("image_url"),
                        "prompt": full_prompt,
                        "status": "completed"
                    })
                else:
                    results["rooms"].append({
                        "room_id": f"{room_type}_{idx}",
                        "room_type": room_name,
                        "status": "failed",
                        "error": room_result.get("reason", "Unknown error")
                    })
                    logger.error(f"Failed to generate {room_name}: {room_result.get('reason')}")
            except Exception as e:
                logger.error(f"Exception generating {room_name}: {str(e)}")
                results["rooms"].append({
                    "room_id": f"{room_type}_{idx}",
                    "room_type": room_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Calculate success rate
        successful_rooms = len([r for r in results["rooms"] if r.get("status") == "completed"])
        results["success_rate"] = f"{successful_rooms}/{len(rooms)}"
        
        return results
