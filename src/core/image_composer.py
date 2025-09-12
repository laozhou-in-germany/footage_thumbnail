"""
Image composer module for the Footage Thumbnailer application.

This module provides functionality to compose contact sheets from extracted thumbnails,
add text overlays with metadata, and arrange them in grid layouts.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

from core.thumbnail_extractor import VideoData, ThumbnailData
from utils.image_utils import (
    add_text_overlay_to_image,
    create_grid_layout,
    create_text_header,
    add_frame_to_image,
    format_duration,
    format_datetime,
    calculate_optimal_font_size,
    ensure_image_rgb,
    create_placeholder_image
)


@dataclass
class CompositionSettings:
    """Settings for image composition."""
    clips_per_row: int = 5
    padding: int = 5
    background_color: str = "white"
    font_size: int = 12
    text_color: str = "white"
    overlay_background_color: str = "black"
    overlay_background_opacity: float = 0.7
    overlay_position: str = "above_thumbnails"  # "on_thumbnails" or "above_thumbnails"
    show_filename: bool = True
    show_creation_date: bool = True
    show_duration: bool = True
    show_timestamp: bool = True
    # Frame/border settings
    show_frame: bool = True
    frame_color: str = "#CCCCCC"
    frame_thickness: int = 2
    frame_padding: int = 10
    # Multi-page settings
    max_rows_per_image: int = 0  # 0 = unlimited (single image)


class ImageComposer:
    """Composes contact sheets from video thumbnails and metadata."""
    
    def __init__(self, settings: Optional[CompositionSettings] = None):
        """
        Initialize the image composer.
        
        Args:
            settings: Composition settings. If None, uses default settings.
        """
        self.settings = settings if settings is not None else CompositionSettings()
    
    def create_contact_sheet(self, video_data_list: List[VideoData]) -> Image.Image:
        """
        Create a contact sheet from video data.
        
        Args:
            video_data_list: List of VideoData objects containing thumbnails.
            
        Returns:
            PIL Image object containing the contact sheet.
        """
        if not video_data_list:
            return create_placeholder_image(800, 600, "No Videos to Process")
        
        # Filter out videos with no thumbnails or errors
        valid_videos = [vd for vd in video_data_list 
                       if vd.processing_status == "success" and vd.thumbnails]
        
        if not valid_videos:
            return create_placeholder_image(800, 600, "No Valid Thumbnails Found")
        
        # Check if multi-page mode is enabled
        if self.settings.max_rows_per_image > 0:
            return self.create_multi_page_contact_sheets(valid_videos)
        else:
            return self.create_single_contact_sheet(valid_videos)
    
    def create_single_contact_sheet(self, video_data_list: List[VideoData]) -> Image.Image:
        """
        Create a single contact sheet from video data (original behavior).
        
        Args:
            video_data_list: List of VideoData objects containing thumbnails.
            
        Returns:
            PIL Image object containing the contact sheet.
        """
        # Process each video to create its thumbnail strip
        video_strips = []
        for video_data in video_data_list:
            try:
                strip = self._create_video_strip(video_data)
                if strip:
                    video_strips.append(strip)
            except Exception as e:
                print(f"Error creating strip for {video_data.file.filename}: {e}")
                continue
        
        if not video_strips:
            return create_placeholder_image(800, 600, "Failed to Create Thumbnails")
        
        # Arrange video strips in a grid layout
        contact_sheet = self._arrange_strips_in_grid(video_strips)
        
        return contact_sheet
    
    def create_multi_page_contact_sheets(self, video_data_list: List[VideoData]) -> Image.Image:
        """
        Create multiple contact sheet pages when max rows limit is exceeded.
        
        Args:
            video_data_list: List of VideoData objects containing thumbnails.
            
        Returns:
            PIL Image object containing the first page (additional pages saved separately).
        """
        # Process each video to create its thumbnail strip
        video_strips = []
        for video_data in video_data_list:
            try:
                strip = self._create_video_strip(video_data)
                if strip:
                    video_strips.append(strip)
            except Exception as e:
                print(f"Error creating strip for {video_data.file.filename}: {e}")
                continue
        
        if not video_strips:
            return create_placeholder_image(800, 600, "Failed to Create Thumbnails")
        
        # Calculate how many videos per page
        videos_per_row = self.settings.clips_per_row
        max_videos_per_page = videos_per_row * self.settings.max_rows_per_image
        
        # Split video strips into pages
        pages = []
        for i in range(0, len(video_strips), max_videos_per_page):
            page_strips = video_strips[i:i + max_videos_per_page]
            page_image = self._arrange_strips_in_grid(page_strips)
            pages.append(page_image)
        
        print(f"Generated {len(pages)} pages due to max_rows_per_image limit of {self.settings.max_rows_per_image}")
        
        # Store additional pages for later saving
        self._additional_pages = pages[1:] if len(pages) > 1 else []
        
        # Return the first page
        return pages[0] if pages else create_placeholder_image(800, 600, "No Pages Created")
    
    def get_additional_pages(self) -> List[Image.Image]:
        """
        Get additional pages created by multi-page mode.
        
        Returns:
            List of PIL Image objects for pages 2, 3, etc.
        """
        return getattr(self, '_additional_pages', [])
    
    def _create_video_strip(self, video_data: VideoData) -> Optional[Image.Image]:
        """
        Create a horizontal strip of thumbnails for a single video.
        
        Args:
            video_data: VideoData object containing thumbnails and metadata.
            
        Returns:
            PIL Image object containing the video strip, or None if creation fails.
        """
        if not video_data.thumbnails:
            return None
        
        try:
            # Process thumbnails based on overlay position setting
            if self.settings.overlay_position == "above_thumbnails":
                strip = self._create_video_strip_with_header(video_data)
            else:
                # Use the existing method for overlays on thumbnails
                strip = self._create_video_strip_with_overlays(video_data)
            
            # Add frame around the entire video strip if enabled
            if self.settings.show_frame and strip:
                strip = add_frame_to_image(
                    strip,
                    frame_color=self.settings.frame_color,
                    frame_thickness=self.settings.frame_thickness,
                    frame_padding=self.settings.frame_padding
                )
            
            return strip
                
        except Exception as e:
            print(f"Error creating video strip for {video_data.file.filename}: {e}")
            return None
    
    def _create_video_strip_with_overlays(self, video_data: VideoData) -> Image.Image:
        """
        Create a video strip with text overlays directly on thumbnails (original behavior).
        
        Args:
            video_data: VideoData object containing thumbnails and metadata.
            
        Returns:
            PIL Image object containing the video strip.
        """
        # Create thumbnails with overlays
        processed_thumbnails = []
        
        for i, thumbnail_data in enumerate(video_data.thumbnails):
            # Start with the base thumbnail image
            thumbnail_image = thumbnail_data.image.copy()
            
            # Ensure image is in RGB mode
            thumbnail_image = ensure_image_rgb(thumbnail_image)
            
            # Calculate optimal font size based on thumbnail width
            font_size = calculate_optimal_font_size(
                thumbnail_image.width, 
                self.settings.font_size
            )
            
            # Add overlays based on position
            if i == 0:  # First thumbnail - show filename and creation date
                if self.settings.show_filename:
                    thumbnail_image = add_text_overlay_to_image(
                        thumbnail_image,
                        video_data.file.filename,
                        "top-left",
                        font_size,
                        self.settings.text_color,
                        self.settings.overlay_background_color,
                        self.settings.overlay_background_opacity
                    )
                
                if self.settings.show_creation_date and video_data.metadata.creation_date:
                    date_str = format_datetime(video_data.metadata.creation_date)
                    if date_str:
                        thumbnail_image = add_text_overlay_to_image(
                            thumbnail_image,
                            date_str,
                            "top-right",
                            font_size,
                            self.settings.text_color,
                            self.settings.overlay_background_color,
                            self.settings.overlay_background_opacity
                        )
            
            elif i == len(video_data.thumbnails) - 1:  # Last thumbnail - show duration
                if self.settings.show_duration:
                    duration_str = format_duration(video_data.metadata.duration)
                    thumbnail_image = add_text_overlay_to_image(
                        thumbnail_image,
                        duration_str,
                        "bottom-right",
                        font_size,
                        self.settings.text_color,
                        self.settings.overlay_background_color,
                        self.settings.overlay_background_opacity
                    )
            
            # Add timestamp to all thumbnails if enabled
            if self.settings.show_timestamp:
                thumbnail_image = add_text_overlay_to_image(
                    thumbnail_image,
                    thumbnail_data.timestamp,
                    "bottom-left",
                    font_size,
                    self.settings.text_color,
                    self.settings.overlay_background_color,
                    self.settings.overlay_background_opacity
                )
            
            processed_thumbnails.append(thumbnail_image)
        
        # Create horizontal strip by concatenating thumbnails
        strip = self._create_horizontal_strip(processed_thumbnails)
        return strip
    
    def _create_video_strip_with_header(self, video_data: VideoData) -> Image.Image:
        """
        Create a video strip with text header above thumbnails.
        
        Args:
            video_data: VideoData object containing thumbnails and metadata.
            
        Returns:
            PIL Image object containing the video strip with header.
        """
        # Process thumbnails without overlays
        processed_thumbnails = []
        
        for i, thumbnail_data in enumerate(video_data.thumbnails):
            # Start with the base thumbnail image
            thumbnail_image = thumbnail_data.image.copy()
            
            # Ensure image is in RGB mode
            thumbnail_image = ensure_image_rgb(thumbnail_image)
            
            # Only add timestamp overlays if enabled (still on thumbnails for time reference)
            if self.settings.show_timestamp:
                font_size = calculate_optimal_font_size(
                    thumbnail_image.width, 
                    self.settings.font_size
                )
                thumbnail_image = add_text_overlay_to_image(
                    thumbnail_image,
                    thumbnail_data.timestamp,
                    "bottom-left",
                    font_size,
                    self.settings.text_color,
                    self.settings.overlay_background_color,
                    self.settings.overlay_background_opacity
                )
            
            processed_thumbnails.append(thumbnail_image)
        
        # Create horizontal strip by concatenating thumbnails
        thumbnail_strip = self._create_horizontal_strip(processed_thumbnails)
        
        # Create text header with metadata
        header_parts = []
        
        if self.settings.show_filename:
            header_parts.append(video_data.file.filename)
        
        if self.settings.show_creation_date and video_data.metadata.creation_date:
            date_str = format_datetime(video_data.metadata.creation_date)
            if date_str:
                header_parts.append(date_str)
        
        if self.settings.show_duration:
            duration_str = format_duration(video_data.metadata.duration)
            header_parts.append(f"Duration: {duration_str}")
        
        # Combine header parts
        header_text = "  |  ".join(header_parts) if header_parts else ""
        
        # Create text header
        header_image = create_text_header(
            header_text,
            thumbnail_strip.width,
            self.settings.font_size,
            self.settings.text_color,
            self.settings.background_color,
            padding=5
        )
        
        # Combine header and thumbnails vertically
        total_height = header_image.height + thumbnail_strip.height
        
        # Determine background color
        if self.settings.background_color.lower() == "white":
            bg_color = (255, 255, 255)
        elif self.settings.background_color.lower() == "black":
            bg_color = (0, 0, 0)
        else:
            bg_color = (255, 255, 255)  # Default to white
            
        combined_strip = Image.new('RGB', (thumbnail_strip.width, total_height), bg_color)
        
        # Paste header at top
        combined_strip.paste(header_image, (0, 0))
        
        # Paste thumbnail strip below header
        combined_strip.paste(thumbnail_strip, (0, header_image.height))
        
        return combined_strip
    
    def _create_horizontal_strip(self, thumbnails: List[Image.Image]) -> Image.Image:
        """
        Create a horizontal strip from a list of thumbnail images.
        
        Args:
            thumbnails: List of PIL Image objects to arrange horizontally.
            
        Returns:
            PIL Image object containing the horizontal strip.
        """
        if not thumbnails:
            return create_placeholder_image(320, 180, "No Thumbnails")
        
        # Ensure all thumbnails have the same height
        max_height = max(img.height for img in thumbnails)
        
        # Resize thumbnails to same height if needed
        normalized_thumbnails = []
        for img in thumbnails:
            if img.height != max_height:
                aspect_ratio = img.width / img.height
                new_width = int(max_height * aspect_ratio)
                img = img.resize((new_width, max_height), Image.Resampling.LANCZOS)
            normalized_thumbnails.append(img)
        
        # Calculate total width
        total_width = sum(img.width for img in normalized_thumbnails)
        total_width += (len(normalized_thumbnails) - 1) * self.settings.padding
        
        # Create the strip image
        if self.settings.background_color.lower() == "white":
            bg_color = (255, 255, 255)
        elif self.settings.background_color.lower() == "black":
            bg_color = (0, 0, 0)
        else:
            bg_color = (255, 255, 255)  # Default to white
        
        strip = Image.new('RGB', (total_width, max_height), bg_color)
        
        # Paste thumbnails
        x_offset = 0
        for img in normalized_thumbnails:
            strip.paste(img, (x_offset, 0))
            x_offset += img.width + self.settings.padding
        
        return strip
    
    def _arrange_strips_in_grid(self, strips: List[Image.Image]) -> Image.Image:
        """
        Arrange video strips in a grid layout.
        
        Args:
            strips: List of PIL Image objects representing video strips.
            
        Returns:
            PIL Image object containing the final contact sheet.
        """
        if not strips:
            return create_placeholder_image(800, 600, "No Strips to Arrange")
        
        # Calculate grid dimensions
        total_strips = len(strips)
        strips_per_row = min(self.settings.clips_per_row, total_strips)
        num_rows = math.ceil(total_strips / strips_per_row)
        
        # Find the maximum dimensions
        max_width = max(strip.width for strip in strips)
        max_height = max(strip.height for strip in strips)
        
        # Resize all strips to have the same width (keep aspect ratio)
        normalized_strips = []
        for strip in strips:
            if strip.width != max_width:
                aspect_ratio = strip.height / strip.width
                new_height = int(max_width * aspect_ratio)
                strip = strip.resize((max_width, new_height), Image.Resampling.LANCZOS)
            normalized_strips.append(strip)
        
        # Recalculate max height after normalization
        max_height = max(strip.height for strip in normalized_strips)
        
        # Calculate total grid size
        grid_width = (strips_per_row * max_width) + ((strips_per_row + 1) * self.settings.padding)
        grid_height = (num_rows * max_height) + ((num_rows + 1) * self.settings.padding)
        
        # Create the grid image
        if self.settings.background_color.lower() == "white":
            bg_color = (255, 255, 255)
        elif self.settings.background_color.lower() == "black":
            bg_color = (0, 0, 0)
        else:
            bg_color = (255, 255, 255)  # Default to white
        
        grid_image = Image.new('RGB', (grid_width, grid_height), bg_color)
        
        # Place strips in the grid
        for i, strip in enumerate(normalized_strips):
            row = i // strips_per_row
            col = i % strips_per_row
            
            x = self.settings.padding + (col * (max_width + self.settings.padding))
            y = self.settings.padding + (row * (max_height + self.settings.padding))
            
            # Center the strip vertically if it's smaller than max_height
            if strip.height < max_height:
                y += (max_height - strip.height) // 2
            
            grid_image.paste(strip, (x, y))
        
        return grid_image
    
    def calculate_grid_dimensions(self, video_count: int, clips_per_row: int) -> Tuple[int, int]:
        """
        Calculate grid dimensions for a given number of videos.
        
        Args:
            video_count: Number of videos to arrange.
            clips_per_row: Number of video clips per row.
            
        Returns:
            Tuple of (columns, rows) for the grid.
        """
        if video_count <= 0:
            return (0, 0)
        
        columns = min(clips_per_row, video_count)
        rows = math.ceil(video_count / clips_per_row)
        
        return (columns, rows)
    
    def estimate_output_size(
        self, 
        video_count: int, 
        thumbnail_width: int,
        positions_count: int
    ) -> Tuple[int, int]:
        """
        Estimate the output image size for given parameters.
        
        Args:
            video_count: Number of videos to process.
            thumbnail_width: Width of individual thumbnails.
            positions_count: Number of thumbnail positions per video.
            
        Returns:
            Tuple of (estimated_width, estimated_height) in pixels.
        """
        if video_count <= 0:
            return (800, 600)  # Default size
        
        # Estimate thumbnail height (assume 16:9 aspect ratio)
        thumbnail_height = int(thumbnail_width * 9 / 16)
        
        # Calculate strip dimensions
        strip_width = (positions_count * thumbnail_width) + ((positions_count - 1) * self.settings.padding)
        strip_height = thumbnail_height
        
        # Calculate grid dimensions
        columns, rows = self.calculate_grid_dimensions(video_count, self.settings.clips_per_row)
        
        # Calculate total size
        total_width = (columns * strip_width) + ((columns + 1) * self.settings.padding)
        total_height = (rows * strip_height) + ((rows + 1) * self.settings.padding)
        
        return (total_width, total_height)
    
    def update_settings(self, **kwargs) -> None:
        """
        Update composition settings.
        
        Args:
            **kwargs: Settings to update (clips_per_row, padding, background_color, etc.).
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
    
    def create_summary_overlay(self, video_data_list: List[VideoData]) -> Image.Image:
        """
        Create a summary overlay with statistics about the processed videos.
        
        Args:
            video_data_list: List of VideoData objects.
            
        Returns:
            PIL Image object containing the summary overlay.
        """
        # Calculate statistics
        total_videos = len(video_data_list)
        successful_videos = len([vd for vd in video_data_list if vd.processing_status == "success"])
        failed_videos = total_videos - successful_videos
        total_duration = sum(vd.metadata.duration for vd in video_data_list 
                           if vd.processing_status == "success")
        
        # Format duration
        duration_str = format_duration(total_duration)
        
        # Create summary text
        summary_lines = [
            f"Total Videos: {total_videos}",
            f"Processed: {successful_videos}",
            f"Failed: {failed_videos}",
            f"Total Duration: {duration_str}"
        ]
        
        # Calculate required image size
        font_size = 14
        line_height = 20
        margin = 10
        
        max_line_width = 300  # Estimate
        overlay_width = max_line_width + (2 * margin)
        overlay_height = (len(summary_lines) * line_height) + (2 * margin)
        
        # Create overlay image
        overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 128))
        draw = ImageDraw.Draw(overlay)
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        
        # Draw text lines
        y_offset = margin
        for line in summary_lines:
            draw.text((margin, y_offset), line, font=font, fill=(255, 255, 255, 255))
            y_offset += line_height
        
        return overlay
    
    def add_watermark(self, image: Image.Image, watermark_text: str) -> Image.Image:
        """
        Add a watermark to an image.
        
        Args:
            image: PIL Image object to add watermark to.
            watermark_text: Text to use as watermark.
            
        Returns:
            PIL Image object with watermark added.
        """
        if not watermark_text.strip():
            return image
        
        # Create a copy of the image
        watermarked = image.copy()
        
        # Create watermark overlay
        watermark_overlay = add_text_overlay_to_image(
            watermarked,
            watermark_text,
            "bottom-right",
            self.settings.font_size,
            self.settings.text_color,
            self.settings.overlay_background_color,
            0.3,  # Lower opacity for watermark
            10    # Larger margin
        )
        
        return watermark_overlay