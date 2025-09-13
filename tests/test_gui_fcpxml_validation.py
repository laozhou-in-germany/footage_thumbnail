"""
Unit tests for the GUI application FCPXML validation fix.

This module tests the specific fix for input validation when using FCPXML files
without specifying source folders.
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Mock tkinter and customtkinter to avoid GUI dependencies in tests
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()
sys.modules['tkinter.colorchooser'] = Mock()
sys.modules['customtkinter'] = Mock()

# Now import the GUI application
from gui.gui_application import GUIApplication


class TestGUIFCPXMLValidation(unittest.TestCase):
    """Test cases for the FCPXML validation fix."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
        # Create a temporary FCPXML file for testing
        self.fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(self.fcpxml_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<fcpxml version="1.8"></fcpxml>')
        
        # Mock the GUI components to avoid actual GUI creation
        with patch('gui.gui_application.ctk') as mock_ctk:
            mock_ctk.CTk.return_value = Mock()
            mock_ctk.StringVar = Mock
            mock_ctk.BooleanVar = Mock
            mock_ctk.DoubleVar = Mock
            
            # Create app instance with mocked config path
            with patch('gui.gui_application.ConfigManager') as mock_config_manager:
                mock_config_manager.return_value.load_config.return_value = self._get_default_config()
                self.app = GUIApplication()
                self.app.config_manager = mock_config_manager.return_value
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.fcpxml_file):
            os.remove(self.fcpxml_file)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def _get_default_config(self):
        """Get default configuration for testing."""
        return {
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
            "max_rows_per_image": 0,
            "fcpxml_file_path": "",
            "fcpxml_use_interval_positions": True
        }
    
    def test_validate_all_inputs_valid_with_fcpxml_and_empty_folders(self):
        """Test validation passes with FCPXML file and empty source folders."""
        # Mock all validation methods to return True
        validation_methods = [
            'validate_thumbnail_width',
            'validate_clips_per_row',
            'validate_positions',
            'validate_font_size',
            'validate_frame_thickness',
            'validate_frame_padding',
            'validate_max_rows',
            'validate_padding'
        ]
        
        for method in validation_methods:
            setattr(self.app, method, Mock(return_value=True))
        
        # Mock FCPXML file and empty folders
        self.app.fcpxml_file_var = Mock()
        self.app.fcpxml_file_var.get.return_value = self.fcpxml_file
        self.app.get_current_folders = Mock(return_value=[])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertTrue(result)
        # Should not log "No source folders selected" error
        self.app.log_message.assert_not_called()
    
    def test_validate_all_inputs_invalid_with_invalid_fcpxml_extension(self):
        """Test validation fails with invalid FCPXML file extension."""
        # Mock all validation methods to return True
        validation_methods = [
            'validate_thumbnail_width',
            'validate_clips_per_row',
            'validate_positions',
            'validate_font_size',
            'validate_frame_thickness',
            'validate_frame_padding',
            'validate_max_rows',
            'validate_padding'
        ]
        
        for method in validation_methods:
            setattr(self.app, method, Mock(return_value=True))
        
        # Mock invalid FCPXML file (wrong extension) and empty folders
        invalid_fcpxml_file = os.path.join(self.temp_dir, "test.xml")
        with open(invalid_fcpxml_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<fcpxml version="1.8"></fcpxml>')
        
        self.app.fcpxml_file_var = Mock()
        self.app.fcpxml_file_var.get.return_value = invalid_fcpxml_file
        self.app.get_current_folders = Mock(return_value=[])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertFalse(result)
        self.app.log_message.assert_called_with("Error: FCPXML file must have .fcpxml extension")
        
        # Clean up
        os.remove(invalid_fcpxml_file)
    
    def test_validate_all_inputs_invalid_without_fcpxml_and_empty_folders(self):
        """Test validation fails without FCPXML file and empty source folders."""
        # Mock all validation methods to return True
        validation_methods = [
            'validate_thumbnail_width',
            'validate_clips_per_row',
            'validate_positions',
            'validate_font_size',
            'validate_frame_thickness',
            'validate_frame_padding',
            'validate_max_rows',
            'validate_padding'
        ]
        
        for method in validation_methods:
            setattr(self.app, method, Mock(return_value=True))
        
        # Mock no FCPXML file and empty folders
        self.app.fcpxml_file_var = Mock()
        self.app.fcpxml_file_var.get.return_value = ""
        self.app.get_current_folders = Mock(return_value=[])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertFalse(result)
        self.app.log_message.assert_called_with("Error: No source folders selected")
    
    def test_validate_all_inputs_valid_with_folders_and_no_fcpxml(self):
        """Test validation passes with source folders and no FCPXML file."""
        # Mock all validation methods to return True
        validation_methods = [
            'validate_thumbnail_width',
            'validate_clips_per_row',
            'validate_positions',
            'validate_font_size',
            'validate_frame_thickness',
            'validate_frame_padding',
            'validate_max_rows',
            'validate_padding'
        ]
        
        for method in validation_methods:
            setattr(self.app, method, Mock(return_value=True))
        
        # Mock no FCPXML file but with folders
        self.app.fcpxml_file_var = Mock()
        self.app.fcpxml_file_var.get.return_value = ""
        self.app.get_current_folders = Mock(return_value=["/test/folder"])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertTrue(result)
        self.app.log_message.assert_not_called()
    
    def test_validate_all_inputs_valid_with_nonexistent_fcpxml(self):
        """Test validation treats nonexistent FCPXML file as folder mode."""
        # Mock all validation methods to return True
        validation_methods = [
            'validate_thumbnail_width',
            'validate_clips_per_row',
            'validate_positions',
            'validate_font_size',
            'validate_frame_thickness',
            'validate_frame_padding',
            'validate_max_rows',
            'validate_padding'
        ]
        
        for method in validation_methods:
            setattr(self.app, method, Mock(return_value=True))
        
        # Mock nonexistent FCPXML file and empty folders
        self.app.fcpxml_file_var = Mock()
        self.app.fcpxml_file_var.get.return_value = "/nonexistent/test.fcpxml"
        self.app.get_current_folders = Mock(return_value=[])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertFalse(result)
        self.app.log_message.assert_called_with("Error: No source folders selected")


if __name__ == '__main__':
    unittest.main()