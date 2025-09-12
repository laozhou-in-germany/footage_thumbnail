"""
Timeline data models for the Footage Thumbnailer application.

This module contains data classes used for timeline-based processing,
specifically for FCPXML files.
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class TimelineEntry:
    """Represents a single video entry from timeline file (FCPXML)."""
    source_id: int
    file_path: str
    media_type: str = "VIDEO"  # 'VIDEO' or 'AUDIO'
    # Timeline positioning (when in sequence)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    # Clip positioning (within original footage)
    clip_start_time: Optional[float] = None
    clip_end_time: Optional[float] = None
    track_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Normalize file path
        self.file_path = os.path.normpath(self.file_path)
        
        # Calculate duration if start and end times are available
        if self.start_time is not None and self.end_time is not None:
            self.timeline_duration = self.end_time - self.start_time
        else:
            self.timeline_duration = None
            
        # Calculate clip duration if clip start and end times are available
        if self.clip_start_time is not None and self.clip_end_time is not None:
            self.clip_duration = self.clip_end_time - self.clip_start_time
        else:
            self.clip_duration = None


@dataclass
class TimelineVideoMatch:
    """Links timeline entries with found video files."""
    timeline_entry: TimelineEntry
    matched_file_path: Optional[str] = None
    is_found: bool = False
    similarity_score: float = 0.0
    error_message: Optional[str] = None