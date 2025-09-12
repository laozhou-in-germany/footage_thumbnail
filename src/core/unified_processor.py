"""
Unified Processing Workflow for the Footage Thumbnailer application.

This module provides a unified interface that handles both timeline-based and 
folder-based thumbnail generation workflows seamlessly.
"""

import os
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from .config_manager import ConfigManager
from .video_scanner import VideoScanner, VideoFile
from .thumbnail_extractor import ThumbnailExtractor, VideoData, VideoMetadata
from .image_composer import ImageComposer, CompositionSettings
from .fcpxml_parser import FCPXMLParser
from .timeline_data_models import TimelineEntry


class UnifiedProcessor:
    """Unified processor for both timeline and folder-based workflows."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the unified processor.
        
        Args:
            config_manager: Configuration manager instance.
        """
        self.config_manager = config_manager
        
        # Standard components
        self.video_scanner = None
        self.thumbnail_extractor = None
        self.image_composer = None
        
        # Timeline components
        self.timeline_parser = None
        
        # Progress tracking
        self.progress_callback = None
        self.log_callback = None
    
    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """
        Set progress reporting callback.
        
        Args:
            callback: Function to call with (progress, message).
        """
        self.progress_callback = callback
    
    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set logging callback.
        
        Args:
            callback: Function to call with log messages.
        """
        self.log_callback = callback
    
    def _report_progress(self, progress: float, message: str) -> None:
        """Report progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def _log_message(self, message: str) -> None:
        """Log message if callback is set."""
        if self.log_callback:
            self.log_callback(message)
    
    def process_thumbnails(self) -> bool:
        """
        Process thumbnails using unified workflow.
        
        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            config = self.config_manager.load_config()
            
            # Determine processing mode based on timeline file presence
            if self._is_timeline_mode(config):
                self._log_message("FCPXML mode detected - processing based on FCPXML file")
                return self._process_fcpxml_mode(config)
            else:
                self._log_message("Standard mode - processing based on source folders")
                return self._process_folder_mode(config)
        
        except Exception as e:
            self._log_message(f"Error in unified processing: {e}")
            return False
    
    def _is_timeline_mode(self, config: Dict[str, Any]) -> bool:
        """
        Check if timeline mode should be used.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            True if timeline mode should be used, False otherwise.
        """
        timeline_path = config.get('fcpxml_file_path', '')
        if not timeline_path or not os.path.exists(timeline_path) or not os.path.isfile(timeline_path):
            return False
        
        # Check file extension to determine type
        file_extension = Path(timeline_path).suffix.lower()
        return file_extension == '.fcpxml'
    
    def _process_fcpxml_mode(self, config: Dict[str, Any]) -> bool:
        """
        Process thumbnails based on FCPXML file.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            self._report_progress(0.05, "Parsing FCPXML file...")
            
            # Initialize timeline components
            self.timeline_parser = FCPXMLParser()
            
            # Parse FCPXML file
            fcpxml_path = config['fcpxml_file_path']
            timeline_entries = self.timeline_parser.parse_fcpxml_file(fcpxml_path)
            
            if not timeline_entries:
                self._log_message("No video entries found in timeline file")
                self._report_progress(1.0, "No video entries found")
                return False
            
            self._log_message(f"Found {len(timeline_entries)} video entries in FCPXML file")
            self._report_progress(0.1, f"Found {len(timeline_entries)} FCPXML entries")
            
            # Check if we should use unique files (when fcpxml_use_interval_positions is False)
            use_interval_positions = config.get('fcpxml_use_interval_positions', True)
            
            if not use_interval_positions:
                # When not using interval positions, process each unique file only once
                unique_files = self.timeline_parser.get_unique_files(timeline_entries)
                self._log_message(f"Processing {len(unique_files)} unique video files (ignoring timeline clips)")
                
                # Create simplified timeline entries for each unique file
                unique_entries = []
                for i, file_path in enumerate(unique_files, 1):
                    # Find the first entry for this file to get basic info
                    original_entry = next((entry for entry in timeline_entries if entry.file_path == file_path), None)
                    
                    # Create a simplified entry for the entire file
                    simplified_entry = TimelineEntry(
                        source_id=i,
                        file_path=file_path,
                        media_type="VIDEO",
                        start_time=0.0,
                        end_time=None,  # Will be determined during processing
                        clip_start_time=None,  # Not applicable when processing entire file
                        clip_end_time=None     # Not applicable when processing entire file
                    )
                    unique_entries.append(simplified_entry)
                
                timeline_entries = unique_entries
                self._log_message(f"Reduced to {len(timeline_entries)} entries for processing")
            
            # For FCPXML files, we validate file paths directly since they contain absolute paths
            self._report_progress(0.15, "Validating video files...")
            video_matches = self._validate_fcpxml_files(timeline_entries)
            
            # Report matching statistics
            match_stats = self._get_match_statistics(video_matches)
            matched_count = match_stats['matched_entries']
            missing_count = match_stats['missing_entries']
            
            self._log_message(
                f"Video validation complete: {matched_count} found, {missing_count} missing "
                f"(match rate: {match_stats['match_rate']:.1%})"
            )
            
            if matched_count == 0 and not config.get('fcpxml_show_placeholders', True):
                self._log_message("No video files found and placeholders are disabled")
                self._report_progress(1.0, "No videos found")
                return False
            
            self._report_progress(0.2, "Extracting thumbnails...")
            
            # Extract thumbnails using existing thumbnail extractor
            self.thumbnail_extractor = ThumbnailExtractor()
            
            # Extract thumbnails
            positions = config.get('positions', '0%,50%,99%').split(',')
            thumbnail_width = config.get('thumbnail_width', 320)
            
            timeline_video_data = self._extract_fcpxml_thumbnails(
                video_matches, positions, thumbnail_width, use_interval_positions
            )
            
            # Filter out placeholders if disabled
            if not config.get('fcpxml_show_placeholders', True):
                timeline_video_data = [data for data in timeline_video_data if not data.is_placeholder]
            
            if not timeline_video_data:
                self._log_message("No video data available for processing")
                self._report_progress(1.0, "No video data")
                return False
            
            # Report extraction statistics
            extraction_stats = self._get_timeline_processing_statistics(timeline_video_data)
            self._log_message(
                f"Thumbnail extraction complete: {extraction_stats['successful_extractions']} successful, "
                f"{extraction_stats['placeholder_count']} placeholders, "
                f"{extraction_stats['total_thumbnails']} total thumbnails"
            )
            
            self._report_progress(0.8, "Composing contact sheet...")
            
            # Create contact sheet
            success = self._create_contact_sheet(timeline_video_data, config)
            
            if success:
                self._report_progress(1.0, "FCPXML processing complete!")
                self._log_message(f"Successfully processed {len(timeline_video_data)} videos from FCPXML")
            
            return success
            
        except Exception as e:
            self._log_message(f"Error in FCPXML processing: {e}")
            self._report_progress(1.0, "FCPXML processing failed")
            return False
    
    def _validate_fcpxml_files(self, timeline_entries) -> List:
        """
        Validate FCPXML-referenced files directly (no scanning needed).
        
        Args:
            timeline_entries: List of timeline entries with absolute file paths.
            
        Returns:
            List of video match objects with validation results.
        """
        matches = []
        
        for entry in timeline_entries:
            # Check if the file exists
            if os.path.exists(entry.file_path) and os.path.isfile(entry.file_path):
                match = {
                    'timeline_entry': entry,
                    'matched_file_path': entry.file_path,
                    'is_found': True,
                    'similarity_score': 1.0
                }
            else:
                match = {
                    'timeline_entry': entry,
                    'is_found': False,
                    'error_message': f"Video file not found: {entry.file_path}"
                }
            
            matches.append(match)
        
        return matches
    
    def _get_match_statistics(self, video_matches: List) -> Dict[str, Any]:
        """
        Get statistics for video matching.
        
        Args:
            video_matches: List of video match objects.
            
        Returns:
            Dictionary with matching statistics.
        """
        matched_entries = sum(1 for match in video_matches if match.get('is_found', False))
        missing_entries = len(video_matches) - matched_entries
        total_entries = len(video_matches)
        
        match_rate = matched_entries / total_entries if total_entries > 0 else 0.0
        
        return {
            'matched_entries': matched_entries,
            'missing_entries': missing_entries,
            'total_entries': total_entries,
            'match_rate': match_rate
        }
    
    def _extract_fcpxml_thumbnails(self, video_matches: List, positions: List[str], 
                                   thumbnail_width: int, use_interval_positions: bool) -> List:
        """
        Extract thumbnails from FCPXML-referenced videos.
        
        Args:
            video_matches: List of video match objects.
            positions: List of position strings.
            thumbnail_width: Width for thumbnails.
            use_interval_positions: Whether to use FCPXML in/out points.
            
        Returns:
            List of video data objects.
        """
        video_data_list = []
        
        # Ensure thumbnail extractor is initialized
        if self.thumbnail_extractor is None:
            self.thumbnail_extractor = ThumbnailExtractor()
        
        for match in video_matches:
            if not match.get('is_found', False):
                # Create placeholder if enabled
                if self.config_manager.get('fcpxml_show_placeholders', True):
                    placeholder_data = self._create_placeholder_video_data(match)
                    video_data_list.append(placeholder_data)
                continue
            
            try:
                file_path = match['matched_file_path']
                entry = match['timeline_entry']
                
                # Create a proper VideoFile object
                video_file = VideoFile(
                    path=file_path,
                    filename=os.path.basename(file_path),
                    size=0,  # Will be determined during processing
                    modified_date=None,  # Will be determined during processing
                    is_accessible=True  # Assume accessible since we found the file
                )
                
                if use_interval_positions and entry.clip_start_time is not None and entry.clip_end_time is not None:
                    # Use clip in/out points for positions (extract from specific segment of footage)
                    clip_duration = entry.clip_end_time - entry.clip_start_time
                    adjusted_positions = []
                    for pos in positions:
                        if pos.endswith('%'):
                            percent = float(pos[:-1])
                            # Calculate each position individually within the clip's time range
                            actual_time = entry.clip_start_time + (clip_duration * percent / 100)
                            adjusted_positions.append(f"{actual_time}s")
                        else:
                            # Handle absolute time positions - might need adjustment based on clip start
                            adjusted_positions.append(pos)
                    video_data = self.thumbnail_extractor.process_video_file(
                        video_file, adjusted_positions, thumbnail_width
                    )
                else:
                    # Use absolute positions (existing behavior)
                    video_data = self.thumbnail_extractor.process_video_file(
                        video_file, positions, thumbnail_width
                    )
                
                if video_data and video_data.processing_status == "success":
                    # Add timeline-specific metadata using a dictionary approach since we can't directly assign attributes
                    setattr(video_data, 'source_id', entry.source_id)
                    setattr(video_data, 'start_time', entry.start_time)
                    setattr(video_data, 'end_time', entry.end_time)
                    setattr(video_data, 'clip_start_time', entry.clip_start_time)
                    setattr(video_data, 'clip_end_time', entry.clip_end_time)
                    setattr(video_data, 'is_placeholder', False)
                    video_data_list.append(video_data)
                else:
                    # Handle extraction failure - create placeholder if enabled
                    self._log_message(f"Failed to extract thumbnails from: {file_path}")
                    if self.config_manager.get('fcpxml_show_placeholders', True):
                        placeholder_data = self._create_placeholder_video_data(match)
                        video_data_list.append(placeholder_data)
                    
            except Exception as e:
                self._log_message(f"Error processing {match.get('matched_file_path', 'unknown')}: {e}")
                # Create placeholder for error cases if enabled
                if self.config_manager.get('fcpxml_show_placeholders', True):
                    placeholder_data = self._create_placeholder_video_data(match)
                    video_data_list.append(placeholder_data)
                continue
        
        return video_data_list
    
    def _create_placeholder_video_data(self, match: Dict) -> object:
        """
        Create placeholder video data for missing files.
        
        Args:
            match: Video match object for missing file.
            
        Returns:
            Placeholder video data object.
        """
        entry = match['timeline_entry']
        
        # Create a basic VideoFile object for the placeholder
        video_file = VideoFile(
            path=entry.file_path,
            filename=os.path.basename(entry.file_path),
            size=0,
            modified_date=None,
            is_accessible=False
        )
        
        # Create a basic VideoData object
        placeholder_data = VideoData(
            file=video_file,
            metadata=VideoMetadata(0, None, (0, 0), 0, "unknown", "unknown"),
            thumbnails=[],
            processing_status="placeholder",
            error_message=match.get('error_message', 'File not found')
        )
        
        # Add timeline-specific metadata using setattr
        setattr(placeholder_data, 'source_id', entry.source_id)
        setattr(placeholder_data, 'start_time', entry.start_time)
        setattr(placeholder_data, 'end_time', entry.end_time)
        setattr(placeholder_data, 'clip_start_time', entry.clip_start_time)
        setattr(placeholder_data, 'clip_end_time', entry.clip_end_time)
        setattr(placeholder_data, 'is_placeholder', True)
        
        return placeholder_data
    
    def _get_timeline_processing_statistics(self, timeline_video_data: List) -> Dict[str, Any]:
        """
        Get processing statistics for timeline video data.
        
        Args:
            timeline_video_data: List of timeline video data objects.
            
        Returns:
            Dictionary with processing statistics.
        """
        successful_extractions = sum(1 for data in timeline_video_data if not getattr(data, 'is_placeholder', False))
        placeholder_count = sum(1 for data in timeline_video_data if getattr(data, 'is_placeholder', False))
        total_thumbnails = sum(len(getattr(data, 'thumbnails', [])) for data in timeline_video_data)
        
        return {
            'successful_extractions': successful_extractions,
            'placeholder_count': placeholder_count,
            'total_thumbnails': total_thumbnails
        }
    
    def _process_folder_mode(self, config: Dict[str, Any]) -> bool:
        """
        Process thumbnails based on source folders (existing workflow).
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            self._report_progress(0.05, "Scanning folders...")
            
            # Initialize standard components
            supported_extensions = config.get('supported_extensions', [])
            self.video_scanner = VideoScanner(supported_extensions)
            self.thumbnail_extractor = ThumbnailExtractor()
            
            # Scan for videos
            source_folders = config.get('source_folders', [])
            if not source_folders:
                self._log_message("No source folders specified")
                self._report_progress(1.0, "No source folders")
                return False
            
            video_files = self.video_scanner.scan_folders(source_folders)
            
            if not video_files:
                self._log_message("No video files found in source folders")
                self._report_progress(1.0, "No videos found")
                return False
            
            accessible_files = self.video_scanner.filter_accessible_files(video_files)
            if not accessible_files:
                self._log_message("No accessible video files found")
                self._report_progress(1.0, "No accessible videos")
                return False
            
            self._log_message(f"Found {len(accessible_files)} accessible video files")
            self._report_progress(0.1, f"Found {len(accessible_files)} videos")
            
            # Extract thumbnails
            video_data_list = []
            total_videos = len(accessible_files)
            
            for i, video_file in enumerate(accessible_files):
                try:
                    progress = 0.1 + (i / total_videos) * 0.7  # 10% to 80% for extraction
                    self._report_progress(progress, f"Processing {video_file.filename}")
                    self._log_message(f"Processing: {video_file.filename}")
                    
                    # Extract video data
                    positions = config.get('positions', '0%,50%,99%').split(',')
                    video_data = self.thumbnail_extractor.process_video_file(
                        video_file,
                        positions,
                        config.get('thumbnail_width', 320)
                    )
                    
                    if video_data and video_data.processing_status == "success":
                        video_data_list.append(video_data)
                        self._log_message(f"Extracted {len(video_data.thumbnails)} thumbnails from {video_file.filename}")
                    else:
                        self._log_message(f"Failed to process: {video_file.filename}")
                        
                except Exception as e:
                    self._log_message(f"Error processing {video_file.filename}: {e}")
                    continue
            
            if not video_data_list:
                self._log_message("No thumbnails could be extracted")
                self._report_progress(1.0, "No thumbnails extracted")
                return False
            
            self._report_progress(0.8, "Composing contact sheet...")
            
            # Create contact sheet
            success = self._create_contact_sheet(video_data_list, config)
            
            if success:
                self._report_progress(1.0, "Processing complete!")
                self._log_message(f"Successfully processed {len(video_data_list)} videos")
            
            return success
            
        except Exception as e:
            self._log_message(f"Error in folder processing: {e}")
            self._report_progress(1.0, "Folder processing failed")
            return False
    
    def _create_contact_sheet(self, video_data_list: List, config: Dict[str, Any]) -> bool:
        """
        Create and save contact sheet from video data.
        
        Args:
            video_data_list: List of video data objects.
            config: Configuration dictionary.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Configure image composer settings
            composition_settings = CompositionSettings(
                clips_per_row=config.get('clips_per_row', 5),
                padding=config.get('padding', 5),
                background_color=config.get('background_color', 'white'),
                font_size=config.get('font_size', 12),
                text_color=config.get('text_color', 'black'),
                overlay_background_color=config.get('overlay_background_color', 'black'),
                overlay_background_opacity=config.get('overlay_background_opacity', 0.7),
                overlay_position=config.get('overlay_position', 'above_thumbnails'),
                show_frame=config.get('show_frame', True),
                frame_color=config.get('frame_color', '#CCCCCC'),
                frame_thickness=config.get('frame_thickness', 2),
                frame_padding=config.get('frame_padding', 10),
                max_rows_per_image=config.get('max_rows_per_image', 0)
            )
            
            self.image_composer = ImageComposer(composition_settings)
            contact_sheet = self.image_composer.create_contact_sheet(video_data_list)
            
            # Save image
            self._report_progress(0.9, "Saving image...")
            output_path = config.get('output_path', 'output/overview.jpg')
            
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine format
            if output_path.lower().endswith('.png'):
                image_format = 'PNG'
            else:
                image_format = 'JPEG'
            
            contact_sheet.save(output_path, format=image_format, quality=95)
            self._log_message(f"Saved contact sheet to: {output_path}")
            
            # Handle additional pages if any
            additional_pages = self.image_composer.get_additional_pages()
            if additional_pages:
                self._log_message(f"Saving {len(additional_pages)} additional pages...")
                
                base_path = Path(output_path)
                base_name = base_path.stem
                extension = base_path.suffix
                
                for i, page in enumerate(additional_pages, 2):
                    page_path = base_path.parent / f"{base_name}_page{i:02d}{extension}"
                    page.save(str(page_path), format=image_format, quality=95)
                    self._log_message(f"Saved page {i} to: {page_path}")
            
            return True
            
        except Exception as e:
            self._log_message(f"Error creating contact sheet: {e}")
            return False
    
    def get_processing_mode(self) -> str:
        """
        Get the current processing mode.
        
        Returns:
            "fcpxml" or "folder" based on the current configuration.
        """
        config = self.config_manager.load_config()
        fcpxml_path = config.get('fcpxml_file_path', '')
        
        if fcpxml_path and os.path.exists(fcpxml_path) and os.path.isfile(fcpxml_path):
            file_extension = Path(fcpxml_path).suffix.lower()
            if file_extension == '.fcpxml':
                return "fcpxml"
        
        return "folder"
    
    def validate_configuration(self) -> tuple[bool, List[str]]:
        """
        Validate the current configuration for processing.
        
        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []
        config = self.config_manager.load_config()
        
        # Check source folders
        source_folders = config.get('source_folders', [])
        if not source_folders:
            errors.append("No source folders specified")
        else:
            for folder in source_folders:
                if not os.path.exists(folder):
                    errors.append(f"Source folder does not exist: {folder}")
        
        # Check output path
        output_path = config.get('output_path', '')
        if not output_path:
            errors.append("No output path specified")
        else:
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create output directory: {e}")
        
        # Check FCPXML-specific configuration if in FCPXML mode
        if self._is_timeline_mode(config):
            fcpxml_valid, fcpxml_errors = self.config_manager.validate_fcpxml_config()
            if not fcpxml_valid:
                errors.extend(fcpxml_errors)
        
        return len(errors) == 0, errors