"""
Test script to verify the FCPXML processing fix.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.config_manager import ConfigManager
from core.unified_processor import UnifiedProcessor


def test_fcpxml_processing():
    """Test FCPXML processing with the fix."""
    print("Testing FCPXML processing fix...")
    
    # Initialize components
    config_manager = ConfigManager()
    processor = UnifiedProcessor(config_manager)
    
    # Set up logging and progress callbacks
    def log_callback(message):
        print(f"[LOG] {message}")
    
    def progress_callback(progress, message):
        print(f"[PROGRESS] {progress:.0%} - {message}")
    
    processor.set_log_callback(log_callback)
    processor.set_progress_callback(progress_callback)
    
    # Process thumbnails
    print("Starting thumbnail processing...")
    success = processor.process_thumbnails()
    
    if success:
        print("✅ FCPXML processing completed successfully!")
        return True
    else:
        print("❌ FCPXML processing failed!")
        return False


if __name__ == "__main__":
    test_fcpxml_processing()