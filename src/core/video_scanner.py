"""
Video scanner module for the Footage Thumbnailer application.

This module provides functionality to recursively scan directories for video files,
validate their accessibility, and return structured file information.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from utils.file_utils import (
    is_directory_accessible,
    is_file_accessible,
    get_file_size,
    get_file_modification_time,
    scan_directory_for_files,
    has_supported_extension
)


@dataclass
class VideoFile:
    """Data class representing a video file with metadata."""
    path: str
    filename: str
    size: int
    modified_date: Optional[datetime]
    is_accessible: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "filename": self.filename,
            "size": self.size,
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
            "is_accessible": self.is_accessible
        }


class VideoScanner:
    """Scans directories for video files and provides file information."""
    
    def __init__(self, supported_extensions: Optional[List[str]] = None):
        """
        Initialize the video scanner.
        
        Args:
            supported_extensions: List of supported video file extensions.
                                If None, uses default extensions.
        """
        if supported_extensions is None:
            self.supported_extensions = [".mp4", ".mov", ".avi", ".mkv", ".mts"]
        else:
            self.supported_extensions = [ext.lower() for ext in supported_extensions]
    
    def scan_folders(self, folder_paths: List[str], recursive: bool = True) -> List[VideoFile]:
        """
        Scan multiple folders for video files.
        
        Args:
            folder_paths: List of directory paths to scan.
            recursive: Whether to scan subdirectories recursively.
            
        Returns:
            List of VideoFile objects representing found video files.
        """
        all_video_files = []
        processed_paths = set()  # Avoid duplicate files from overlapping paths
        
        for folder_path in folder_paths:
            if not folder_path or not folder_path.strip():
                continue
                
            folder_path = folder_path.strip()
            
            if not is_directory_accessible(folder_path):
                print(f"Warning: Cannot access directory: {folder_path}")
                continue
            
            try:
                video_files = self._scan_single_folder(folder_path, recursive)
                
                # Filter out duplicates based on normalized path
                for video_file in video_files:
                    normalized_path = os.path.normpath(os.path.abspath(video_file.path))
                    if normalized_path not in processed_paths:
                        processed_paths.add(normalized_path)
                        all_video_files.append(video_file)
                        
            except Exception as e:
                print(f"Error scanning folder {folder_path}: {e}")
                continue
        
        # Sort by path for consistent ordering
        all_video_files.sort(key=lambda x: x.path.lower())
        
        return all_video_files
    
    def _scan_single_folder(self, folder_path: str, recursive: bool = True) -> List[VideoFile]:
        """
        Scan a single folder for video files.
        
        Args:
            folder_path: Path to the directory to scan.
            recursive: Whether to scan subdirectories recursively.
            
        Returns:
            List of VideoFile objects found in the directory.
        """
        video_files = []
        
        try:
            # Get list of video file paths
            file_paths = scan_directory_for_files(
                folder_path, 
                self.supported_extensions, 
                recursive
            )
            
            # Create VideoFile objects for each found file
            for file_path in file_paths:
                video_file = self._create_video_file_object(file_path)
                if video_file:
                    video_files.append(video_file)
                    
        except Exception as e:
            print(f"Error scanning folder {folder_path}: {e}")
        
        return video_files
    
    def _create_video_file_object(self, file_path: str) -> Optional[VideoFile]:
        """
        Create a VideoFile object from a file path.
        
        Args:
            file_path: Path to the video file.
            
        Returns:
            VideoFile object or None if file cannot be processed.
        """
        try:
            filename = os.path.basename(file_path)
            size = get_file_size(file_path)
            modified_date = get_file_modification_time(file_path)
            is_accessible = is_file_accessible(file_path)
            
            return VideoFile(
                path=file_path,
                filename=filename,
                size=size,
                modified_date=modified_date,
                is_accessible=is_accessible
            )
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None
    
    def is_supported_video(self, file_path: str) -> bool:
        """
        Check if a file is a supported video file.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if file is a supported video file, False otherwise.
        """
        return has_supported_extension(file_path, self.supported_extensions)
    
    def get_video_count(self, folder_paths: List[str], recursive: bool = True) -> int:
        """
        Get the total count of video files in the specified folders.
        
        Args:
            folder_paths: List of directory paths to scan.
            recursive: Whether to count files in subdirectories recursively.
            
        Returns:
            Total number of video files found.
        """
        video_files = self.scan_folders(folder_paths, recursive)
        return len([vf for vf in video_files if vf.is_accessible])
    
    def get_total_size(self, folder_paths: List[str], recursive: bool = True) -> int:
        """
        Get the total size of video files in the specified folders.
        
        Args:
            folder_paths: List of directory paths to scan.
            recursive: Whether to include files in subdirectories recursively.
            
        Returns:
            Total size of video files in bytes.
        """
        video_files = self.scan_folders(folder_paths, recursive)
        return sum(vf.size for vf in video_files if vf.is_accessible)
    
    def filter_accessible_files(self, video_files: List[VideoFile]) -> List[VideoFile]:
        """
        Filter video files to only include accessible ones.
        
        Args:
            video_files: List of VideoFile objects to filter.
            
        Returns:
            List of accessible VideoFile objects.
        """
        return [vf for vf in video_files if vf.is_accessible]
    
    def group_by_directory(self, video_files: List[VideoFile]) -> Dict[str, List[VideoFile]]:
        """
        Group video files by their parent directory.
        
        Args:
            video_files: List of VideoFile objects to group.
            
        Returns:
            Dictionary mapping directory paths to lists of VideoFile objects.
        """
        grouped = {}
        
        for video_file in video_files:
            directory = os.path.dirname(video_file.path)
            if directory not in grouped:
                grouped[directory] = []
            grouped[directory].append(video_file)
        
        return grouped
    
    def get_scan_summary(self, folder_paths: List[str], recursive: bool = True) -> Dict[str, Any]:
        """
        Get a summary of the scan results.
        
        Args:
            folder_paths: List of directory paths to scan.
            recursive: Whether to scan subdirectories recursively.
            
        Returns:
            Dictionary containing scan summary information.
        """
        video_files = self.scan_folders(folder_paths, recursive)
        accessible_files = self.filter_accessible_files(video_files)
        
        total_size = sum(vf.size for vf in accessible_files)
        
        # Group by directory for additional statistics
        grouped = self.group_by_directory(accessible_files)
        
        return {
            "total_files_found": len(video_files),
            "accessible_files": len(accessible_files),
            "inaccessible_files": len(video_files) - len(accessible_files),
            "total_size_bytes": total_size,
            "directories_scanned": len(folder_paths),
            "directories_with_videos": len(grouped),
            "supported_extensions": self.supported_extensions,
            "scan_mode": "recursive" if recursive else "non-recursive"
        }
    
    def validate_folders(self, folder_paths: List[str]) -> Dict[str, bool]:
        """
        Validate that all specified folders are accessible.
        
        Args:
            folder_paths: List of directory paths to validate.
            
        Returns:
            Dictionary mapping folder paths to their accessibility status.
        """
        validation_results = {}
        
        for folder_path in folder_paths:
            if not folder_path or not folder_path.strip():
                validation_results[folder_path] = False
                continue
                
            folder_path = folder_path.strip()
            validation_results[folder_path] = is_directory_accessible(folder_path)
        
        return validation_results
    
    def update_supported_extensions(self, extensions: List[str]) -> None:
        """
        Update the list of supported file extensions.
        
        Args:
            extensions: New list of supported file extensions.
        """
        self.supported_extensions = [ext.lower() for ext in extensions]
    
    def get_file_extension_stats(self, folder_paths: List[str], recursive: bool = True) -> Dict[str, int]:
        """
        Get statistics about file extensions found during scanning.
        
        Args:
            folder_paths: List of directory paths to scan.
            recursive: Whether to scan subdirectories recursively.
            
        Returns:
            Dictionary mapping file extensions to their counts.
        """
        video_files = self.scan_folders(folder_paths, recursive)
        extension_counts = {}
        
        for video_file in video_files:
            if video_file.is_accessible:
                extension = Path(video_file.path).suffix.lower()
                extension_counts[extension] = extension_counts.get(extension, 0) + 1
        
        return extension_counts