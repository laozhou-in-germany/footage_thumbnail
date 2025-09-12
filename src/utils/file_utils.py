"""
File system utility functions for the Footage Thumbnailer application.

This module provides utilities for file system operations, path handling,
and video file validation.
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory to create.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def is_file_accessible(file_path: str) -> bool:
    """
    Check if a file is accessible for reading.
    
    Args:
        file_path: Path to the file to check.
        
    Returns:
        True if file is accessible, False otherwise.
    """
    try:
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
    except Exception:
        return False


def is_directory_accessible(directory_path: str) -> bool:
    """
    Check if a directory is accessible for reading.
    
    Args:
        directory_path: Path to the directory to check.
        
    Returns:
        True if directory is accessible, False otherwise.
    """
    try:
        return os.path.isdir(directory_path) and os.access(directory_path, os.R_OK)
    except Exception:
        return False


def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File size in bytes, or 0 if file doesn't exist or is inaccessible.
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def get_file_modification_time(file_path: str) -> Optional[datetime]:
    """
    Get the modification time of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Modification time as datetime object, or None if file doesn't exist.
    """
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return None


def generate_multi_page_filenames(base_path: str, page_count: int) -> List[str]:
    """
    Generate filenames for multiple pages based on a base path.
    
    Args:
        base_path: Base output file path (e.g., "output/overview.jpg")
        page_count: Number of pages to generate names for
        
    Returns:
        List of file paths for each page
    """
    if page_count <= 1:
        return [base_path]
    
    # Parse the base path
    path_obj = Path(base_path)
    base_name = path_obj.stem  # filename without extension
    extension = path_obj.suffix  # file extension
    directory = path_obj.parent  # directory path
    
    # Generate filenames with page numbers
    filenames = []
    for i in range(page_count):
        page_num = i + 1
        if i == 0:
            # First page keeps original name
            filename = base_path
        else:
            # Additional pages get page numbers
            filename = directory / f"{base_name}_page{page_num:02d}{extension}"
            filename = str(filename)
        filenames.append(filename)
    
    return filenames


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes.
        
    Returns:
        Formatted file size string (e.g., "1.5 GB").
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    if size_index == 0:
        return f"{int(size)} {size_names[size_index]}"
    else:
        return f"{size:.1f} {size_names[size_index]}"


def get_safe_filename(filename: str) -> str:
    """
    Convert a filename to a safe version by removing or replacing invalid characters.
    
    Args:
        filename: Original filename.
        
    Returns:
        Safe filename with invalid characters removed or replaced.
    """
    # Characters that are invalid in Windows filenames
    invalid_chars = '<>:"/\\|?*'
    safe_filename = filename
    
    for char in invalid_chars:
        safe_filename = safe_filename.replace(char, '_')
    
    # Remove leading/trailing spaces and periods
    safe_filename = safe_filename.strip(' .')
    
    # Ensure filename is not empty
    if not safe_filename:
        safe_filename = "untitled"
    
    return safe_filename


def has_supported_extension(file_path: str, supported_extensions: List[str]) -> bool:
    """
    Check if a file has a supported extension.
    
    Args:
        file_path: Path to the file.
        supported_extensions: List of supported file extensions (with dots).
        
    Returns:
        True if file has a supported extension, False otherwise.
    """
    file_extension = Path(file_path).suffix.lower()
    return file_extension in [ext.lower() for ext in supported_extensions]


def scan_directory_for_files(
    directory_path: str, 
    supported_extensions: List[str], 
    recursive: bool = True
) -> List[str]:
    """
    Scan a directory for files with supported extensions.
    
    Args:
        directory_path: Path to the directory to scan.
        supported_extensions: List of supported file extensions.
        recursive: Whether to scan subdirectories recursively.
        
    Returns:
        List of file paths that match the supported extensions.
    """
    found_files = []
    
    try:
        if not is_directory_accessible(directory_path):
            return found_files
        
        if recursive:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if (has_supported_extension(file_path, supported_extensions) and
                        is_file_accessible(file_path)):
                        found_files.append(file_path)
        else:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if (os.path.isfile(item_path) and
                    has_supported_extension(item_path, supported_extensions) and
                    is_file_accessible(item_path)):
                    found_files.append(item_path)
    
    except Exception as e:
        print(f"Error scanning directory {directory_path}: {e}")
    
    return found_files


def get_available_disk_space(path: str) -> int:
    """
    Get available disk space for a given path.
    
    Args:
        path: Path to check disk space for.
        
    Returns:
        Available disk space in bytes, or 0 if path doesn't exist.
    """
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path),
                ctypes.pointer(free_bytes),
                None,
                None
            )
            return free_bytes.value
        else:  # Unix-like systems
            statvfs = os.statvfs(path)
            return statvfs.f_frsize * statvfs.f_bavail
    except Exception:
        return 0


def create_output_directory(output_path: str) -> bool:
    """
    Create the output directory for a given output file path.
    
    Args:
        output_path: Full path to the output file.
        
    Returns:
        True if directory was created successfully, False otherwise.
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            return ensure_directory_exists(output_dir)
        return True
    except Exception as e:
        print(f"Error creating output directory for {output_path}: {e}")
        return False


def normalize_path(path: str) -> str:
    """
    Normalize a file path by resolving relative paths and converting separators.
    
    Args:
        path: File path to normalize.
        
    Returns:
        Normalized file path.
    """
    try:
        return os.path.normpath(os.path.abspath(path))
    except Exception:
        return path


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Get the relative path of a file from a base directory.
    
    Args:
        file_path: Full path to the file.
        base_path: Base directory path.
        
    Returns:
        Relative path from base directory to file.
    """
    try:
        return os.path.relpath(file_path, base_path)
    except Exception:
        return file_path


def estimate_processing_time(file_count: int, average_time_per_file: float = 2.0) -> str:
    """
    Estimate total processing time for a given number of files.
    
    Args:
        file_count: Number of files to process.
        average_time_per_file: Average processing time per file in seconds.
        
    Returns:
        Formatted time estimate string.
    """
    total_seconds = file_count * average_time_per_file
    
    if total_seconds < 60:
        return f"{int(total_seconds)}s"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"