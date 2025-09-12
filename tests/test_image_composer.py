"""
Unit tests for the Image Composer component.
"""

import unittest
from PIL import Image
from pathlib import Path

# Add src to path for imports
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.image_composer import ImageComposer, CompositionSettings
from core.thumbnail_extractor import VideoData, ThumbnailData, VideoMetadata
from core.video_scanner import VideoFile
from datetime import datetime


class TestImageComposer(unittest.TestCase):
    """Test cases for the ImageComposer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.composer = ImageComposer()
        
        # Create test thumbnail images
        self.test_thumbnails = []
        for i in range(3):
            img = Image.new('RGB', (320, 180), color=(100 + i*50, 150, 200))
            timestamp = f"00:{i*30:02d}"
            thumbnail_data = ThumbnailData(
                image=img,
                position=i * 30.0,
                timestamp=timestamp,
                frame_number=i * 900
            )
            self.test_thumbnails.append(thumbnail_data)
        
        # Create test video metadata
        self.test_metadata = VideoMetadata(
            duration=120.0,
            creation_date=datetime(2023, 1, 15, 14, 30, 0),
            resolution=(1920, 1080),
            fps=30.0,
            codec="h264",
            format="mp4"
        )
        
        # Create test video file
        self.test_video_file = VideoFile(
            path="C:/Videos/test_video.mp4",
            filename="test_video.mp4",
            size=50000000,
            modified_date=datetime(2023, 1, 15, 14, 30, 0),
            is_accessible=True
        )
        
        # Create test video data
        self.test_video_data = VideoData(
            file=self.test_video_file,
            metadata=self.test_metadata,
            thumbnails=self.test_thumbnails,
            processing_status="success"
        )
    
    def test_composition_settings_default(self):
        """Test default composition settings."""
        settings = CompositionSettings()
        
        self.assertEqual(settings.clips_per_row, 5)
        self.assertEqual(settings.padding, 5)
        self.assertEqual(settings.background_color, "white")
        self.assertEqual(settings.font_size, 12)
        self.assertTrue(settings.show_filename)
        self.assertTrue(settings.show_creation_date)
        self.assertTrue(settings.show_duration)
    
    def test_horizontal_strip_creation(self):
        """Test horizontal strip creation from thumbnails."""
        # Create test images
        thumbnails = [thumbnail.image for thumbnail in self.test_thumbnails]
        
        strip = self.composer._create_horizontal_strip(thumbnails)
        
        # Check that strip was created
        self.assertIsInstance(strip, Image.Image)
        self.assertEqual(strip.mode, 'RGB')
        
        # Check dimensions
        expected_width = (3 * 320) + (2 * 5)  # 3 thumbnails + 2 padding
        self.assertEqual(strip.size, (expected_width, 180))
    
    def test_video_strip_creation(self):
        """Test video strip creation with overlays."""
        strip = self.composer._create_video_strip(self.test_video_data)
        
        self.assertIsInstance(strip, Image.Image)
        self.assertEqual(strip.mode, 'RGB')
        
        # Should have combined all thumbnails horizontally
        expected_width = (3 * 320) + (2 * 5)  # 3 thumbnails + 2 padding
        self.assertEqual(strip.size[0], expected_width)
    
    def test_contact_sheet_creation(self):
        """Test complete contact sheet creation."""
        # Create multiple video data objects
        video_data_list = [self.test_video_data]
        
        contact_sheet = self.composer.create_contact_sheet(video_data_list)
        
        self.assertIsInstance(contact_sheet, Image.Image)
        self.assertEqual(contact_sheet.mode, 'RGB')
        self.assertGreater(contact_sheet.size[0], 0)
        self.assertGreater(contact_sheet.size[1], 0)
    
    def test_empty_video_list(self):
        """Test handling of empty video list."""
        contact_sheet = self.composer.create_contact_sheet([])
        
        self.assertIsInstance(contact_sheet, Image.Image)
        # Should create a placeholder image
        self.assertEqual(contact_sheet.size, (800, 600))
    
    def test_failed_video_filtering(self):
        """Test filtering of failed video processing."""
        # Create a failed video data
        failed_video_data = VideoData(
            file=self.test_video_file,
            metadata=self.test_metadata,
            thumbnails=[],
            processing_status="error",
            error_message="Failed to process"
        )
        
        video_data_list = [self.test_video_data, failed_video_data]
        contact_sheet = self.composer.create_contact_sheet(video_data_list)
        
        # Should still create a contact sheet with only successful videos
        self.assertIsInstance(contact_sheet, Image.Image)
    
    def test_grid_dimensions_calculation(self):
        """Test grid dimensions calculation."""
        # Test various video counts
        self.assertEqual(self.composer.calculate_grid_dimensions(0, 5), (0, 0))
        self.assertEqual(self.composer.calculate_grid_dimensions(1, 5), (1, 1))
        self.assertEqual(self.composer.calculate_grid_dimensions(5, 5), (5, 1))
        self.assertEqual(self.composer.calculate_grid_dimensions(6, 5), (5, 2))
        self.assertEqual(self.composer.calculate_grid_dimensions(12, 5), (5, 3))
    
    def test_output_size_estimation(self):
        """Test output size estimation."""
        estimated_size = self.composer.estimate_output_size(
            video_count=2,
            thumbnail_width=320,
            positions_count=3
        )
        
        self.assertIsInstance(estimated_size, tuple)
        self.assertEqual(len(estimated_size), 2)
        self.assertGreater(estimated_size[0], 0)
        self.assertGreater(estimated_size[1], 0)
    
    def test_settings_update(self):
        """Test composition settings update."""
        self.composer.update_settings(
            clips_per_row=3,
            padding=10,
            background_color="black"
        )
        
        self.assertEqual(self.composer.settings.clips_per_row, 3)
        self.assertEqual(self.composer.settings.padding, 10)
        self.assertEqual(self.composer.settings.background_color, "black")
    
    def test_custom_settings(self):
        """Test custom composition settings."""
        custom_settings = CompositionSettings(
            clips_per_row=3,
            padding=10,
            background_color="black",
            font_size=16,
            show_filename=False
        )
        
        custom_composer = ImageComposer(custom_settings)
        
        self.assertEqual(custom_composer.settings.clips_per_row, 3)
        self.assertEqual(custom_composer.settings.padding, 10)
        self.assertEqual(custom_composer.settings.background_color, "black")
        self.assertEqual(custom_composer.settings.font_size, 16)
        self.assertFalse(custom_composer.settings.show_filename)
    
    def test_watermark_addition(self):
        """Test watermark addition to images."""
        test_image = Image.new('RGB', (400, 300), color=(255, 255, 255))
        watermarked = self.composer.add_watermark(test_image, "Test Watermark")
        
        self.assertIsInstance(watermarked, Image.Image)
        self.assertEqual(watermarked.size, test_image.size)
        
        # Test empty watermark
        no_watermark = self.composer.add_watermark(test_image, "")
        self.assertEqual(no_watermark.size, test_image.size)
    
    def test_summary_overlay_creation(self):
        """Test summary overlay creation."""
        video_data_list = [self.test_video_data]
        summary_overlay = self.composer.create_summary_overlay(video_data_list)
        
        self.assertIsInstance(summary_overlay, Image.Image)
        self.assertEqual(summary_overlay.mode, 'RGBA')
        self.assertGreater(summary_overlay.size[0], 0)
        self.assertGreater(summary_overlay.size[1], 0)


if __name__ == "__main__":
    unittest.main()