"""
Image processing utility functions for the Footage Thumbnailer application.

This module provides utilities for image manipulation, text overlay creation,
and thumbnail processing using the Pillow library.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional, List
import os
import math


def resize_image_proportional(image: Image.Image, target_width: int) -> Image.Image:
    """
    Resize an image proportionally to a target width.
    
    Args:
        image: PIL Image object to resize.
        target_width: Target width in pixels.
        
    Returns:
        Resized PIL Image object.
    """
    original_width, original_height = image.size
    aspect_ratio = original_height / original_width
    target_height = int(target_width * aspect_ratio)
    
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def create_text_overlay(
    text: str,
    font_size: int = 12,
    text_color: str = "white",
    background_color: str = "black",
    background_opacity: float = 0.7,
    padding: int = 4
) -> Image.Image:
    """
    Create a text overlay image with semi-transparent background.
    
    Args:
        text: Text to render.
        font_size: Font size in pixels.
        text_color: Color of the text.
        background_color: Color of the background.
        background_opacity: Opacity of the background (0.0 to 1.0).
        padding: Padding around text in pixels.
        
    Returns:
        PIL Image object containing the text overlay.
    """
    try:
        # Try to load a system font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("calibri.ttf", font_size)
            except OSError:
                # Fallback to default font
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Create a temporary image to measure text size
    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Get text bounding box
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Create the overlay image
    overlay_width = int(text_width + (padding * 2))
    overlay_height = int(text_height + (padding * 2))
    
    # Create background with opacity
    background_alpha = int(255 * background_opacity)
    overlay = Image.new('RGBA', (overlay_width, overlay_height), 
                       (0, 0, 0, 0))  # Transparent background
    
    # Draw semi-transparent background
    draw = ImageDraw.Draw(overlay)
    if background_color.lower() == "black":
        bg_color = (0, 0, 0, background_alpha)
    elif background_color.lower() == "white":
        bg_color = (255, 255, 255, background_alpha)
    else:
        # Parse hex color if provided
        try:
            if background_color.startswith('#'):
                hex_color = background_color[1:]
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                bg_color = (*rgb, background_alpha)
            else:
                bg_color = (0, 0, 0, background_alpha)  # Default to black
        except Exception:
            bg_color = (0, 0, 0, background_alpha)
    
    draw.rectangle([0, 0, overlay_width, overlay_height], fill=bg_color)
    
    # Draw text
    if text_color.lower() == "white":
        text_rgba = (255, 255, 255, 255)
    elif text_color.lower() == "black":
        text_rgba = (0, 0, 0, 255)
    else:
        # Parse hex color if provided
        try:
            if text_color.startswith('#'):
                hex_color = text_color[1:]
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                text_rgba = (*rgb, 255)
            else:
                text_rgba = (255, 255, 255, 255)  # Default to white
        except Exception:
            text_rgba = (255, 255, 255, 255)
    
    draw.text((padding, padding), text, font=font, fill=text_rgba)
    
    return overlay


def add_text_overlay_to_image(
    image: Image.Image,
    text: str,
    position: str = "top-left",
    font_size: int = 12,
    text_color: str = "white",
    background_color: str = "black",
    background_opacity: float = 0.7,
    margin: int = 5
) -> Image.Image:
    """
    Add a text overlay to an image at the specified position.
    
    Args:
        image: PIL Image object to add overlay to.
        text: Text to overlay.
        position: Position for the overlay ("top-left", "top-right", "bottom-left", "bottom-right").
        font_size: Font size in pixels.
        text_color: Color of the text.
        background_color: Color of the background.
        background_opacity: Opacity of the background (0.0 to 1.0).
        margin: Margin from image edges in pixels.
        
    Returns:
        PIL Image object with text overlay added.
    """
    if not text.strip():
        return image.copy()
    
    # Create text overlay
    text_overlay = create_text_overlay(
        text, font_size, text_color, background_color, background_opacity
    )
    
    # Create a copy of the original image
    result_image = image.copy()
    if result_image.mode != 'RGBA':
        result_image = result_image.convert('RGBA')
    
    # Calculate position
    img_width, img_height = result_image.size
    overlay_width, overlay_height = text_overlay.size
    
    if position == "top-left":
        x, y = margin, margin
    elif position == "top-right":
        x, y = img_width - overlay_width - margin, margin
    elif position == "bottom-left":
        x, y = margin, img_height - overlay_height - margin
    elif position == "bottom-right":
        x, y = img_width - overlay_width - margin, img_height - overlay_height - margin
    else:
        # Default to top-left
        x, y = margin, margin
    
    # Composite the overlay onto the image
    result_image.paste(text_overlay, (x, y), text_overlay)
    
    return result_image


def create_grid_layout(
    images: List[Image.Image],
    clips_per_row: int,
    padding: int = 5,
    background_color: str = "white"
) -> Image.Image:
    """
    Arrange images in a grid layout.
    
    Args:
        images: List of PIL Image objects to arrange.
        clips_per_row: Number of images per row.
        padding: Padding between images in pixels.
        background_color: Background color for the grid.
        
    Returns:
        PIL Image object containing the grid layout.
    """
    if not images:
        return Image.new('RGB', (100, 100), background_color)
    
    # Calculate grid dimensions
    num_images = len(images)
    num_rows = math.ceil(num_images / clips_per_row)
    
    # Assume all images have the same size (they should be resized beforehand)
    img_width, img_height = images[0].size
    
    # Calculate total grid size
    grid_width = (clips_per_row * img_width) + ((clips_per_row + 1) * padding)
    grid_height = (num_rows * img_height) + ((num_rows + 1) * padding)
    
    # Create the grid image
    if background_color.lower() == "white":
        bg_color = (255, 255, 255)
    elif background_color.lower() == "black":
        bg_color = (0, 0, 0)
    else:
        # Parse hex color if provided
        try:
            if background_color.startswith('#'):
                hex_color = background_color[1:]
                bg_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                bg_color = (255, 255, 255)  # Default to white
        except Exception:
            bg_color = (255, 255, 255)
    
    grid_image = Image.new('RGB', (grid_width, grid_height), bg_color)
    
    # Place images in the grid
    for i, img in enumerate(images):
        row = i // clips_per_row
        col = i % clips_per_row
        
        x = padding + (col * (img_width + padding))
        y = padding + (row * (img_height + padding))
        
        # Convert image to RGB if it's RGBA
        if img.mode == 'RGBA':
            # Create a white background and composite the RGBA image onto it
            background = Image.new('RGB', img.size, bg_color)
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        grid_image.paste(img, (x, y))
    
    return grid_image


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to MM:SS or HH:MM:SS format.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string.
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_datetime(dt) -> str:
    """
    Format datetime object to string for overlay display.
    
    Args:
        dt: datetime object to format.
        
    Returns:
        Formatted datetime string.
    """
    if dt is None:
        return ""
    
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def calculate_optimal_font_size(image_width: int, base_font_size: int = 12) -> int:
    """
    Calculate optimal font size based on image width.
    
    Args:
        image_width: Width of the image in pixels.
        base_font_size: Base font size to scale from.
        
    Returns:
        Optimal font size in pixels.
    """
    # Scale font size based on image width
    # Base calculation: 12px font for 320px width
    scale_factor = image_width / 320.0
    optimal_size = int(base_font_size * scale_factor)
    
    # Clamp between reasonable bounds
    return max(8, min(optimal_size, 24))


def ensure_image_rgb(image: Image.Image) -> Image.Image:
    """
    Ensure an image is in RGB mode.
    
    Args:
        image: PIL Image object.
        
    Returns:
        PIL Image object in RGB mode.
    """
    if image.mode != 'RGB':
        if image.mode == 'RGBA':
            # Create white background and composite
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            return background
        else:
            return image.convert('RGB')
    return image


def create_text_header(text: str, width: int, font_size: int = 12, text_color: str = "black", background_color: str = "white", padding: int = 5) -> Image.Image:
    """
    Create a text header that spans the specified width.
    
    Args:
        text: Text to render.
        width: Width of the header.
        font_size: Font size in pixels.
        text_color: Color of the text.
        background_color: Background color.
        padding: Vertical padding around text.
        
    Returns:
        PIL Image object containing the text header.
    """
    if not text.strip():
        return Image.new('RGB', (width, 1), background_color)
    
    try:
        # Try to load a system font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("calibri.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Create a temporary image to measure text size
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Get text bounding box
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate header height
    header_height = int(text_height + (padding * 2))
    
    # Create background color tuple
    if background_color.lower() == "white":
        bg_color = (255, 255, 255)
    elif background_color.lower() == "black":
        bg_color = (0, 0, 0)
    else:
        # Parse hex color if provided
        try:
            if background_color.startswith('#'):
                hex_color = background_color[1:]
                bg_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                bg_color = (255, 255, 255)  # Default to white
        except Exception:
            bg_color = (255, 255, 255)
    
    # Create the header image
    header = Image.new('RGB', (width, header_height), bg_color)
    draw = ImageDraw.Draw(header)
    
    # Calculate text position (center horizontally)
    x = (width - text_width) // 2
    y = padding
    
    # Handle text color
    if text_color.lower() == "white":
        text_rgb = (255, 255, 255)
    elif text_color.lower() == "black":
        text_rgb = (0, 0, 0)
    else:
        # Parse hex color if provided
        try:
            if text_color.startswith('#'):
                hex_color = text_color[1:]
                text_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                text_rgb = (0, 0, 0)  # Default to black
        except Exception:
            text_rgb = (0, 0, 0)
    
    draw.text((x, y), text, font=font, fill=text_rgb)
    
    return header


def add_frame_to_image(image: Image.Image, frame_color: str = "#CCCCCC", frame_thickness: int = 2, frame_padding: int = 10) -> Image.Image:
    """
    Add a frame/border around an image with padding.
    
    Args:
        image: PIL Image object to add frame to.
        frame_color: Color of the frame border.
        frame_thickness: Thickness of the frame border in pixels.
        frame_padding: Internal padding between content and frame.
        
    Returns:
        PIL Image object with frame added.
    """
    # Calculate new dimensions
    total_padding = frame_padding + frame_thickness
    new_width = image.width + (2 * total_padding)
    new_height = image.height + (2 * total_padding)
    
    # Parse frame color
    if frame_color.startswith('#'):
        try:
            hex_color = frame_color[1:]
            frame_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            frame_rgb = (204, 204, 204)  # Default gray
    elif frame_color.lower() == "black":
        frame_rgb = (0, 0, 0)
    elif frame_color.lower() == "white":
        frame_rgb = (255, 255, 255)
    elif frame_color.lower() == "gray" or frame_color.lower() == "grey":
        frame_rgb = (204, 204, 204)
    else:
        frame_rgb = (204, 204, 204)  # Default gray
    
    # Create new image with frame
    framed_image = Image.new('RGB', (new_width, new_height), frame_rgb)
    
    # Create inner background (same as original or white)
    inner_width = image.width + (2 * frame_padding)
    inner_height = image.height + (2 * frame_padding)
    
    # Determine background color for inner area
    if image.mode == 'RGB':
        # Sample a corner pixel to get background color, or use white
        try:
            bg_color = image.getpixel((0, 0))
        except:
            bg_color = (255, 255, 255)
    else:
        bg_color = (255, 255, 255)
    
    # Create inner background
    inner_bg = Image.new('RGB', (inner_width, inner_height), bg_color)
    
    # Paste inner background onto frame
    framed_image.paste(inner_bg, (frame_thickness, frame_thickness))
    
    # Paste original image onto inner background
    framed_image.paste(image, (total_padding, total_padding))
    
    return framed_image


def create_placeholder_image(width: int, height: int, text: str = "No Preview") -> Image.Image:
    """
    Create a placeholder image with text.
    
    Args:
        width: Width of the placeholder image.
        height: Height of the placeholder image.
        text: Text to display on the placeholder.
        
    Returns:
        PIL Image object containing the placeholder.
    """
    placeholder = Image.new('RGB', (width, height), (128, 128, 128))  # Gray background
    draw = ImageDraw.Draw(placeholder)
    
    try:
        font_size = min(width, height) // 10
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    
    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    return placeholder