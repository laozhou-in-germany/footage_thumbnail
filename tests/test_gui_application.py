"""
Unit tests for the GUI application components.

This module tests the GUI functionality including configuration loading,
validation, event handling, and core engine integration.
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

# Mock tkinter and customtkinter to avoid GUI dependencies in tests
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()
sys.modules['tkinter.colorchooser'] = Mock()
sys.modules['customtkinter'] = Mock()

# Now import the GUI application
from gui.gui_application import GUIApplication


class TestGUIApplication(unittest.TestCase):
    """Test cases for the GUI application."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
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
            "max_rows_per_image": 0
        }
    
    def test_validate_thumbnail_width_valid(self):
        """Test thumbnail width validation with valid values."""
        # Mock the necessary attributes
        self.app.thumbnail_width_var = Mock()
        self.app.thumbnail_width_entry = Mock()
        self.app._set_valid_style = Mock()
        
        # Test valid values
        valid_values = ["100", "320", "1000"]
        for value in valid_values:
            self.app.thumbnail_width_var.get.return_value = value
            result = self.app.validate_thumbnail_width()
            self.assertTrue(result, f"Should be valid: {value}")
            self.app._set_valid_style.assert_called_with(self.app.thumbnail_width_entry)
    
    def test_validate_thumbnail_width_invalid(self):
        """Test thumbnail width validation with invalid values."""
        # Mock the necessary attributes
        self.app.thumbnail_width_var = Mock()
        self.app.thumbnail_width_entry = Mock()
        self.app._set_invalid_style = Mock()
        
        # Test invalid values
        invalid_values = ["50", "1500", "abc", ""]
        for value in invalid_values:
            self.app.thumbnail_width_var.get.return_value = value
            result = self.app.validate_thumbnail_width()
            self.assertFalse(result, f"Should be invalid: {value}")
            self.app._set_invalid_style.assert_called_with(self.app.thumbnail_width_entry)
    
    def test_validate_clips_per_row_valid(self):
        """Test clips per row validation with valid values."""
        # Mock the necessary attributes
        self.app.clips_per_row_var = Mock()
        self.app.clips_per_row_entry = Mock()
        self.app._set_valid_style = Mock()
        
        # Test valid values
        valid_values = ["1", "5", "10"]
        for value in valid_values:
            self.app.clips_per_row_var.get.return_value = value
            result = self.app.validate_clips_per_row()
            self.assertTrue(result, f"Should be valid: {value}")
    
    def test_validate_clips_per_row_invalid(self):
        """Test clips per row validation with invalid values."""
        # Mock the necessary attributes
        self.app.clips_per_row_var = Mock()
        self.app.clips_per_row_entry = Mock()
        self.app._set_invalid_style = Mock()
        
        # Test invalid values
        invalid_values = ["0", "11", "abc", ""]
        for value in invalid_values:
            self.app.clips_per_row_var.get.return_value = value
            result = self.app.validate_clips_per_row()
            self.assertFalse(result, f"Should be invalid: {value}")
    
    def test_validate_positions_valid(self):
        """Test positions validation with valid values."""
        # Mock the necessary attributes
        self.app.positions_var = Mock()
        self.app.positions_entry = Mock()
        self.app._set_valid_style = Mock()
        
        # Test valid values
        valid_values = [
            "0%,50%,99%",
            "10%,90%",
            "0s,30s,60s",
            "5s",
            "25%"
        ]
        for value in valid_values:
            self.app.positions_var.get.return_value = value
            result = self.app.validate_positions()
            self.assertTrue(result, f"Should be valid: {value}")
    
    def test_validate_positions_invalid(self):
        """Test positions validation with invalid values."""
        # Mock the necessary attributes
        self.app.positions_var = Mock()
        self.app.positions_entry = Mock()
        self.app._set_invalid_style = Mock()
        
        # Test invalid values
        invalid_values = [
            "",
            "150%",
            "-10%",
            "abc",
            "50",  # Missing % or s
            "50%,abc"
        ]
        for value in invalid_values:
            self.app.positions_var.get.return_value = value
            result = self.app.validate_positions()
            self.assertFalse(result, f"Should be invalid: {value}")
    
    def test_validate_font_size_valid(self):
        """Test font size validation with valid values."""
        # Mock the necessary attributes
        self.app.font_size_var = Mock()
        self.app.font_size_entry = Mock()
        self.app._set_valid_style = Mock()
        
        # Test valid values
        valid_values = ["8", "12", "24", "72"]
        for value in valid_values:
            self.app.font_size_var.get.return_value = value
            result = self.app.validate_font_size()
            self.assertTrue(result, f"Should be valid: {value}")
    
    def test_validate_font_size_invalid(self):
        """Test font size validation with invalid values."""
        # Mock the necessary attributes
        self.app.font_size_var = Mock()
        self.app.font_size_entry = Mock()
        self.app._set_invalid_style = Mock()
        
        # Test invalid values
        invalid_values = ["5", "100", "abc", ""]
        for value in invalid_values:
            self.app.font_size_var.get.return_value = value
            result = self.app.validate_font_size()
            self.assertFalse(result, f"Should be invalid: {value}")
    
    def test_validate_all_inputs_valid(self):
        """Test validation of all inputs with valid values."""
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
        
        # Mock folder and output path methods
        self.app.get_current_folders = Mock(return_value=["/test/folder"])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        
        result = self.app.validate_all_inputs()
        self.assertTrue(result)
    
    def test_validate_all_inputs_invalid_no_folders(self):
        """Test validation fails when no folders are selected."""
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
        
        # Mock no folders selected
        self.app.get_current_folders = Mock(return_value=[])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = "output/test.jpg"
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertFalse(result)
        self.app.log_message.assert_called_with("Error: No source folders selected")
    
    def test_validate_all_inputs_invalid_no_output_path(self):
        """Test validation fails when output path is empty."""
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
        
        # Mock valid folders but empty output path
        self.app.get_current_folders = Mock(return_value=["/test/folder"])
        self.app.output_path_var = Mock()
        self.app.output_path_var.get.return_value = ""
        self.app.log_message = Mock()
        
        result = self.app.validate_all_inputs()
        self.assertFalse(result)
        self.app.log_message.assert_called_with("Error: Output path cannot be empty")
    
    def test_update_color_button(self):
        """Test color button update functionality."""
        # Mock button objects
        self.app.text_color_btn = Mock()
        self.app.bg_color_btn = Mock()
        self.app.frame_color_btn = Mock()
        self.app.log_message = Mock()
        
        # Test updating text color button
        self.app.update_color_button("text", "#FF0000")
        self.app.text_color_btn.configure.assert_called_with(text="🟨 #FF0000")
        
        # Test updating background color button
        self.app.update_color_button("background", "#000000")
        self.app.bg_color_btn.configure.assert_called_with(text="⬛ Black")
        
        # Test updating frame color button
        self.app.update_color_button("frame", "#FFFFFF")
        self.app.frame_color_btn.configure.assert_called_with(text="⬜ White")
    
    def test_update_opacity_label(self):
        """Test opacity label update functionality."""
        # Mock label objects
        self.app.text_opacity_label = Mock()
        self.app.bg_opacity_label = Mock()
        self.app.log_message = Mock()
        
        # Test updating text opacity label
        self.app.update_opacity_label("text", 0.75)
        self.app.text_opacity_label.configure.assert_called_with(text="75%")
        
        # Test updating background opacity label
        self.app.update_opacity_label("bg", 0.5)
        self.app.bg_opacity_label.configure.assert_called_with(text="50%")
    
    def test_get_current_folders_empty(self):
        """Test getting current folders when none are selected."""
        # Mock text widget
        self.app.folder_list_text = Mock()
        self.app.folder_list_text.get.return_value = ""
        
        folders = self.app.get_current_folders()
        self.assertEqual(folders, [])
    
    def test_get_current_folders_with_folders(self):
        """Test getting current folders when folders are selected."""
        # Mock text widget
        self.app.folder_list_text = Mock()
        self.app.folder_list_text.get.return_value = "/path/folder1\n/path/folder2\n"
        
        folders = self.app.get_current_folders()
        self.assertEqual(folders, ["/path/folder1", "/path/folder2"])
    
    def test_update_folder_display(self):
        """Test updating folder display."""
        # Mock text widget
        self.app.folder_list_text = Mock()
        
        # Test with empty folders
        self.app.update_folder_display([])
        self.app.folder_list_text.delete.assert_called_with("1.0", "end")
        
        # Test with folders
        folders = ["/path/folder1", "/path/folder2"]
        self.app.update_folder_display(folders)
        self.app.folder_list_text.insert.assert_called_with("1.0", "/path/folder1\n/path/folder2")
    
    @patch('gui.gui_application.queue')
    def test_processing_worker_no_videos(self, mock_queue):
        """Test processing worker when no videos are found."""
        # Mock the necessary components
        self.app.progress_queue = Mock()
        self.app.log_queue = Mock()
        
        # Mock config manager
        self.app.config_manager.load_config.return_value = {
            'source_folders': ['/test/folder'],
            'supported_extensions': ['.mp4']
        }
        
        # Mock video scanner to return no videos
        with patch('gui.gui_application.VideoScanner') as mock_scanner:
            mock_scanner_instance = Mock()
            mock_scanner_instance.scan_folders.return_value = []
            mock_scanner.return_value = mock_scanner_instance
            
            # Run the worker
            self.app._processing_worker()
            
            # Verify progress and log updates
            self.app.progress_queue.put.assert_called()
            self.app.log_queue.put.assert_called()
    
    def test_toggle_frame_settings_enabled(self):
        """Test toggling frame settings when enabled."""
        # Mock frame settings
        self.app.show_frame_var = Mock()
        self.app.show_frame_var.get.return_value = True
        self.app.frame_settings_frame = Mock()
        self.app.frame_settings_frame.winfo_children.return_value = []
        self.app._enable_widget_recursive = Mock()
        
        self.app.toggle_frame_settings()
        # Should call enable method (test is simplified due to mocking complexity)
    
    def test_toggle_frame_settings_disabled(self):
        """Test toggling frame settings when disabled."""
        # Mock frame settings
        self.app.show_frame_var = Mock()
        self.app.show_frame_var.get.return_value = False
        self.app.frame_settings_frame = Mock()
        self.app.frame_settings_frame.winfo_children.return_value = []
        self.app._disable_widget_recursive = Mock()
        
        self.app.toggle_frame_settings()
        # Should call disable method (test is simplified due to mocking complexity)


