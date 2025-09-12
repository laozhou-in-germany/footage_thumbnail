"""
Integration tests for the GUI application with core modules.

This module tests the integration between the GUI and the existing core components
without requiring the actual GUI to be displayed.
"""

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.config_manager import ConfigManager
from core.video_scanner import VideoScanner
from core.image_composer import ImageComposer, CompositionSettings


class TestGUIIntegration(unittest.TestCase):
    """Test cases for GUI integration with core modules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test config
        self.test_config = {
            "source_folders": [],
            "output_path": "output/overview.jpg",
            "thumbnail_width": 320,
            "clips_per_row": 5,
            "positions": "0%,50%,99%",
            "padding": 5,
            "supported_extensions": [".mp4", ".mov", ".avi", ".mkv", ".mts"],
            "font_size": 12,
            "overlay_opacity": 0.7,
            "background_color": "white",
            "text_color": "black",
            "overlay_background_color": "black",
            "overlay_background_opacity": 0.7,
            "overlay_position": "above_thumbnails",
            "show_frame": True,
            "frame_color": "#CCCCCC",
            "frame_thickness": 2,
            "frame_padding": 10,
            "max_rows_per_image": 0
        }
        
        # Write test config
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f, indent=2)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_config_manager_integration(self):
        """Test that ConfigManager works correctly with GUI settings."""
        config_manager = ConfigManager(self.config_path)
        
        # Test loading configuration
        config = config_manager.load_config()
        self.assertEqual(config['thumbnail_width'], 320)
        self.assertEqual(config['clips_per_row'], 5)
        self.assertEqual(config['overlay_position'], 'above_thumbnails')
        self.assertEqual(config['show_frame'], True)
        self.assertEqual(config['frame_color'], '#CCCCCC')
        self.assertEqual(config['max_rows_per_image'], 0)
        
        # Test updating configuration with GUI-style updates
        gui_updates = {
            'thumbnail_width': 400,
            'overlay_position': 'on_thumbnails',
            'show_frame': False,
            'frame_color': '#FF0000',
            'max_rows_per_image': 5
        }
        
        success = config_manager.update_config(gui_updates)
        self.assertTrue(success)
        
        # Verify updates were saved
        updated_config = config_manager.load_config()
        self.assertEqual(updated_config['thumbnail_width'], 400)
        self.assertEqual(updated_config['overlay_position'], 'on_thumbnails')
        self.assertEqual(updated_config['show_frame'], False)
        self.assertEqual(updated_config['frame_color'], '#FF0000')
        self.assertEqual(updated_config['max_rows_per_image'], 5)
    
    def test_video_scanner_with_gui_config(self):
        """Test VideoScanner with configuration from GUI."""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.load_config()
        
        # Initialize scanner with config extensions
        scanner = VideoScanner(config['supported_extensions'])
        
        # Test that scanner has correct extensions
        expected_extensions = [".mp4", ".mov", ".avi", ".mkv", ".mts"]
        self.assertEqual(scanner.supported_extensions, expected_extensions)
        
        # Test scanner functionality with empty folders (should not crash)
        result = scanner.scan_folders([])
        self.assertEqual(result, [])
        
        # Test scanner with non-existent folder
        result = scanner.scan_folders(["/non/existent/folder"])
        self.assertEqual(result, [])
    
    def test_image_composer_with_gui_settings(self):
        """Test ImageComposer with settings from GUI configuration."""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.load_config()
        
        # Create composition settings from GUI config
        settings = CompositionSettings(
            clips_per_row=config['clips_per_row'],
            padding=config['padding'],
            background_color=config['background_color'],
            font_size=config['font_size'],
            text_color=config['text_color'],
            overlay_background_color=config['overlay_background_color'],
            overlay_background_opacity=config['overlay_background_opacity'],
            overlay_position=config['overlay_position'],
            show_frame=config['show_frame'],
            frame_color=config['frame_color'],
            frame_thickness=config['frame_thickness'],
            frame_padding=config['frame_padding'],
            max_rows_per_image=config['max_rows_per_image']
        )
        
        # Initialize composer with settings
        composer = ImageComposer(settings)
        
        # Test that settings are correctly applied
        self.assertEqual(composer.settings.clips_per_row, 5)
        self.assertEqual(composer.settings.overlay_position, 'above_thumbnails')
        self.assertEqual(composer.settings.show_frame, True)
        self.assertEqual(composer.settings.frame_color, '#CCCCCC')
        self.assertEqual(composer.settings.max_rows_per_image, 0)
        
        # Test creating contact sheet with empty data (should return placeholder)
        result = composer.create_contact_sheet([])
        self.assertIsNotNone(result)
        self.assertEqual(result.width, 800)  # Default placeholder size
        self.assertEqual(result.height, 600)
    
    def test_multi_page_settings_integration(self):
        """Test multi-page settings integration."""
        config_manager = ConfigManager(self.config_path)
        
        # Update config with multi-page settings
        multi_page_updates = {
            'max_rows_per_image': 3,
            'clips_per_row': 2
        }
        
        success = config_manager.update_config(multi_page_updates)
        self.assertTrue(success)
        
        # Load updated config
        config = config_manager.load_config()
        self.assertEqual(config['max_rows_per_image'], 3)
        self.assertEqual(config['clips_per_row'], 2)
        
        # Create composer settings
        settings = CompositionSettings(
            clips_per_row=config['clips_per_row'],
            max_rows_per_image=config['max_rows_per_image']
        )
        
        composer = ImageComposer(settings)
        self.assertEqual(composer.settings.max_rows_per_image, 3)
    
    def test_frame_settings_integration(self):
        """Test frame settings integration."""
        config_manager = ConfigManager(self.config_path)
        
        # Test different frame configurations
        frame_configs = [
            {
                'show_frame': True,
                'frame_color': '#FF0000',
                'frame_thickness': 5,
                'frame_padding': 20
            },
            {
                'show_frame': False,
                'frame_color': '#00FF00',
                'frame_thickness': 1,
                'frame_padding': 5
            }
        ]
        
        for frame_config in frame_configs:
            with self.subTest(frame_config=frame_config):
                # Update config
                success = config_manager.update_config(frame_config)
                self.assertTrue(success)
                
                # Load and verify
                config = config_manager.load_config()
                self.assertEqual(config['show_frame'], frame_config['show_frame'])
                self.assertEqual(config['frame_color'], frame_config['frame_color'])
                self.assertEqual(config['frame_thickness'], frame_config['frame_thickness'])
                self.assertEqual(config['frame_padding'], frame_config['frame_padding'])
                
                # Create composer settings
                settings = CompositionSettings(
                    show_frame=config['show_frame'],
                    frame_color=config['frame_color'],
                    frame_thickness=config['frame_thickness'],
                    frame_padding=config['frame_padding']
                )
                
                composer = ImageComposer(settings)
                self.assertEqual(composer.settings.show_frame, frame_config['show_frame'])
                self.assertEqual(composer.settings.frame_color, frame_config['frame_color'])
    
    def test_overlay_position_integration(self):
        """Test overlay position settings integration."""
        config_manager = ConfigManager(self.config_path)
        
        # Test both overlay positions
        overlay_positions = ['above_thumbnails', 'on_thumbnails']
        
        for position in overlay_positions:
            with self.subTest(position=position):
                # Update config
                success = config_manager.update_config({'overlay_position': position})
                self.assertTrue(success)
                
                # Load and verify
                config = config_manager.load_config()
                self.assertEqual(config['overlay_position'], position)
                
                # Create composer settings
                settings = CompositionSettings(overlay_position=config['overlay_position'])
                composer = ImageComposer(settings)
                self.assertEqual(composer.settings.overlay_position, position)
    
    def test_validation_scenarios(self):
        """Test various validation scenarios that might occur in GUI."""
        config_manager = ConfigManager(self.config_path)
        
        # Test valid updates
        valid_updates = [
            {'thumbnail_width': 100},  # Minimum valid
            {'thumbnail_width': 1000}, # Maximum valid
            {'clips_per_row': 1},      # Minimum valid
            {'clips_per_row': 10},     # Maximum valid
            {'positions': '0%'},       # Single position
            {'positions': '0%,25%,50%,75%,100%'},  # Multiple positions
            {'padding': 0},            # Minimum padding
            {'max_rows_per_image': 0}, # Unlimited rows
            {'max_rows_per_image': 10} # Limited rows
        ]
        
        for update in valid_updates:
            with self.subTest(update=update):
                success = config_manager.update_config(update)
                self.assertTrue(success, f"Valid update should succeed: {update}")
        
        # Test invalid updates (should fail validation)
        invalid_updates = [
            {'thumbnail_width': 50},   # Too small
            {'thumbnail_width': 2000}, # Too large
            {'clips_per_row': 0},      # Too small
            {'clips_per_row': 20},     # Too large
            {'padding': -1}            # Negative padding
        ]
        
        for update in invalid_updates:
            with self.subTest(update=update):
                success = config_manager.update_config(update)
                self.assertFalse(success, f"Invalid update should fail: {update}")
    
    def test_output_format_handling(self):
        """Test output format handling in integration."""
        config_manager = ConfigManager(self.config_path)
        
        # Test different output formats
        formats = [
            ('output/test.jpg', 'JPEG'),
            ('output/test.jpeg', 'JPEG'),
            ('output/test.png', 'PNG')
        ]
        
        for output_path, expected_format in formats:
            with self.subTest(output_path=output_path):
                # Update config
                success = config_manager.update_config({'output_path': output_path})
                self.assertTrue(success)
                
                # Verify update
                config = config_manager.load_config()
                self.assertEqual(config['output_path'], output_path)
                
                # Test format determination
                if output_path.lower().endswith('.png'):
                    detected_format = 'PNG'
                else:
                    detected_format = 'JPEG'
                
                self.assertEqual(detected_format, expected_format)

    def test_fcpxml_use_interval_positions_integration(self):
        """Test FCPXML use interval positions setting integration."""
        config_manager = ConfigManager(self.config_path)
        
        # Test default value for the new setting
        config = config_manager.load_config()
        self.assertIn('fcpxml_use_interval_positions', config)
        self.assertTrue(config['fcpxml_use_interval_positions'])  # Should default to True
        
        # Test updating the setting
        updates = {
            'fcpxml_use_interval_positions': False
        }
        
        success = config_manager.update_config(updates)
        self.assertTrue(success)
        
        # Verify the update was saved
        updated_config = config_manager.load_config()
        self.assertFalse(updated_config['fcpxml_use_interval_positions'])
        
        # Test FCPXML config includes the setting
        fcpxml_config = config_manager.get_timeline_config()
        self.assertIn('fcpxml_use_interval_positions', fcpxml_config)
        self.assertFalse(fcpxml_config['fcpxml_use_interval_positions'])
        
        # Test setting it back to True
        updates = {
            'fcpxml_use_interval_positions': True
        }
        
        success = config_manager.update_config(updates)
        self.assertTrue(success)
        
        # Verify it's back to True
        final_config = config_manager.load_config()
        self.assertTrue(final_config['fcpxml_use_interval_positions'])
        
        # Test that FCPXML config reflects the change
        final_fcpxml_config = config_manager.get_timeline_config()
        self.assertTrue(final_fcpxml_config['fcpxml_use_interval_positions'])

    def test_fcpxml_settings_complete_integration(self):
        """Test complete FCPXML settings integration."""
        config_manager = ConfigManager(self.config_path)
        
        # Test all FCPXML settings together
        fcpxml_updates = {
            'fcpxml_file_path': '/path/to/test.fcpxml',
            'fcpxml_show_placeholders': False,
            'fcpxml_use_interval_positions': False,  # Our new setting
            'fcpxml_placeholder_color': '#0000FF',
            'fcpxml_similarity_threshold': 0.8
        }
        
        success = config_manager.update_config(fcpxml_updates)
        self.assertTrue(success)
        
        # Verify all settings were saved
        config = config_manager.load_config()
        self.assertEqual(config['fcpxml_file_path'], '/path/to/test.fcpxml')
        self.assertFalse(config['fcpxml_show_placeholders'])
        self.assertFalse(config['fcpxml_use_interval_positions'])  # Our new setting
        self.assertEqual(config['fcpxml_placeholder_color'], '#0000FF')
        self.assertEqual(config['fcpxml_similarity_threshold'], 0.8)
        
        # Test FCPXML config method returns all settings
        fcpxml_config = config_manager.get_timeline_config()
        self.assertEqual(fcpxml_config['fcpxml_file_path'], '/path/to/test.fcpxml')
        self.assertFalse(fcpxml_config['fcpxml_show_placeholders'])
        self.assertFalse(fcpxml_config['fcpxml_use_interval_positions'])  # Our new setting
        self.assertEqual(fcpxml_config['fcpxml_placeholder_color'], '#0000FF')
        self.assertEqual(fcpxml_config['fcpxml_similarity_threshold'], 0.8)


if __name__ == "__main__":
    unittest.main()