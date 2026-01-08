"""
Video generation service for room tour animations.
Uses MoviePy to stitch room images into MP4 video.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import tempfile

logger = logging.getLogger(__name__)

class RoomTourVideoService:
    """Service for generating MP4 videos from room tour images."""
    
    def __init__(self):
        self.temp_dir = Path("./storage/temp/videos")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.fps = 24
        self.duration_per_room = 5  # seconds
        self.resolution = (1280, 720)  # HD
    
    async def generate_video(
        self, 
        rooms: List[Dict[str, Any]],
        output_filename: str = "room_tour.mp4"
    ) -> Path:
        """
        Generate MP4 video from room images.
        
        Args:
            rooms: List of room dictionaries with 'image_url', 'room_type', etc.
            output_filename: Name for output video file
            
        Returns:
            Path to generated video file
        """
        try:
            from moviepy.editor import ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip
        except ImportError:
            logger.error("MoviePy not installed. Install with: pip install moviepy")
            raise ImportError("MoviePy is required for video generation")
        
        output_path = self.temp_dir / output_filename
        
        try:
            # Download and prepare images
            logger.info(f"Downloading {len(rooms)} room images...")
            local_images = await self._download_images(rooms)
            
            # Create video clips
            clips = []
            for idx, (room, img_path) in enumerate(zip(rooms, local_images)):
                logger.info(f"Creating clip {idx + 1}/{len(rooms)}: {room.get('room_type')}")
                
                # Create image clip
                img_clip = ImageClip(str(img_path), duration=self.duration_per_room)
                
                # Add text overlay
                room_text = f"{room.get('room_type', 'Room')}"
                if room.get('dimensions'):
                    room_text += f"\n{room['dimensions']}"
                
                try:
                    text_clip = TextClip(
                        room_text,
                        fontsize=50,
                        color='white',
                        font='Arial-Bold',
                        stroke_color='black',
                        stroke_width=2
                    )
                    text_clip = text_clip.set_position(('center', 50)).set_duration(self.duration_per_room)
                    
                    # Composite
                    video_clip = CompositeVideoClip([img_clip, text_clip])
                except Exception as e:
                    logger.warning(f"Failed to add text overlay: {e}, using image only")
                    video_clip = img_clip
                
                clips.append(video_clip)
            
            # Concatenate all clips
            logger.info("Concatenating clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Write video file
            logger.info(f"Writing video to {output_path}...")
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio=False,
                logger=None  # Suppress MoviePy's verbose logging
            )
            
            logger.info(f"Video generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            raise
    
    async def _download_images(self, rooms: List[Dict]) -> List[Path]:
        """
        Download room images from URLs.
        
        Returns:
            List of paths to downloaded images
        """
        local_paths = []
        
        for idx, room in enumerate(rooms):
            if room.get('status') != 'completed':
                logger.warning(f"Skipping room {idx}: status is {room.get('status')}")
                continue
            
            image_url = room.get('image_url')
            if not image_url:
                logger.warning(f"Skipping room {idx}: no image URL")
                continue
            
            try:
                # Download image
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                # Save to temp file
                img_path = self.temp_dir / f"room_{idx}.jpg"
                img = Image.open(BytesIO(response.content))
                
                # Resize to standard resolution
                img = img.resize(self.resolution, Image.Resampling.LANCZOS)
                img = img.convert('RGB')  # Ensure RGB mode
                img.save(img_path, 'JPEG', quality=95)
                
                local_paths.append(img_path)
                logger.debug(f"Downloaded room image {idx + 1}/{len(rooms)}")
                
            except Exception as e:
                logger.error(f"Failed to download image for room {idx}: {e}")
                continue
        
        return local_paths
    
    def cleanup_temp_files(self):
        """Remove temporary image and video files."""
        try:
            for file in self.temp_dir.glob("room_*.jpg"):
                file.unlink()
            logger.info("Cleaned up temporary image files")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")
