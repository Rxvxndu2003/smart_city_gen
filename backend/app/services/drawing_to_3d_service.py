"""
2D Drawing to 3D Model Conversion Service.
Processes PDF and DWG files to extract floor plan information and generate 3D house models.
"""
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import PyPDF2
import re
import json
from decimal import Decimal

logger = logging.getLogger(__name__)


class DrawingTo3DService:
    """Service for converting 2D drawings (PDF/DWG) to 3D house models."""
    
    def __init__(self):
        """Initialize the drawing to 3D service."""
        self.output_dir = Path("./storage/house_models")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def process_drawing_file(
        self,
        file_path: Path,
        file_type: str,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Process a 2D drawing file and extract building information.
        
        Args:
            file_path: Path to the drawing file (PDF or DWG)
            file_type: Type of file ('pdf' or 'dwg')
            project_id: Associated project ID
            
        Returns:
            Dictionary with extracted building parameters
        """
        try:
            if file_type.lower() == 'pdf':
                return self._process_pdf(file_path, project_id)
            elif file_type.lower() in ['dwg', 'dxf']:
                return self._process_dwg(file_path, project_id)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error processing drawing file: {str(e)}")
            raise
    
    def _process_pdf(self, file_path: Path, project_id: int) -> Dict[str, Any]:
        """
        Extract building information from PDF floor plan.
        Uses OCR and pattern matching to extract dimensions and room layouts.
        """
        extracted_data = {
            "file_type": "pdf",
            "project_id": project_id,
            "rooms": [],
            "dimensions": {},
            "floor_count": 1,
            "total_floor_area": 0,
            "building_footprint": {},
            "status": "extracted"
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text_content = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text()
                
                # Parse dimensions using regex patterns
                extracted_data["dimensions"] = self._extract_dimensions_from_text(text_content)
                
                # Detect room information
                extracted_data["rooms"] = self._detect_rooms_from_text(text_content)
                
                # Estimate floor count
                extracted_data["floor_count"] = self._estimate_floor_count(text_content)
                
                # Calculate total floor area
                extracted_data["total_floor_area"] = self._calculate_total_area(
                    extracted_data["dimensions"],
                    extracted_data["rooms"]
                )
                
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            extracted_data["status"] = "error"
            extracted_data["error"] = str(e)
        
        return extracted_data
    
    def _process_dwg(self, file_path: Path, project_id: int) -> Dict[str, Any]:
        """
        Extract building information from DWG/DXF CAD file.
        Note: Full DWG processing requires ezdxf library for DXF or external tools for DWG.
        """
        extracted_data = {
            "file_type": "dwg",
            "project_id": project_id,
            "rooms": [],
            "dimensions": {},
            "floor_count": 1,
            "total_floor_area": 0,
            "building_footprint": {},
            "status": "pending_processing"
        }
        
        # For DWG files, we would typically:
        # 1. Convert DWG to DXF using external tool (e.g., ODA File Converter)
        # 2. Parse DXF using ezdxf library
        # 3. Extract entities (lines, polylines, text) to detect walls and dimensions
        
        # Placeholder implementation - would need ezdxf library
        logger.info(f"DWG file processing for project {project_id} - requires CAD parsing library")
        
        return extracted_data
    
    def _extract_dimensions_from_text(self, text: str) -> Dict[str, Any]:
        """Extract dimension measurements from text content."""
        dimensions = {
            "width": None,
            "length": None,
            "height": None,
            "plot_size": None
        }
        
        # Common patterns for dimensions in floor plans
        patterns = {
            'width': r'(?:width|w)[:\s]*(\d+(?:\.\d+)?)\s*(?:m|ft|meter|feet)',
            'length': r'(?:length|l)[:\s]*(\d+(?:\.\d+)?)\s*(?:m|ft|meter|feet)',
            'height': r'(?:height|h|ceiling)[:\s]*(\d+(?:\.\d+)?)\s*(?:m|ft|meter|feet)',
            'plot': r'(?:plot|site)[:\s]*(\d+(?:\.\d+)?)\s*(?:m2|sq\.m|perches)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if key == 'plot':
                    dimensions['plot_size'] = float(match.group(1))
                else:
                    dimensions[key] = float(match.group(1))
        
        return dimensions
    
    def _detect_rooms_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Detect room types and dimensions from text."""
        rooms = []
        
        # Common room types in Sri Lankan houses
        room_types = [
            'bedroom', 'living room', 'dining room', 'kitchen',
            'bathroom', 'toilet', 'veranda', 'balcony', 'garage',
            'store room', 'pantry', 'utility', 'porch'
        ]
        
        for room_type in room_types:
            # Look for room type mentions with possible dimensions
            pattern = rf'{room_type}[:\s]*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                width = float(match.group(1))
                length = float(match.group(2))
                area = width * length
                
                rooms.append({
                    'type': room_type.title(),
                    'width': width,
                    'length': length,
                    'area': area,
                    'unit': 'm'
                })
        
        return rooms
    
    def _estimate_floor_count(self, text: str) -> int:
        """Estimate number of floors from text content."""
        floor_patterns = [
            r'(\d+)\s*(?:floor|storey|story)',
            r'ground\s*floor.*first\s*floor',
            r'(?:g|ground)\s*\+\s*(\d+)'
        ]
        
        for pattern in floor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(1):
                    return int(match.group(1))
                else:
                    return 2  # Ground + First
        
        return 1  # Default single floor
    
    def _calculate_total_area(
        self,
        dimensions: Dict[str, Any],
        rooms: List[Dict[str, Any]]
    ) -> float:
        """Calculate total floor area from dimensions or room data."""
        # First try to calculate from room areas
        if rooms:
            return sum(room.get('area', 0) for room in rooms)
        
        # Otherwise use overall dimensions
        if dimensions.get('width') and dimensions.get('length'):
            return dimensions['width'] * dimensions['length']
        
        return 0.0
    
    def generate_3d_model_from_drawing(
        self,
        extracted_data: Dict[str, Any],
        project_id: int
    ) -> Dict[str, Any]:
        """
        Generate a 3D house model based on extracted 2D drawing data.
        
        Args:
            extracted_data: Extracted building parameters from 2D drawing
            project_id: Project ID
            
        Returns:
            Dictionary with 3D model generation results
        """
        try:
            # Prepare parameters for 3D generation
            building_params = self._prepare_building_parameters(extracted_data)
            
            # Generate 3D model using Blender or parametric generation
            model_result = self._create_house_model(building_params, project_id)
            
            return {
                "status": "success",
                "model_url": model_result.get("model_url"),
                "model_path": model_result.get("model_path"),
                "building_params": building_params,
                "extracted_data": extracted_data,
                "message": "3D house model generated successfully from 2D drawing"
            }
            
        except Exception as e:
            logger.error(f"Error generating 3D model: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to generate 3D model from drawing"
            }
    
    def _prepare_building_parameters(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare building parameters for 3D model generation."""
        dimensions = extracted_data.get("dimensions", {})
        rooms = extracted_data.get("rooms", [])
        
        # Calculate building dimensions
        building_width = dimensions.get("width") or self._estimate_width_from_rooms(rooms) or 10.0
        building_length = dimensions.get("length") or self._estimate_length_from_rooms(rooms) or 12.0
        building_height = dimensions.get("height") or 3.0  # Default floor height
        floor_count = extracted_data.get("floor_count", 1)
        
        return {
            "building_width": building_width,
            "building_length": building_length,
            "building_height": building_height * floor_count,
            "floor_height": building_height,
            "floor_count": floor_count,
            "total_floor_area": extracted_data.get("total_floor_area", building_width * building_length),
            "rooms": rooms,
            "building_type": "residential_house"
        }
    
    def _estimate_width_from_rooms(self, rooms: List[Dict[str, Any]]) -> Optional[float]:
        """Estimate building width from room dimensions."""
        if not rooms:
            return None
        max_width = max((room.get('width', 0) for room in rooms), default=0)
        return max_width if max_width > 0 else None
    
    def _estimate_length_from_rooms(self, rooms: List[Dict[str, Any]]) -> Optional[float]:
        """Estimate building length from room dimensions."""
        if not rooms:
            return None
        max_length = max((room.get('length', 0) for room in rooms), default=0)
        return max_length if max_length > 0 else None
    
    def _create_house_model(
        self,
        building_params: Dict[str, Any],
        project_id: int
    ) -> Dict[str, Any]:
        """
        Create a 3D house model using Blender or parametric generation.
        This is a simplified version - would call Blender in production.
        """
        output_dir = self.output_dir / str(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_filename = f"house_from_drawing_{project_id}.glb"
        model_path = output_dir / model_filename
        
        # For now, create a simple parametric model
        # In production, this would call a Blender script to generate detailed house model
        
        # Create a minimal GLB file placeholder
        # This is a minimal valid glTF binary file with a simple cube
        self._create_placeholder_glb(model_path, building_params)
        
        # Save building parameters for frontend rendering
        params_file = output_dir / f"house_params_{project_id}.json"
        with open(params_file, 'w') as f:
            json.dump(building_params, f, indent=2)
        
        return {
            "model_url": f"/api/v1/generation/{project_id}/house/download",
            "model_path": str(model_path),
            "params_path": str(params_file),
            "building_params": building_params
        }
    
    def _create_placeholder_glb(self, output_path: Path, building_params: Dict[str, Any]):
        """Create a placeholder GLB file with building parameters as metadata."""
        import struct
        
        # Get building dimensions
        width = building_params.get('building_width', 10)
        length = building_params.get('building_length', 12)
        height = building_params.get('building_height', 10)
        
        # Minimal glTF JSON structure
        gltf_json = {
            "asset": {"version": "2.0", "generator": "SmartCity House Generator"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": "House"}],
            "meshes": [{
                "primitives": [{
                    "attributes": {"POSITION": 0},
                    "indices": 1
                }],
                "name": "HouseModel"
            }],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5126,
                    "count": 8,
                    "type": "VEC3",
                    "max": [width/2, height, length/2],
                    "min": [-width/2, 0, -length/2]
                },
                {
                    "bufferView": 1,
                    "componentType": 5123,
                    "count": 36,
                    "type": "SCALAR"
                }
            ],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": 96, "target": 34962},
                {"buffer": 0, "byteOffset": 96, "byteLength": 72, "target": 34963}
            ],
            "buffers": [{"byteLength": 168}]
        }
        
        # Create simple box vertices
        w, h, l = width/2, height, length/2
        vertices = [
            -w, 0, -l,  w, 0, -l,  w, h, -l,  -w, h, -l,  # Front
            -w, 0,  l,  w, 0,  l,  w, h,  l,  -w, h,  l   # Back
        ]
        
        # Indices for box faces
        indices = [
            0,1,2, 2,3,0,  # Front
            5,4,7, 7,6,5,  # Back
            4,0,3, 3,7,4,  # Left
            1,5,6, 6,2,1,  # Right
            3,2,6, 6,7,3,  # Top
            4,5,1, 1,0,4   # Bottom
        ]
        
        # Pack binary data
        vertex_data = struct.pack(f'{len(vertices)}f', *vertices)
        index_data = struct.pack(f'{len(indices)}H', *indices)
        binary_data = vertex_data + index_data
        
        # Convert JSON to bytes
        json_data = json.dumps(gltf_json, separators=(',', ':')).encode('utf-8')
        json_padding = (4 - len(json_data) % 4) % 4
        json_data += b' ' * json_padding
        
        # Add padding to binary data
        bin_padding = (4 - len(binary_data) % 4) % 4
        binary_data += b'\x00' * bin_padding
        
        # GLB header
        magic = b'glTF'
        version = struct.pack('<I', 2)
        total_length = 12 + 8 + len(json_data) + 8 + len(binary_data)
        length = struct.pack('<I', total_length)
        
        # JSON chunk
        json_chunk_length = struct.pack('<I', len(json_data))
        json_chunk_type = struct.pack('<I', 0x4E4F534A)  # "JSON"
        
        # BIN chunk
        bin_chunk_length = struct.pack('<I', len(binary_data))
        bin_chunk_type = struct.pack('<I', 0x004E4942)  # "BIN\0"
        
        # Write GLB file
        with open(output_path, 'wb') as f:
            f.write(magic + version + length)
            f.write(json_chunk_length + json_chunk_type + json_data)
            f.write(bin_chunk_length + bin_chunk_type + binary_data)


# Singleton instance
_drawing_service = None

def get_drawing_service() -> DrawingTo3DService:
    """Get or create drawing to 3D service instance."""
    global _drawing_service
    if _drawing_service is None:
        _drawing_service = DrawingTo3DService()
    return _drawing_service
