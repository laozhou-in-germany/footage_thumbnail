"""
Thumbnail extractor module for the Footage Thumbnailer application.

This module provides functionality to extract frames from video files at specified
time positions and retrieve video metadata using FFmpeg and OpenCV.
"""

import os
import re
import cv2
import ffmpeg
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from PIL import Image
import numpy as np

from core.video_scanner import VideoFile


@dataclass
class VideoMetadata:
    """Data class representing video metadata."""
    duration: float
    creation_date: Optional[datetime]
    resolution: Tuple[int, int]
    fps: float
    codec: str
    format: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "duration": self.duration,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "resolution": self.resolution,
            "fps": self.fps,
            "codec": self.codec,
            "format": self.format
        }


@dataclass
class ThumbnailData:
    """Data class representing extracted thumbnail data."""
    image: Image.Image
    position: float
    timestamp: str
    frame_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (excluding image)."""
        return {
            "position": self.position,
            "timestamp": self.timestamp,
            "frame_number": self.frame_number
        }


@dataclass
class VideoData:
    """Data class combining video file, metadata, and thumbnails."""
    file: VideoFile
    metadata: VideoMetadata
    thumbnails: List[ThumbnailData]
    processing_status: str = "pending"
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file": self.file.to_dict(),
            "metadata": self.metadata.to_dict(),
            "thumbnails": [thumb.to_dict() for thumb in self.thumbnails],
            "processing_status": self.processing_status,
            "error_message": self.error_message
        }


class ThumbnailExtractor:
    """Extracts thumbnails and metadata from video files."""
    
    def __init__(self):
        """Initialize the thumbnail extractor."""
        self.temp_frame_count = 0
    
    def extract_thumbnails(
        self, 
        video_path: str, 
        positions: List[str],
        thumbnail_width: int = 320
    ) -> List[ThumbnailData]:
        """
        Extract thumbnails from a video at specified positions.
        
        Args:
            video_path: Path to the video file.
            positions: List of position strings (e.g., ["0%", "50%", "99%"]).
            thumbnail_width: Target width for thumbnails.
            
        Returns:
            List of ThumbnailData objects containing extracted thumbnails.
        """
        thumbnails = []
        
        try:
            # Get video metadata first
            metadata = self.get_video_metadata(video_path)
            if metadata is None:
                return thumbnails
            
            # Open video file with OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file {video_path}")
                return thumbnails
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if fps <= 0:
                fps = metadata.fps
            
            # Extract thumbnails at each position
            for i, position_str in enumerate(positions):
                try:
                    # Parse the position
                    position_seconds = self.parse_time_position(position_str, metadata.duration)
                    
                    if position_seconds is None:
                        continue
                    
                    # Calculate frame number
                    frame_number = int(position_seconds * fps)
                    frame_number = max(0, min(frame_number, total_frames - 1))
                    
                    # Seek to the frame
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    
                    # Read the frame
                    ret, frame = cap.read()
                    if not ret:
                        print(f"Warning: Could not read frame at position {position_str} for {video_path}")
                        continue
                    
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Resize proportionally
                    original_width, original_height = pil_image.size
                    aspect_ratio = original_height / original_width
                    target_height = int(thumbnail_width * aspect_ratio)
                    
                    resized_image = pil_image.resize(
                        (thumbnail_width, target_height), 
                        Image.Resampling.LANCZOS
                    )
                    
                    # Create timestamp string
                    timestamp = self._format_timestamp(position_seconds)
                    
                    # Create thumbnail data
                    thumbnail = ThumbnailData(
                        image=resized_image,
                        position=position_seconds,
                        timestamp=timestamp,
                        frame_number=frame_number
                    )
                    
                    thumbnails.append(thumbnail)
                    
                except Exception as e:
                    print(f"Error extracting thumbnail at position {position_str} for {video_path}: {e}")
                    continue
            
            cap.release()
            
        except Exception as e:
            print(f"Error extracting thumbnails from {video_path}: {e}")
        
        return thumbnails
    
    def get_video_metadata(self, video_path: str) -> Optional[VideoMetadata]:
        """
        Extract metadata from a video file using FFmpeg.
        
        Args:
            video_path: Path to the video file.
            
        Returns:
            VideoMetadata object or None if extraction fails.
        """
        try:
            # Use ffmpeg-python to probe the video file
            probe = ffmpeg.probe(video_path)
            
            # Find the video stream
            video_stream = None
            for stream in probe['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if video_stream is None:
                print(f"No video stream found in {video_path}")
                return None
            
            # Extract basic metadata
            duration = float(probe['format'].get('duration', 0))
            
            # Get resolution
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            # Get FPS
            fps_str = video_stream.get('r_frame_rate', '0/1')
            if '/' in fps_str:
                fps_parts = fps_str.split('/')
                fps = float(fps_parts[0]) / float(fps_parts[1]) if float(fps_parts[1]) != 0 else 0
            else:
                fps = float(fps_str)
            
            # Get codec and format
            codec = video_stream.get('codec_name', 'unknown')
            format_name = probe['format'].get('format_name', 'unknown')
            
            # Try to get creation date from metadata
            creation_date = None
            format_tags = probe['format'].get('tags', {})
            stream_tags = video_stream.get('tags', {})
            
            # Look for creation date in various tag formats
            creation_tags = ['creation_time', 'date', 'DATE', 'creation_date']
            for tag in creation_tags:
                if tag in format_tags:
                    creation_date = self._parse_creation_date(format_tags[tag])
                    break
                elif tag in stream_tags:
                    creation_date = self._parse_creation_date(stream_tags[tag])
                    break
            
            # If no creation date in metadata, try file modification time
            if creation_date is None:
                try:
                    file_mtime = os.path.getmtime(video_path)
                    creation_date = datetime.fromtimestamp(file_mtime)
                except Exception:
                    creation_date = None
            
            return VideoMetadata(
                duration=duration,
                creation_date=creation_date,
                resolution=(width, height),
                fps=fps,
                codec=codec,
                format=format_name
            )
            
        except Exception as e:
            print(f"Error extracting metadata from {video_path}: {e}")
            return None
    
    def parse_time_position(self, position: str, duration: float) -> Optional[float]:
        """
        Parse a time position string into seconds.
        
        Args:
            position: Position string (e.g., "50%", "30s", "1m30s").
            duration: Total duration of the video in seconds.
            
        Returns:
            Position in seconds, or None if parsing fails.
        """
        try:
            position = position.strip()
            
            if position.endswith('%'):
                # Percentage position
                percent = float(position[:-1])
                if 0 <= percent <= 100:
                    return (percent / 100.0) * duration
                else:
                    return None
            
            elif position.endswith('s'):
                # Absolute seconds
                seconds = float(position[:-1])
                return min(seconds, duration)
            
            elif 'm' in position:
                # Minutes and seconds format (e.g., "1m30s")
                if position.endswith('s'):
                    # Format like "1m30s"
                    parts = position[:-1].split('m')
                    if len(parts) == 2:
                        minutes = float(parts[0])
                        seconds = float(parts[1]) if parts[1] else 0
                        total_seconds = minutes * 60 + seconds
                        return min(total_seconds, duration)
                else:
                    # Format like "1m"
                    minutes = float(position[:-1])
                    total_seconds = minutes * 60
                    return min(total_seconds, duration)
            
            elif position.startswith('frame:'):
                # Frame number format
                frame_num = int(position[6:])
                # This would need FPS information, which we'll approximate
                # For now, assume 30 FPS as fallback
                seconds = frame_num / 30.0
                return min(seconds, duration)
            
            else:
                # Try to parse as pure seconds
                seconds = float(position)
                return min(seconds, duration)
                
        except Exception as e:
            print(f"Error parsing position '{position}': {e}")
            return None
    
    def _parse_creation_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse creation date string into datetime object.
        
        Args:
            date_str: Date string from video metadata.
            
        Returns:
            datetime object or None if parsing fails.
        """
        if not date_str:
            return None
        
        # Common date formats in video metadata
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%SZ",     # ISO format
            "%Y-%m-%d %H:%M:%S",      # Standard format
            "%Y:%m:%d %H:%M:%S",      # EXIF-style format
            "%Y-%m-%d",               # Date only
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try to extract date with regex if standard formats fail
        try:
            # Look for YYYY-MM-DD pattern
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
            if date_match:
                year, month, day = map(int, date_match.groups())
                
                # Look for HH:MM:SS pattern
                time_match = re.search(r'(\d{2}):(\d{2}):(\d{2})', date_str)
                if time_match:
                    hour, minute, second = map(int, time_match.groups())
                    return datetime(year, month, day, hour, minute, second)
                else:
                    return datetime(year, month, day)
        except Exception:
            pass
        
        return None
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds into a timestamp string.
        
        Args:
            seconds: Time in seconds.
            
        Returns:
            Formatted timestamp string (HH:MM:SS or MM:SS).
        """
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def process_video_file(
        self, 
        video_file: VideoFile, 
        positions: List[str],
        thumbnail_width: int = 320
    ) -> VideoData:
        """
        Process a complete video file to extract metadata and thumbnails.
        
        Args:
            video_file: VideoFile object to process.
            positions: List of position strings for thumbnail extraction.
            thumbnail_width: Target width for thumbnails.
            
        Returns:
            VideoData object containing all extracted information.
        """
        try:
            # Extract metadata
            metadata = self.get_video_metadata(video_file.path)
            if metadata is None:
                return VideoData(
                    file=video_file,
                    metadata=VideoMetadata(0, None, (0, 0), 0, "unknown", "unknown"),
                    thumbnails=[],
                    processing_status="error",
                    error_message="Failed to extract video metadata"
                )
            
            # Extract thumbnails
            thumbnails = self.extract_thumbnails(
                video_file.path,
                positions,
                thumbnail_width
            )
            
            return VideoData(
                file=video_file,
                metadata=metadata,
                thumbnails=thumbnails,
                processing_status="success" if thumbnails else "no_thumbnails"
            )
            
        except Exception as e:
            return VideoData(
                file=video_file,
                metadata=VideoMetadata(0, None, (0, 0), 0, "unknown", "unknown"),
                thumbnails=[],
                processing_status="error",
                error_message=str(e)
            )
    
    def batch_process_videos(
        self, 
        video_files: List[VideoFile], 
        positions: List[str],
        thumbnail_width: int = 320,
        progress_callback: Optional[callable] = None
    ) -> List[VideoData]:
        """
        Process multiple video files in batch.
        
        Args:
            video_files: List of VideoFile objects to process.
            positions: List of position strings for thumbnail extraction.
            thumbnail_width: Target width for thumbnails.
            progress_callback: Optional callback function for progress updates.
            
        Returns:
            List of VideoData objects containing extracted information.
        """
        processed_videos = []
        total_files = len(video_files)
        
        for i, video_file in enumerate(video_files):
            if not video_file.is_accessible:
                # Create error entry for inaccessible files
                processed_videos.append(VideoData(
                    file=video_file,
                    metadata=VideoMetadata(0, None, (0, 0), 0, "unknown", "unknown"),
                    thumbnails=[],
                    processing_status="error",
                    error_message="File is not accessible"
                ))
                continue
            
            # Process the video file
            video_data = self.process_video_file(video_file, positions, thumbnail_width)
            processed_videos.append(video_data)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, total_files, video_file.filename)
        
        return processed_videos
    
    def validate_video_file(self, video_path: str) -> bool:
        """
        Validate that a video file can be processed.
        
        Args:
            video_path: Path to the video file.
            
        Returns:
            True if video file is valid and can be processed, False otherwise.
        """
        try:
            # Try to open with OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                cap.release()
                return False
            
            # Try to read one frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False
            
            # Try to get metadata with FFmpeg
            metadata = self.get_video_metadata(video_path)
            return metadata is not None and metadata.duration > 0
            
        except Exception:
            return False