"""
FCPXML parser for the Footage Thumbnailer application.

This module handles parsing of FCPXML files and extracting video file references
for timeline-based thumbnail generation.
"""

import os
import re
import urllib.parse
from typing import List, Optional, Dict, Any
from pathlib import Path
from xml.etree import ElementTree as ET

from .timeline_data_models import TimelineEntry, TimelineVideoMatch


# FCPXMLEntry is now simply an alias for TimelineEntry
FCPXMLEntry = TimelineEntry


class FCPXMLParser:
    """Parser for FCPXML file format."""
    
    def __init__(self):
        """Initialize the FCPXML parser."""
        self._reset_state()
    
    def _reset_state(self):
        """Reset parser state for new file."""
        self.entries = []
        self.resources = {}
        self.line_number = 0
    
    def parse_fcpxml_file(self, file_path: str) -> List[TimelineEntry]:
        """
        Parse an FCPXML file and extract video entries.
        
        Args:
            file_path: Path to the FCPXML file.
            
        Returns:
            List of TimelineEntry objects representing video references.
            
        Raises:
            FileNotFoundError: If the FCPXML file doesn't exist.
            ValueError: If the FCPXML file format is unsupported or malformed.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"FCPXML file not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        self._reset_state()
        
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check if it's a valid FCPXML file
            if root.tag != 'fcpxml':
                raise ValueError("Invalid FCPXML file format")
            
            # Parse resources section to get file paths
            self._parse_resources(root)
            
            # Parse timeline to get video entries
            self._parse_timeline(root)
            
            # Extract and normalize video entries
            video_entries = self.extract_video_entries(self.entries)
            return self.normalize_file_paths(video_entries)
            
        except ET.ParseError as e:
            raise ValueError(f"Error parsing FCPXML file {file_path}: Invalid XML format - {e}")
        except Exception as e:
            raise ValueError(f"Error parsing FCPXML file {file_path}: {e}")
    
    def _parse_resources(self, root: ET.Element) -> None:
        """
        Parse the resources section of FCPXML file.
        
        Args:
            root: Root element of the FCPXML document.
        """
        resources_elem = root.find('resources')
        if resources_elem is None:
            return
        
        # Process each asset in resources
        for asset in resources_elem.findall('asset'):
            asset_id = asset.get('id')
            if asset_id:
                # Extract file path from src attribute
                src_url = asset.get('src')
                if src_url:
                    # Convert file:// URL to local path
                    local_path = self._convert_file_url_to_path(src_url)
                    if local_path:
                        self.resources[asset_id] = local_path
    
    def _parse_timeline(self, root: ET.Element) -> None:
        """
        Parse the timeline section of FCPXML file.
        
        Args:
            root: Root element of the FCPXML document.
        """
        # Find the sequence in the project
        sequence = root.find('.//sequence')
        if sequence is None:
            return
        
        # Find all asset clips in the spine
        spine = sequence.find('spine')
        if spine is None:
            return
        
        source_id = 1
        cumulative_offset = 0.0  # Keep track of cumulative time for proper start times
        
        for asset_clip in spine.findall('asset-clip'):
            ref_id = asset_clip.get('ref')
            if ref_id and ref_id in self.resources:
                # Get the file path from resources
                file_path = self.resources[ref_id]
                
                # Extract timing information
                # These are timeline positions (when in timeline)
                timeline_offset = self._parse_time_attribute(asset_clip.get('offset', '0s'))
                timeline_duration = self._parse_time_attribute(asset_clip.get('duration', '0s'))
                
                # These are positions within the original footage
                clip_start = self._parse_time_attribute(asset_clip.get('start', '0s'))
                
                # Calculate timeline start and end times
                start_time = timeline_offset if timeline_offset is not None else cumulative_offset
                end_time = start_time + timeline_duration if start_time is not None and timeline_duration is not None else None
                
                # Calculate clip end time
                clip_end = clip_start + timeline_duration if clip_start is not None and timeline_duration is not None else None
                
                # Update cumulative offset for next clip
                if start_time is not None and timeline_duration is not None:
                    cumulative_offset = start_time + timeline_duration
                
                entry = TimelineEntry(
                    source_id=source_id,
                    file_path=file_path,
                    media_type="VIDEO",
                    # Timeline positioning (when in sequence)
                    start_time=start_time,
                    end_time=end_time,
                    # Clip positioning (within original footage)
                    clip_start_time=clip_start,
                    clip_end_time=clip_end
                )
                
                self.entries.append(entry)
                source_id += 1
    
    def _convert_file_url_to_path(self, file_url: str) -> Optional[str]:
        """
        Convert file:// URL to local file path.
        
        Args:
            file_url: File URL to convert.
            
        Returns:
            Local file path or None if conversion fails.
        """
        try:
            # Parse the URL
            parsed_url = urllib.parse.urlparse(file_url)
            
            # Check if it's a file URL
            if parsed_url.scheme != 'file':
                return None
            
            # Convert to local path
            # Handle both file://localhost/path and file:///path formats
            if parsed_url.netloc and parsed_url.netloc != 'localhost':
                # Network path - not supported
                return None
            
            # Decode URL-encoded characters
            local_path = urllib.parse.unquote(parsed_url.path)
            
            # Handle Windows paths that start with /drive_letter:/
            if local_path.startswith('/') and len(local_path) > 3 and local_path[2] == ':':
                local_path = local_path[1:]  # Remove leading slash
            
            # Normalize the path but preserve forward slashes for consistency
            local_path = os.path.normpath(local_path)
            
            # Convert backslashes to forward slashes for consistency
            local_path = local_path.replace('\\', '/')
            
            return local_path
        except Exception:
            return None
    
    def _parse_time_attribute(self, time_str: str) -> Optional[float]:
        """
        Parse time attribute from FCPXML (e.g., "1/25s", "3600/1s", "5.5s").
        
        Args:
            time_str: Time string to parse.
            
        Returns:
            Time in seconds or None if parsing fails.
        """
        if not time_str:
            return None
        
        try:
            # Remove the 's' suffix
            if time_str.endswith('s'):
                time_str = time_str[:-1]
            
            # Handle fractional format (e.g., "1/25")
            if '/' in time_str:
                numerator, denominator = time_str.split('/')
                return float(numerator) / float(denominator)
            else:
                # Handle decimal format (e.g., "5.5")
                return float(time_str)
        except (ValueError, ZeroDivisionError):
            return None
    
    def extract_video_entries(self, entries: List[TimelineEntry]) -> List[TimelineEntry]:
        """
        Filter entries to only include video entries.
        
        Args:
            entries: List of all FCPXML entries.
            
        Returns:
            List of video entries only.
        """
        return [entry for entry in entries if entry.media_type.upper() == "VIDEO"]
    
    def normalize_file_paths(self, entries: List[TimelineEntry]) -> List[TimelineEntry]:
        """
        Normalize file paths in FCPXML entries.
        
        Args:
            entries: List of FCPXML entries to normalize.
            
        Returns:
            List of entries with normalized file paths.
        """
        normalized_entries = []
        
        for entry in entries:
            # Create a copy to avoid modifying the original
            normalized_entry = TimelineEntry(
                source_id=entry.source_id,
                file_path=os.path.normpath(entry.file_path).replace('\\', '/'),
                media_type=entry.media_type,
                start_time=entry.start_time,
                end_time=entry.end_time,
                clip_start_time=entry.clip_start_time,
                clip_end_time=entry.clip_end_time,
                track_info=entry.track_info
            )
            
            normalized_entries.append(normalized_entry)
        
        return normalized_entries
    
    def get_unique_files(self, entries: List[TimelineEntry]) -> List[str]:
        """
        Get unique file paths from FCPXML entries.
        
        Args:
            entries: List of FCPXML entries.
            
        Returns:
            List of unique file paths.
        """
        unique_paths = set()
        for entry in entries:
            # Normalize path for comparison
            normalized_path = os.path.normpath(entry.file_path).replace('\\', '/')
            unique_paths.add(normalized_path)
        
        return sorted(list(unique_paths))
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parsing statistics.
        
        Returns:
            Dictionary containing parsing statistics.
        """
        video_entries = self.extract_video_entries(self.entries)
        unique_files = self.get_unique_files(video_entries)
        
        return {
            "total_entries": len(self.entries),
            "video_entries": len(video_entries),
            "unique_files": len(unique_files),
            "unique_file_paths": unique_files
        }