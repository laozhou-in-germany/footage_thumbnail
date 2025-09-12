"""
Unit tests for the Config Manager component.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path

# Add src to path for imports
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = os.path.join(self.temp_dir, "test_config.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_config_path):
            os.remove(self.temp_config_path)
        os.rmdir(self.temp_dir)
    
    def test_default_config_creation(self):
        """Test that default configuration is created correctly."""
        config_manager = ConfigManager(self.temp_config_path)
        config = config_manager.load_config()
        
        # Check that all required fields exist
        required_fields = [
            "source_folders", "output_path", "thumbnail_width",
            "clips_per_row", "positions", "padding", "supported_extensions"
        ]
        
        for field in required_fields:
            self.assertIn(field, config)
        
        # Check default values
        self.assertEqual(config["thumbnail_width"], 320)
        self.assertEqual(config["clips_per_row"], 5)
        self.assertEqual(config["positions"], "0%,50%,99%")
        self.assertEqual(config["padding"], 5)
        self.assertIsInstance(config["source_folders"], list)
        self.assertIsInstance(config["supported_extensions"], list)
    
    def test_config_validation(self):
        """Test configuration validation."""
        config_manager = ConfigManager(self.temp_config_path)
        
        # Test valid configuration
        valid_config = {
            "source_folders": ["C:/Videos"],
            "output_path": "output.jpg",
            "thumbnail_width": 320,
            "clips_per_row": 5,
            "positions": "0%,50%,99%",
            "padding": 5,
            "supported_extensions": [".mp4", ".mov"]
        }
        self.assertTrue(config_manager._validate_config(valid_config))
        
        # Test invalid thumbnail width
        invalid_config = valid_config.copy()
        invalid_config["thumbnail_width"] = 50  # Too small
        self.assertFalse(config_manager._validate_config(invalid_config))
        
        # Test invalid clips per row
        invalid_config = valid_config.copy()
        invalid_config["clips_per_row"] = 15  # Too large
        self.assertFalse(config_manager._validate_config(invalid_config))
        
        # Test invalid positions
        invalid_config = valid_config.copy()
        invalid_config["positions"] = "invalid"
        self.assertFalse(config_manager._validate_config(invalid_config))
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        config_manager = ConfigManager(self.temp_config_path)
        
        # Update configuration
        test_config = {
            "source_folders": ["C:/TestVideos"],
            "output_path": "test_output.jpg",
            "thumbnail_width": 400,
            "clips_per_row": 3,
            "positions": "0%,25%,50%,75%,99%",
            "padding": 10,
            "supported_extensions": [".mp4", ".avi"],
            "font_size": 14,
            "overlay_opacity": 0.8
        }
        
        # Save configuration
        self.assertTrue(config_manager.save_config(test_config))
        
        # Create new config manager to test loading
        new_config_manager = ConfigManager(self.temp_config_path)
        loaded_config = new_config_manager.load_config()
        
        # Check that values were saved and loaded correctly
        self.assertEqual(loaded_config["source_folders"], ["C:/TestVideos"])
        self.assertEqual(loaded_config["thumbnail_width"], 400)
        self.assertEqual(loaded_config["clips_per_row"], 3)
    
    def test_source_folder_management(self):
        """Test source folder add/remove operations."""
        config_manager = ConfigManager(self.temp_config_path)
        
        # Add source folders
        self.assertTrue(config_manager.add_source_folder("C:/Videos1"))
        self.assertTrue(config_manager.add_source_folder("C:/Videos2"))
        
        folders = config_manager.get_source_folders()
        self.assertIn("C:/Videos1", folders)
        self.assertIn("C:/Videos2", folders)
        
        # Remove source folder
        self.assertTrue(config_manager.remove_source_folder("C:/Videos1"))
        folders = config_manager.get_source_folders()
        self.assertNotIn("C:/Videos1", folders)
        self.assertIn("C:/Videos2", folders)
        
        # Clear all folders
        self.assertTrue(config_manager.clear_source_folders())
        folders = config_manager.get_source_folders()
        self.assertEqual(len(folders), 0)
    
    def test_config_update(self):
        """Test configuration updates."""
        config_manager = ConfigManager(self.temp_config_path)
        
        # Update specific values
        updates = {
            "thumbnail_width": 500,
            "clips_per_row": 4
        }
        
        self.assertTrue(config_manager.update_config(updates))
        
        config = config_manager.load_config()
        self.assertEqual(config["thumbnail_width"], 500)
        self.assertEqual(config["clips_per_row"], 4)
        
        # Test invalid update
        invalid_updates = {
            "thumbnail_width": 50  # Invalid value
        }
        self.assertFalse(config_manager.update_config(invalid_updates))
    
    def test_fcpxml_use_interval_positions_config(self):
        """Test the new fcpxml_use_interval_positions configuration parameter."""
        config_manager = ConfigManager(self.temp_config_path)
        
        # Test default value
        config = config_manager.load_config()
        self.assertIn('fcpxml_use_interval_positions', config)
        self.assertTrue(config['fcpxml_use_interval_positions'])
        
        # Test getting FCPXML config includes the new parameter
        fcpxml_config = config_manager.get_timeline_config()
        self.assertIn('fcpxml_use_interval_positions', fcpxml_config)
        
        # Test updating the parameter
        updates = {
            'fcpxml_use_interval_positions': False
        }
        self.assertTrue(config_manager.update_config(updates))
        
        # Verify the update was saved
        updated_config = config_manager.load_config()
        self.assertFalse(updated_config['fcpxml_use_interval_positions'])
        
        # Test FCPXML config reflects the change
        updated_fcpxml_config = config_manager.get_timeline_config()
        self.assertFalse(updated_fcpxml_config['fcpxml_use_interval_positions'])
        
        # Test validation of the parameter
        valid_config = {
            "source_folders": ["C:/Videos"],
            "output_path": "output.jpg",
            "thumbnail_width": 320,
            "clips_per_row": 5,
            "positions": "0%,50%,99%",
            "padding": 5,
            "supported_extensions": [".mp4", ".mov"],
            "fcpxml_use_interval_positions": True
        }
        self.assertTrue(config_manager._validate_config(valid_config))
        
        # Test invalid value (non-boolean)
        invalid_config = valid_config.copy()
        invalid_config["fcpxml_use_interval_positions"] = "invalid"
        self.assertFalse(config_manager._validate_config(invalid_config))


if __name__ == "__main__":
    unittest.main()