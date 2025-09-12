"""
Unit tests for FCPXML Parser module.

This module contains comprehensive tests for the FCPXML parser functionality,
including various FCPXML formats and edge cases.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.fcpxml_parser import FCPXMLParser
from core.timeline_data_models import TimelineEntry


class TestFCPXMLParser(unittest.TestCase):
    """Test cases for FCPXML parser functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.parser = FCPXMLParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_fcpxml_file(self, content: str) -> str:
        """Create a temporary FCPXML file with given content."""
        temp_file = os.path.join(self.temp_dir, "test.fcpxml")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return temp_file
    
    def normalize_path_for_comparison(self, path):
        """Normalize path for platform-independent comparison."""
        return os.path.normpath(path).replace('\\', '/')
    
    def test_fcpxml_parsing_basic(self):
        """Test parsing of basic FCPXML format."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="video1.mp4" src="file://localhost/C:/Videos/video1.mp4" duration="5/1s"/>
        <asset id="r2" name="video2.mov" src="file:///Users/test/video2.mov" duration="10/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="15/1s">
                    <spine>
                        <asset-clip name="video1.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                        <asset-clip name="video2.mov" offset="5/1s" duration="10/1s" ref="r2"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = self.create_temp_fcpxml_file(content)
        entries = self.parser.parse_fcpxml_file(fcpxml_file)
        
        self.assertEqual(len(entries), 2)
        self.assertEqual(self.normalize_path_for_comparison(entries[0].file_path), "C:/Videos/video1.mp4")
        self.assertEqual(self.normalize_path_for_comparison(entries[1].file_path), "/Users/test/video2.mov")
        self.assertEqual(entries[0].start_time, 0.0)
        self.assertEqual(entries[0].end_time, 5.0)
        self.assertEqual(entries[1].start_time, 5.0)
        self.assertEqual(entries[1].end_time, 15.0)
    
    def test_fcpxml_parsing_with_decimal_times(self):
        """Test parsing of FCPXML with decimal time formats."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="video1.mp4" src="file://localhost/C:/Videos/video1.mp4" duration="5.5s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="5.5s">
                    <spine>
                        <asset-clip name="video1.mp4" offset="0s" duration="5.5s" ref="r1"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = self.create_temp_fcpxml_file(content)
        entries = self.parser.parse_fcpxml_file(fcpxml_file)
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(self.normalize_path_for_comparison(entries[0].file_path), "C:/Videos/video1.mp4")
        self.assertEqual(entries[0].start_time, 0.0)
        self.assertEqual(entries[0].end_time, 5.5)
        self.assertEqual(entries[0].timeline_duration, 5.5)
    
    def test_file_url_conversion(self):
        """Test file URL to path conversion."""
        # Test Windows path conversion
        windows_url = "file://localhost/C:/Videos/test.mp4"
        path = self.parser._convert_file_url_to_path(windows_url)
        self.assertEqual(path, "C:/Videos/test.mp4")
        
        # Test Unix path conversion
        unix_url = "file:///Users/test/video.mov"
        path = self.parser._convert_file_url_to_path(unix_url)
        self.assertEqual(path, "/Users/test/video.mov")
        
        # Test URL decoding
        encoded_url = "file://localhost/C:/Videos/test%20video.mp4"
        path = self.parser._convert_file_url_to_path(encoded_url)
        self.assertEqual(path, "C:/Videos/test video.mp4")
    
    def test_time_attribute_parsing(self):
        """Test time attribute parsing."""
        test_cases = [
            ("1/25s", 0.04),      # Fractional format
            ("3600/1s", 3600.0),  # Integer format
            ("5.5s", 5.5),        # Decimal format
            ("10s", 10.0),        # Simple integer format
            ("", None),           # Empty string
            ("invalid", None),    # Invalid format
        ]
        
        for time_str, expected in test_cases:
            with self.subTest(time_str=time_str):
                result = self.parser._parse_time_attribute(time_str)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertAlmostEqual(result, expected, places=3)
    
    def test_invalid_fcpxml_file(self):
        """Test handling of invalid FCPXML files."""
        # Test non-existent file
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_fcpxml_file("/nonexistent/file.fcpxml")
        
        # Test invalid XML
        invalid_content = '''<?xml version="1.0" encoding="UTF-8"?>
<invalid>
    <unclosed_tag>
</invalid>'''
        
        invalid_file = self.create_temp_fcpxml_file(invalid_content)
        with self.assertRaises(ValueError):
            self.parser.parse_fcpxml_file(invalid_file)
        
        # Test empty file
        empty_file = self.create_temp_fcpxml_file("")
        with self.assertRaises(ValueError):
            self.parser.parse_fcpxml_file(empty_file)
    
    def test_file_path_normalization(self):
        """Test file path normalization."""
        entries = [
            TimelineEntry(1, "C:\\Videos\\file1.mp4"),
            TimelineEntry(2, "/home/user/file2.mov"),
            TimelineEntry(3, "relative\\path\\file3.avi")
        ]
        
        normalized = self.parser.normalize_file_paths(entries)
        
        self.assertEqual(self.normalize_path_for_comparison(normalized[0].file_path), "C:/Videos/file1.mp4")
        self.assertEqual(self.normalize_path_for_comparison(normalized[1].file_path), "/home/user/file2.mov")
        self.assertEqual(self.normalize_path_for_comparison(normalized[2].file_path), "relative/path/file3.avi")
    
    def test_get_unique_files(self):
        """Test getting unique file paths."""
        entries = [
            TimelineEntry(1, "C:\\Videos\\file1.mp4"),
            TimelineEntry(2, "/home/user/file2.mov"),
            TimelineEntry(3, "C:\\Videos\\file1.mp4"),  # Duplicate
            TimelineEntry(4, "relative\\path\\file3.avi")
        ]
        
        unique_files = self.parser.get_unique_files(entries)
        
        self.assertEqual(len(unique_files), 3)
        self.assertIn("C:/Videos/file1.mp4", unique_files)
        self.assertIn("/home/user/file2.mov", unique_files)
        self.assertIn("relative/path/file3.avi", unique_files)
    
    def test_statistics_generation(self):
        """Test parsing statistics generation."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
    <resources>
        <format id="r0" name="FFVideoFormat1080p24" width="1920" height="1080" frameDuration="1/24s"/>
        <asset id="r1" name="video1.mp4" src="file://localhost/C:/Videos/video1.mp4" duration="5/1s"/>
        <asset id="r2" name="video2.mov" src="file:///Users/test/video2.mov" duration="10/1s"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence format="r0" duration="15/1s">
                    <spine>
                        <asset-clip name="video1.mp4" offset="0/1s" duration="5/1s" ref="r1"/>
                        <asset-clip name="video2.mov" offset="5/1s" duration="10/1s" ref="r2"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        fcpxml_file = self.create_temp_fcpxml_file(content)
        entries = self.parser.parse_fcpxml_file(fcpxml_file)
        stats = self.parser.get_statistics()
        
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["video_entries"], 2)
        self.assertEqual(stats["unique_files"], 2)
        self.assertIn("C:/Videos/video1.mp4", stats["unique_file_paths"])
        self.assertIn("/Users/test/video2.mov", stats["unique_file_paths"])


if __name__ == '__main__':
    unittest.main()