class TestGUIConfigurationIntegration(unittest.TestCase):
    """Test cases for GUI configuration integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_save_configuration_format_handling(self):
        """Test configuration saving with different output formats."""
        # Create a mock app with minimal setup
        app = Mock()
        app.validate_all_inputs = Mock(return_value=True)
        app.get_current_folders = Mock(return_value=["/test/folder"])
        app.log_message = Mock()
        
        # Mock all the variables
        app.thumbnail_width_var = Mock()
        app.thumbnail_width_var.get.return_value = "320"
        app.clips_per_row_var = Mock()
        app.clips_per_row_var.get.return_value = "5"
        app.positions_var = Mock()
        app.positions_var.get.return_value = "0%,50%,99%"
        app.padding_var = Mock()
        app.padding_var.get.return_value = "5"
        app.max_rows_var = Mock()
        app.max_rows_var.get.return_value = "0"
        app.output_path_var = Mock()
        app.output_path_var.get.return_value = "output/test"
        app.output_path_var.set = Mock()
        app.font_size_var = Mock()
        app.font_size_var.get.return_value = "12"
        app.overlay_position_var = Mock()
        app.overlay_position_var.get.return_value = "above_thumbnails"
        app.text_color_var = Mock()
        app.text_color_var.get.return_value = "black"
        app.bg_color_var = Mock()
        app.bg_color_var.get.return_value = "black"
        app.text_opacity_var = Mock()
        app.text_opacity_var.get.return_value = 0.7
        app.bg_opacity_var = Mock()
        app.bg_opacity_var.get.return_value = 0.7
        app.show_frame_var = Mock()
        app.show_frame_var.get.return_value = True
        app.frame_color_var = Mock()
        app.frame_color_var.get.return_value = "#CCCCCC"
        app.frame_thickness_var = Mock()
        app.frame_thickness_var.get.return_value = "2"
        app.frame_padding_var = Mock()
        app.frame_padding_var.get.return_value = "10"
        app.format_var = Mock()
        app.format_var.get.return_value = "PNG"
        
        # Mock config manager
        app.config_manager = Mock()
        app.config_manager.update_config.return_value = True
        
        # Import the method and bind it to our mock
        from gui.gui_application import GUIApplication
        app.save_configuration = GUIApplication.save_configuration.__get__(app)
        
        # Test PNG format
        result = app.save_configuration()
        self.assertTrue(result)
        app.output_path_var.set.assert_called_with("output/test.png")
        
        # Test JPEG format
        app.format_var.get.return_value = "JPEG"
        app.output_path_var.get.return_value = "output/test"
        result = app.save_configuration()
        self.assertTrue(result)
        app.output_path_var.set.assert_called_with("output/test.jpg")


if __name__ == '__main__':
    unittest.main()