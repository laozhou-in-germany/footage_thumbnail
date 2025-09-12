"""
Unit tests for the Video Scanner component.
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add src to path for imports
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.video_scanner import VideoScanner, VideoFile


class TestVideoScanner(unittest.TestCase):
    """Test cases for the VideoScanner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.video_scanner = VideoScanner()
        
        # Create test directory structure
        self.test_videos_dir = os.path.join(self.temp_dir, "test_videos")
        self.test_subdir = os.path.join(self.test_videos_dir, "subdir")
        os.makedirs(self.test_subdir)
        
        # Create test files (empty files for testing)
        self.test_files = [
            os.path.join(self.test_videos_dir, "video1.mp4"),
            os.path.join(self.test_videos_dir, "video2.mov"),
            os.path.join(self.test_videos_dir, "video3.avi"),
            os.path.join(self.test_videos_dir, "document.txt"),  # Not a video
            os.path.join(self.test_subdir, "video4.mkv"),
            os.path.join(self.test_subdir, "video5.mts"),
        ]
        
        for file_path in self.test_files:
            with open(file_path, "w") as f:
                f.write("test content")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test files and directories
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if os.path.exists(self.test_subdir):
            os.rmdir(self.test_subdir)
        if os.path.exists(self.test_videos_dir):
            os.rmdir(self.test_videos_dir)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_supported_extension_detection(self):
        """Test supported video file extension detection."""
        # Test default supported extensions
        self.assertTrue(self.video_scanner.is_supported_video("test.mp4"))
        self.assertTrue(self.video_scanner.is_supported_video("test.mov"))
        self.assertTrue(self.video_scanner.is_supported_video("test.avi"))
        self.assertTrue(self.video_scanner.is_supported_video("test.mkv"))
        self.assertTrue(self.video_scanner.is_supported_video("test.mts"))
        
        # Test unsupported extensions
        self.assertFalse(self.video_scanner.is_supported_video("test.txt"))
        self.assertFalse(self.video_scanner.is_supported_video("test.jpg"))
        self.assertFalse(self.video_scanner.is_supported_video("test.pdf"))
        
        # Test case insensitivity
        self.assertTrue(self.video_scanner.is_supported_video("test.MP4"))
        self.assertTrue(self.video_scanner.is_supported_video("test.MOV"))
    
    def test_folder_scanning_recursive(self):
        """Test recursive folder scanning."""
        video_files = self.video_scanner.scan_folders([self.test_videos_dir], recursive=True)
        
        # Should find 5 video files (excluding document.txt)
        video_filenames = [vf.filename for vf in video_files]
        expected_videos = ["video1.mp4", "video2.mov", "video3.avi", "video4.mkv", "video5.mts"]
        
        self.assertEqual(len(video_files), 5)
        for expected in expected_videos:
            self.assertIn(expected, video_filenames)
        
        # Should not include non-video files
        self.assertNotIn("document.txt", video_filenames)
    
    def test_folder_scanning_non_recursive(self):
        """Test non-recursive folder scanning."""
        video_files = self.video_scanner.scan_folders([self.test_videos_dir], recursive=False)
        
        # Should find only 3 video files in the main directory
        video_filenames = [vf.filename for vf in video_files]
        expected_videos = ["video1.mp4", "video2.mov", "video3.avi"]
        
        self.assertEqual(len(video_files), 3)
        for expected in expected_videos:
            self.assertIn(expected, video_filenames)
        
        # Should not include files from subdirectory
        self.assertNotIn("video4.mkv", video_filenames)
        self.assertNotIn("video5.mts", video_filenames)
    
    def test_video_file_object_creation(self):
        """Test VideoFile object creation."""
        video_files = self.video_scanner.scan_folders([self.test_videos_dir], recursive=True)
        
        self.assertGreater(len(video_files), 0)
        
        video_file = video_files[0]
        self.assertIsInstance(video_file, VideoFile)
        self.assertTrue(hasattr(video_file, 'path'))
        self.assertTrue(hasattr(video_file, 'filename'))
        self.assertTrue(hasattr(video_file, 'size'))
        self.assertTrue(hasattr(video_file, 'modified_date'))
        self.assertTrue(hasattr(video_file, 'is_accessible'))
        
        # Check that file is accessible
        self.assertTrue(video_file.is_accessible)
        self.assertGreater(video_file.size, 0)
    
    def test_folder_validation(self):
        """Test folder accessibility validation."""
        validation_results = self.video_scanner.validate_folders([
            self.test_videos_dir,  # Should be valid
            "/nonexistent/path",   # Should be invalid
            ""                     # Should be invalid
        ])
        
        self.assertTrue(validation_results[self.test_videos_dir])
        self.assertFalse(validation_results["/nonexistent/path"])
        self.assertFalse(validation_results[""]) 
    
    def test_scan_summary(self):
        """Test scan summary generation."""
        summary = self.video_scanner.get_scan_summary([self.test_videos_dir], recursive=True)
        
        # Check summary structure
        expected_keys = [
            "total_files_found", "accessible_files", "inaccessible_files",
            "total_size_bytes", "directories_scanned", "directories_with_videos",
            "supported_extensions", "scan_mode"
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # Check values
        self.assertEqual(summary["total_files_found"], 5)
        self.assertEqual(summary["accessible_files"], 5)
        self.assertEqual(summary["inaccessible_files"], 0)
        self.assertEqual(summary["directories_scanned"], 1)
        self.assertEqual(summary["scan_mode"], "recursive")
    
    def test_extension_stats(self):
        """Test file extension statistics."""
        stats = self.video_scanner.get_file_extension_stats([self.test_videos_dir], recursive=True)
        
        # Should have stats for each video extension
        expected_extensions = [".mp4", ".mov", ".avi", ".mkv", ".mts"]
        
        for ext in expected_extensions:
            self.assertIn(ext, stats)
            self.assertEqual(stats[ext], 1)  # One file of each type
    
    def test_custom_extensions(self):
        """Test custom supported extensions."""
        custom_scanner = VideoScanner([".mp4", ".mov"])  # Only MP4 and MOV
        
        video_files = custom_scanner.scan_folders([self.test_videos_dir], recursive=True)
        video_filenames = [vf.filename for vf in video_files]
        
        # Should only find MP4 and MOV files
        self.assertIn("video1.mp4", video_filenames)
        self.assertIn("video2.mov", video_filenames)
        self.assertNotIn("video3.avi", video_filenames)
        self.assertNotIn("video4.mkv", video_filenames)
        self.assertNotIn("video5.mts", video_filenames)
    
    def test_group_by_directory(self):
        """Test grouping videos by directory."""
        video_files = self.video_scanner.scan_folders([self.test_videos_dir], recursive=True)
        grouped = self.video_scanner.group_by_directory(video_files)
        
        # Should have two groups: main directory and subdirectory
        self.assertEqual(len(grouped), 2)
        self.assertIn(self.test_videos_dir, grouped)
        self.assertIn(self.test_subdir, grouped)
        
        # Check file counts in each directory
        main_dir_files = grouped[self.test_videos_dir]
        sub_dir_files = grouped[self.test_subdir]
        
        self.assertEqual(len(main_dir_files), 3)  # video1, video2, video3
        self.assertEqual(len(sub_dir_files), 2)   # video4, video5


if __name__ == "__main__":
    unittest.main()