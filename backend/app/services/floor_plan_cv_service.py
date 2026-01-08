"""
Computer Vision service for analyzing floor plan images.
Uses OpenCV for image processing and pytesseract for OCR.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FloorPlanCVService:
    """Advanced computer vision analysis for floor plans."""
    
    def __init__(self):
        self.min_room_area = 1000  # Minimum pixels for a valid room
        self.room_keywords = {
            'bedroom': ['bedroom', 'bed room', 'br', 'bdrm'],
            'master bedroom': ['master', 'mbr', 'master bedroom'],
            'living room': ['living', 'lounge', 'hall', 'family room'],
            'dining room': ['dining', 'dining room'],
            'kitchen': ['kitchen', 'kitchenette', 'pantry'],
            'bathroom': ['bathroom', 'bath', 'wc'],
            'toilet': ['toilet', 'powder', 'half bath'],
            'office': ['office', 'study', 'den'],
            'garage': ['garage', 'car port'],
            'balcony': ['balcony', 'terrace', 'deck'],
            'utility': ['utility', 'laundry', 'storage']
        }
    
    def analyze_floor_plan(self, image_path: str) -> Dict[str, Any]:
        """
        Main analysis function - detects rooms from floor plan image.
        
        Args:
            image_path: Path to floor plan image
            
        Returns:
            Dictionary with detected rooms and metadata
        """
        try:
            # Load and preprocess image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return self._empty_result("Failed to load image")
            
            logger.info(f"Analyzing floor plan image: {image_path} ({img.shape})")
            
            # Step 1: Detect room boundaries
            room_contours = self._detect_room_boundaries(img)
            logger.info(f"Detected {len(room_contours)} potential rooms")
            
            # Step 2: Extract and classify rooms
            rooms = self._extract_rooms(img, image_path, room_contours)
            logger.info(f"Classified {len(rooms)} rooms")
            
            # Step 3: Calculate total area
            total_area = sum(r.get('area', 0) for r in rooms)
            
            return {
                'success': True,
                'rooms': rooms,
                'total_rooms': len(rooms),
                'total_area': total_area,
                'detected_at': datetime.now().isoformat(),
                'image_size': {'width': img.shape[1], 'height': img.shape[0]}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing floor plan: {e}", exc_info=True)
            return self._empty_result(str(e))
    
    def _detect_room_boundaries(self, img: np.ndarray) -> List[np.ndarray]:
        """
        Detect room boundaries using edge detection and contour finding.
        
        Args:
            img: Input image array
            
        Returns:
            List of contours representing room boundaries
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding for better results
        binary = cv2.adaptiveThreshold(
            blurred, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Morphological operations to close gaps
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(
            binary, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours by area
        valid_contours = [
            cnt for cnt in contours 
            if cv2.contourArea(cnt) > self.min_room_area
        ]
        
        # Sort by area (largest first)
        valid_contours = sorted(
            valid_contours, 
            key=lambda c: cv2.contourArea(c), 
            reverse=True
        )
        
        return valid_contours
    
    def _extract_rooms(
        self, 
        img: np.ndarray, 
        image_path: str,
        contours: List[np.ndarray]
    ) -> List[Dict[str, Any]]:
        """
        Extract room information from contours and classify using OCR.
        
        Args:
            img: Original image
            image_path: Path to image for OCR
            contours: List of room boundary contours
            
        Returns:
            List of room dictionaries
        """
        rooms = []
        
        # Try to import pytesseract for OCR
        try:
            import pytesseract
            from PIL import Image
            ocr_available = True
            pil_img = Image.open(image_path)
        except ImportError:
            logger.warning("pytesseract not available, using heuristic room detection")
            ocr_available = False
            pil_img = None
        
        for idx, contour in enumerate(contours[:15]):  # Limit to top 15 largest areas
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Try OCR if available
            room_type = "Room"
            if ocr_available and pil_img:
                try:
                    # Crop to room area with padding
                    padding = 10
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(pil_img.width, x + w + padding)
                    y2 = min(pil_img.height, y + h + padding)
                    
                    room_img = pil_img.crop((x1, y1, x2, y2))
                    
                    # Perform OCR
                    text = pytesseract.image_to_string(room_img, config='--psm 6')
                    room_type = self._classify_room_type(text)
                    
                except Exception as e:
                    logger.debug(f"OCR failed for contour {idx}: {e}")
            
            # Estimate dimensions (assuming ~10 pixels per meter as rough scale)
            pixels_per_meter = 100  # Adjust based on typical floor plan scale
            width_m = round(w / pixels_per_meter, 1)
            length_m = round(h / pixels_per_meter, 1)
            area_m2 = round(area / (pixels_per_meter ** 2), 1)
            
            rooms.append({
                'type': room_type,
                'width': width_m,
                'length': length_m,
                'area': area_m2,
                'position': {'x': int(x), 'y': int(y)},
                'bbox': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
            })
        
        # Apply heuristics to improve classification
        rooms = self._apply_heuristics(rooms)
        
        return rooms
    
    def _classify_room_type(self, ocr_text: str) -> str:
        """
        Classify room type from OCR text.
        
        Args:
            ocr_text: Text extracted from room area
            
        Returns:
            Classified room type
        """
        text_lower = ocr_text.lower()
        
        # Check for each room type
        for room_type, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return room_type.title()
        
        return "Room"
    
    def _apply_heuristics(self, rooms: List[Dict]) -> List[Dict]:
        """
        Apply heuristic rules to improve room classification.
        
        For example:
        - Largest room is likely living room
        - Small rooms (<10 m²) are likely bathrooms
        - Medium rooms (10-20 m²) are likely bedrooms
        """
        if not rooms:
            return rooms
        
        # Sort by area
        sorted_rooms = sorted(rooms, key=lambda r: r.get('area', 0), reverse=True)
        
        for idx, room in enumerate(sorted_rooms):
            if room['type'] == 'Room':
                area = room.get('area', 0)
                
                # Heuristic classification
                if idx == 0 and area > 20:
                    room['type'] = 'Living Room'
                elif area < 8:
                    room['type'] = 'Bathroom'
                elif area > 12:
                    # Default to bedroom for medium-large unidentified rooms
                    room['type'] = 'Bedroom'
        
        return sorted_rooms
    
    def _empty_result(self, error: str = None) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'success': False,
            'rooms': [],
            'total_rooms': 0,
            'total_area': 0,
            'error': error
        }
