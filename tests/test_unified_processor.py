"""
Unit tests for Unified Processor module.

This module contains comprehensive tests for the unified processing workflow
that handles both FCPXML and folder-based thumbnail generation.
"""

import unittest
import tempfile
import os
import json
import sys
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.unified_processor import UnifiedProcessor
from core.config_manager import ConfigManager


class TestUnifiedProcessor(unittest.TestCase):
    """Test cases for unified processor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test configuration
        test_config = {
            "source_folders": [self.temp_dir],
            "output_path": os.path.join(self.temp_dir, "output.jpg"),
            "thumbnail_width": 320,
            "clips_per_row": 4,
            "positions": "0%,50%,99%",
            "padding": 5,
            "supported_extensions": [".mp4", ".mov", ".avi"],
            "fcpxml_file_path": "",
            "fcpxml_show_placeholders": True,
            "fcpxml_use_interval_positions": True
        }
        
        self.config_manager = ConfigManager(self.config_path)
        self.config_manager.save_config(test_config)
        
        self.processor = UnifiedProcessor(self.config_manager)
        
        # Set up mock callbacks
        self.progress_calls = []
        self.log_calls = []
        
        def mock_progress(progress, message):
            self.progress_calls.append((progress, message))
        
        def mock_log(message):
            self.log_calls.append(message)
        
        self.processor.set_progress_callback(mock_progress)
        self.processor.set_log_callback(mock_log)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_processing_mode_detection_folder(self):
        """Test detection of folder processing mode."""
        mode = self.processor.get_processing_mode()
        self.assertEqual(mode, "folder")
    
    def test_processing_mode_detection_fcpxml(self):
        """Test detection of FCPXML processing mode."""
        # Create a test FCPXML file
        fcpxml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="test.mp4" src="file://localhost/C:/Videos/test.mp4" duration="5/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="5/1s">
                    <spine>
                        <asset-clip name="test.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        
        # Update config to use FCPXML file
        self.config_manager.set_fcpxml_file(fcpxml_file)
        
        mode = self.processor.get_processing_mode()
        self.assertEqual(mode, "fcpxml")
    
    def test_configuration_validation_valid(self):
        """Test configuration validation with valid settings."""
        is_valid, errors = self.processor.validate_configuration()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_configuration_validation_invalid(self):
        """Test configuration validation with invalid settings."""
        # Clear source folders
        self.config_manager.update_config({"source_folders": []})
        
        is_valid, errors = self.processor.validate_configuration()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("No source folders specified", errors[0])
    
    def test_configuration_validation_fcpxml_mode(self):
        """Test configuration validation in FCPXML mode."""
        # Create a valid test FCPXML file
        fcpxml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="test.mp4" src="file://localhost/C:/Videos/test.mp4" duration="5/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="5/1s">
                    <spine>
                        <asset-clip name="test.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        
        # Update config to use valid FCPXML file
        self.config_manager.set_fcpxml_file(fcpxml_file)
        
        is_valid, errors = self.processor.validate_configuration()
        # This should pass since we have a valid FCPXML file
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    @patch('core.unified_processor.VideoScanner')
    @patch('core.unified_processor.ThumbnailExtractor')
    @patch('core.unified_processor.ImageComposer')
    def test_folder_mode_processing(self, mock_composer, mock_extractor, mock_scanner):
        """Test folder mode processing workflow."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance
        
        # Mock video files
        mock_video_file = Mock()
        mock_video_file.filename = "test.mp4"
        mock_scanner_instance.scan_folders.return_value = [mock_video_file]
        mock_scanner_instance.filter_accessible_files.return_value = [mock_video_file]
        
        # Mock thumbnail extractor
        mock_extractor_instance = Mock()
        mock_extractor.return_value = mock_extractor_instance
        
        mock_video_data = Mock()
        mock_video_data.processing_status = "success"
        mock_video_data.thumbnails = [Mock(), Mock()]
        mock_extractor_instance.process_video_file.return_value = mock_video_data
        
        # Mock image composer
        mock_composer_instance = Mock()
        mock_composer.return_value = mock_composer_instance
        mock_composer_instance.create_contact_sheet.return_value = Mock()
        mock_composer_instance.get_additional_pages.return_value = []
        
        # Mock save method
        mock_image = Mock()
        mock_composer_instance.create_contact_sheet.return_value = mock_image
        
        # Execute processing
        result = self.processor.process_thumbnails()
        
        # Verify workflow
        self.assertTrue(result)
        mock_scanner_instance.scan_folders.assert_called_once()
        mock_extractor_instance.process_video_file.assert_called_once()
        mock_composer_instance.create_contact_sheet.assert_called_once()
    
    @patch('core.unified_processor.FCPXMLParser')
    @patch('core.unified_processor.ImageComposer')
    def test_fcpxml_mode_processing(self, mock_composer, mock_fcpxml_parser):
        """Test FCPXML mode processing workflow."""
        # Create test FCPXML file
        fcpxml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="test.mp4" src="file://localhost/C:/Videos/test.mp4" duration="5/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="5/1s">
                    <spine>
                        <asset-clip name="test.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        self.config_manager.set_fcpxml_file(fcpxml_file)
        
        # Setup mocks
        mock_parser_instance = Mock()
        mock_fcpxml_parser.return_value = mock_parser_instance
        mock_fcpxml_entry = Mock()
        mock_parser_instance.parse_fcpxml_file.return_value = [mock_fcpxml_entry]
        
        # Mock the validate_fcpxml_files method to return a match
        mock_match = {
            'timeline_entry': mock_fcpxml_entry,
            'matched_file_path': 'C:/Videos/test.mp4',
            'is_found': True,
            'similarity_score': 1.0
        }
        
        # Mock the _extract_fcpxml_thumbnails method to return video data
        mock_video_data = Mock()
        mock_video_data.is_placeholder = False
        mock_video_data.processing_status = "success"
        mock_video_data.thumbnails = [Mock(), Mock(), Mock()]
        
        # Mock the image composer to avoid actual image processing
        mock_composer_instance = Mock()
        mock_composer.return_value = mock_composer_instance
        mock_composer_instance.create_contact_sheet.return_value = Mock()
        mock_composer_instance.get_additional_pages.return_value = []
        
        # Patch the methods in the processor instance
        with patch.object(self.processor, '_validate_fcpxml_files', return_value=[mock_match]), \
             patch.object(self.processor, '_extract_fcpxml_thumbnails', return_value=[mock_video_data]):
            
            # Execute processing
            result = self.processor.process_thumbnails()
            
            # Verify FCPXML workflow
            self.assertTrue(result)
            mock_parser_instance.parse_fcpxml_file.assert_called_once_with(fcpxml_file)
            mock_composer_instance.create_contact_sheet.assert_called_once()
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        # Callbacks should capture progress updates
        self.processor._report_progress(0.5, "Test progress")
        
        self.assertEqual(len(self.progress_calls), 1)
        self.assertEqual(self.progress_calls[0], (0.5, "Test progress"))
    
    def test_log_callback(self):
        """Test progress callback functionality."""
        # Callbacks should capture progress updates
        self.processor._report_progress(0.5, "Test progress")
        
        self.assertEqual(len(self.progress_calls), 1)
        self.assertEqual(self.progress_calls[0], (0.5, "Test progress"))
    
    def test_mode_switching(self):
        """Test switching between folder and FCPXML modes."""
        # Start in folder mode
        self.assertEqual(self.processor.get_processing_mode(), "folder")
        
        # Switch to FCPXML mode
        fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(fcpxml_file, 'w') as f:
            f.write("test.mp4\n")
        self.config_manager.set_fcpxml_file(fcpxml_file)
        
        self.assertEqual(self.processor.get_processing_mode(), "fcpxml")
        
        # Switch back to folder mode
        self.config_manager.clear_fcpxml_file()
        self.assertEqual(self.processor.get_processing_mode(), "folder")
    
    def test_is_fcpxml_mode(self):
        """Test FCPXML mode detection with FCPXML file.""" 
        # Create temporary FCPXML file
        fcpxml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="test.mp4" src="file://localhost/C:/Videos/test.mp4" duration="5/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="5/1s">
                    <spine>
                        <asset-clip name="test.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        
        # Update config with FCPXML file
        self.config_manager.set_fcpxml_file(fcpxml_file)
        
        # Test mode detection
        processor = UnifiedProcessor(self.config_manager)
        mode = processor.get_processing_mode()
        
        self.assertEqual(mode, "fcpxml")
    
    def test_process_fcpxml_mode(self):
        """Test FCPXML mode processing."""
        # Create temporary FCPXML file with non-existent video files
        fcpxml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="nonexistent1.mp4" src="file://localhost/C:/Videos/nonexistent1.mp4" duration="5/1s"/>
        <asset id="r2" name="nonexistent2.mov" src="file:///Users/test/nonexistent2.mov" duration="10/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="15/1s">
                    <spine>
                        <asset-clip name="nonexistent1.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                        <asset-clip name="nonexistent2.mov" offset="5/1s" duration="10/1s" ref="r2"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        
        # Update config
        config_updates = {
            'fcpxml_file_path': fcpxml_file,
            'source_folders': [self.temp_dir],
            'output_path': os.path.join(self.temp_dir, 'output.jpg')
        }
        self.config_manager.update_config(config_updates)
        
        # Mock the image composer to avoid actual image processing
        with patch('core.unified_processor.ImageComposer') as mock_composer:
            mock_composer_instance = Mock()
            mock_composer_instance.create_contact_sheet.return_value = Mock()
            mock_composer_instance.get_additional_pages.return_value = []
            mock_composer.return_value = mock_composer_instance
            
            # Test processing
            processor = UnifiedProcessor(self.config_manager)
            result = processor.process_thumbnails()
            
            # Should succeed even with missing files (will generate placeholders)
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()