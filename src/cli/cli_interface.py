"""
Command-line interface for the Footage Thumbnailer application.

This module provides a command-line interface with argument parsing and
execution logic for generating video contact sheets.
"""

import argparse
import sys
import time
import os
from typing import List, Optional
from pathlib import Path

from core.config_manager import ConfigManager
from core.video_scanner import VideoScanner
from core.thumbnail_extractor import ThumbnailExtractor
from core.image_composer import ImageComposer, CompositionSettings
from utils.file_utils import (
    ensure_directory_exists,
    create_output_directory,
    format_file_size,
    estimate_processing_time,
    generate_multi_page_filenames
)


class CLIInterface:
    """Command-line interface for the Footage Thumbnailer."""
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.config_manager = None
        self.video_scanner = None
        self.thumbnail_extractor = None
        self.image_composer = None
        self.start_time = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure the argument parser.
        
        Returns:
            Configured ArgumentParser object.
        """
        parser = argparse.ArgumentParser(
            description="Generate visual contact sheets from video collections",
            prog="footage-thumbnailer",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s
  %(prog)s --folders "C:/Videos" "D:/Footage"
  %(prog)s --output "my_overview.jpg" --width 400
  %(prog)s --config "custom_config.json"
  %(prog)s --positions "0%%,25%%,50%%,75%%,99%%"
            """
        )
        
        parser.add_argument(
            "--folders",
            nargs="+",
            metavar="PATH",
            help="Source folder paths to scan for video files"
        )
        
        parser.add_argument(
            "--output",
            metavar="FILE",
            help="Output file path for the contact sheet image"
        )
        
        parser.add_argument(
            "--width",
            type=int,
            metavar="PIXELS",
            help="Thumbnail width in pixels (100-1000)"
        )
        
        parser.add_argument(
            "--rows",
            type=int,
            metavar="NUM",
            help="Number of video clips per row (1-10)"
        )
        
        parser.add_argument(
            "--positions",
            metavar="POS",
            help="Comma-separated thumbnail positions (e.g., '0%%,50%%,99%%')"
        )
        
        parser.add_argument(
            "--config",
            metavar="FILE",
            help="Configuration file path (default: src/config.json)"
        )
        
        parser.add_argument(
            "--no-recursive",
            action="store_true",
            help="Don't scan subdirectories recursively"
        )
        
        parser.add_argument(
            "--font-size",
            type=int,
            metavar="SIZE",
            help="Font size for text overlays"
        )
        
        parser.add_argument(
            "--background",
            choices=["white", "black"],
            help="Background color for the contact sheet"
        )
        
        parser.add_argument(
            "--padding",
            type=int,
            metavar="PIXELS",
            help="Padding between thumbnails in pixels"
        )
        
        parser.add_argument(
            "--overlay-position",
            choices=["on_thumbnails", "above_thumbnails"],
            help="Position text overlays on thumbnails or above them"
        )
        
        parser.add_argument(
            "--no-frame",
            action="store_true",
            help="Disable frame borders around each video section"
        )
        
        parser.add_argument(
            "--frame-color",
            metavar="COLOR",
            help="Frame border color (e.g., '#CCCCCC', 'gray', 'black')"
        )
        
        parser.add_argument(
            "--max-rows",
            type=int,
            metavar="NUM",
            help="Maximum rows per image (0=unlimited, creates multiple images if exceeded)"
        )
        
        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 1.0.0"
        )
        
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be processed without actually processing"
        )
        
        return parser
    
    def parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command-line arguments.
        
        Args:
            args: List of arguments to parse. If None, uses sys.argv.
            
        Returns:
            Parsed arguments namespace.
        """
        parser = self.create_parser()
        return parser.parse_args(args)
    
    def initialize_components(self, config_path: Optional[str] = None) -> bool:
        """
        Initialize core components with configuration.
        
        Args:
            config_path: Path to configuration file.
            
        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager(config_path)
            config = self.config_manager.load_config()
            
            # Initialize components
            self.video_scanner = VideoScanner(config.get("supported_extensions"))
            self.thumbnail_extractor = ThumbnailExtractor()
            
            # Create composition settings from config
            composition_settings = CompositionSettings(
                clips_per_row=config.get("clips_per_row", 5),
                padding=config.get("padding", 5),
                background_color=config.get("background_color", "white"),
                font_size=config.get("font_size", 12),
                text_color=config.get("text_color", "white"),
                overlay_background_color=config.get("overlay_background_color", "black"),
                overlay_background_opacity=config.get("overlay_background_opacity", 0.7),
                overlay_position=config.get("overlay_position", "above_thumbnails"),
                show_frame=config.get("show_frame", True),
                frame_color=config.get("frame_color", "#CCCCCC"),
                frame_thickness=config.get("frame_thickness", 2),
                frame_padding=config.get("frame_padding", 10),
                max_rows_per_image=config.get("max_rows_per_image", 0)
            )
            
            self.image_composer = ImageComposer(composition_settings)
            
            return True
            
        except Exception as e:
            print(f"Error initializing components: {e}")
            return False
    
    def apply_cli_overrides(self, args: argparse.Namespace) -> dict:
        """
        Apply command-line argument overrides to configuration.
        
        Args:
            args: Parsed command-line arguments.
            
        Returns:
            Updated configuration dictionary.
        """
        config = self.config_manager.load_config()
        
        # Apply overrides
        if args.folders:
            config["source_folders"] = args.folders
        
        if args.output:
            config["output_path"] = args.output
        
        if args.width:
            if 100 <= args.width <= 1000:
                config["thumbnail_width"] = args.width
            else:
                print("Warning: Width must be between 100 and 1000 pixels")
        
        if args.rows:
            if 1 <= args.rows <= 10:
                config["clips_per_row"] = args.rows
            else:
                print("Warning: Clips per row must be between 1 and 10")
        
        if args.positions:
            config["positions"] = args.positions
        
        if args.font_size:
            config["font_size"] = args.font_size
        
        if args.background:
            config["background_color"] = args.background
        
        if args.padding is not None:
            if args.padding >= 0:
                config["padding"] = args.padding
            else:
                print("Warning: Padding must be non-negative")
        
        if hasattr(args, 'overlay_position') and args.overlay_position:
            config["overlay_position"] = args.overlay_position
        
        if hasattr(args, 'no_frame') and args.no_frame:
            config["show_frame"] = False
        
        if hasattr(args, 'frame_color') and args.frame_color:
            config["frame_color"] = args.frame_color
        
        if hasattr(args, 'max_rows') and args.max_rows is not None:
            if args.max_rows >= 0:
                config["max_rows_per_image"] = args.max_rows
            else:
                print("Warning: Max rows must be non-negative (0=unlimited)")
        
        return config
    
    def update_image_composer_settings(self, config: dict) -> None:
        """
        Update the image composer settings with new configuration.
        
        Args:
            config: Updated configuration dictionary.
        """
        if self.image_composer:
            # Create new composition settings from updated config
            new_settings = CompositionSettings(
                clips_per_row=config.get("clips_per_row", 5),
                padding=config.get("padding", 5),
                background_color=config.get("background_color", "white"),
                font_size=config.get("font_size", 12),
                text_color=config.get("text_color", "white"),
                overlay_background_color=config.get("overlay_background_color", "black"),
                overlay_background_opacity=config.get("overlay_background_opacity", 0.7),
                overlay_position=config.get("overlay_position", "above_thumbnails"),
                show_frame=config.get("show_frame", True),
                frame_color=config.get("frame_color", "#CCCCCC"),
                frame_thickness=config.get("frame_thickness", 2),
                frame_padding=config.get("frame_padding", 10),
                max_rows_per_image=config.get("max_rows_per_image", 0)
            )
            
            # Update the image composer with new settings
            self.image_composer.settings = new_settings
    
    def progress_callback(self, current: int, total: int, filename: str) -> None:
        """
        Progress callback for processing updates.
        
        Args:
            current: Current file index (1-based).
            total: Total number of files.
            filename: Current filename being processed.
        """
        percent = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"\r[{bar}] {percent:5.1f}% ({current}/{total}) - {filename}", end="", flush=True)
    
    def run_dry_run(self, config: dict, recursive: bool = True, verbose: bool = False) -> None:
        """
        Perform a dry run showing what would be processed.
        
        Args:
            config: Configuration dictionary.
            recursive: Whether to scan recursively.
            verbose: Whether to show verbose output.
        """
        print("=== DRY RUN MODE ===")
        print("This shows what would be processed without actually processing files.\n")
        
        # Get source folders
        source_folders = config.get("source_folders", [])
        if not source_folders:
            print("No source folders specified.")
            return
        
        print("Source folders:")
        for folder in source_folders:
            print(f"  - {folder}")
        print()
        
        # Validate folders
        validation_results = self.video_scanner.validate_folders(source_folders)
        invalid_folders = [folder for folder, valid in validation_results.items() if not valid]
        
        if invalid_folders:
            print("Invalid/inaccessible folders:")
            for folder in invalid_folders:
                print(f"  - {folder}")
            print()
        
        # Scan for videos
        valid_folders = [folder for folder, valid in validation_results.items() if valid]
        if not valid_folders:
            print("No accessible folders to scan.")
            return
        
        print("Scanning for video files...")
        video_files = self.video_scanner.scan_folders(valid_folders, recursive)
        accessible_files = self.video_scanner.filter_accessible_files(video_files)
        
        # Show summary
        summary = self.video_scanner.get_scan_summary(valid_folders, recursive)
        total_size = format_file_size(summary["total_size_bytes"])
        estimated_time = estimate_processing_time(len(accessible_files))
        
        print(f"Found {summary['total_files_found']} video files")
        print(f"Accessible: {summary['accessible_files']}")
        print(f"Inaccessible: {summary['inaccessible_files']}")
        print(f"Total size: {total_size}")
        print(f"Estimated processing time: {estimated_time}")
        print()
        
        # Show settings
        positions = config.get("positions", "0%,50%,99%").split(",")
        print("Processing settings:")
        print(f"  Thumbnail width: {config.get('thumbnail_width', 320)}px")
        print(f"  Positions per video: {len(positions)} ({config.get('positions', '0%,50%,99%')})")
        print(f"  Clips per row: {config.get('clips_per_row', 5)}")
        print(f"  Output path: {config.get('output_path', 'output/overview.jpg')}")
        print()
        
        # Show file list if verbose
        if verbose and accessible_files:
            print("Files to be processed:")
            for i, video_file in enumerate(accessible_files, 1):
                file_size = format_file_size(video_file.size)
                print(f"  {i:3d}. {video_file.filename} ({file_size})")
            print()
        
        # Estimate output size
        estimated_size = self.image_composer.estimate_output_size(
            len(accessible_files),
            config.get("thumbnail_width", 320),
            len(positions)
        )
        print(f"Estimated output image size: {estimated_size[0]}x{estimated_size[1]} pixels")
        print("\n=== END DRY RUN ===")
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Main execution method for the CLI interface.
        
        Args:
            args: Command-line arguments. If None, uses sys.argv.
            
        Returns:
            Exit code (0 for success, non-zero for error).
        """
        try:
            # Parse arguments
            parsed_args = self.parse_arguments(args)
            
            # Show header
            print("Footage Thumbnailer v1.0")
            print("=" * 24)
            
            # Initialize components
            if not self.initialize_components(parsed_args.config):
                return 1
            
            # Apply CLI overrides
            config = self.apply_cli_overrides(parsed_args)
            
            # Update image composer with overridden settings
            self.update_image_composer_settings(config)
            
            # Check for source folders
            source_folders = config.get("source_folders", [])
            if not source_folders:
                print("Error: No source folders specified.")
                print("Use --folders option or add folders to config.json")
                return 1
            
            # Perform dry run if requested
            if parsed_args.dry_run:
                self.run_dry_run(config, not parsed_args.no_recursive, parsed_args.verbose)
                return 0
            
            # Start processing
            self.start_time = time.time()
            recursive = not parsed_args.no_recursive
            
            print("Scanning folders...")
            if parsed_args.verbose:
                for folder in source_folders:
                    print(f"  Scanning: {folder}")
            
            # Scan for video files
            video_files = self.video_scanner.scan_folders(source_folders, recursive)
            accessible_files = self.video_scanner.filter_accessible_files(video_files)
            
            if not accessible_files:
                print("No accessible video files found.")
                return 1
            
            print(f"Found {len(accessible_files)} video files")
            
            # Parse positions
            positions = [pos.strip() for pos in config.get("positions", "0%,50%,99%").split(",")]
            
            # Process videos
            print("Processing videos:")
            processed_videos = self.thumbnail_extractor.batch_process_videos(
                accessible_files,
                positions,
                config.get("thumbnail_width", 320),
                self.progress_callback if not parsed_args.verbose else None
            )
            
            print()  # New line after progress bar
            
            # Filter successful videos
            successful_videos = [vd for vd in processed_videos if vd.processing_status == "success"]
            failed_videos = len(processed_videos) - len(successful_videos)
            
            if failed_videos > 0:
                print(f"Warning: {failed_videos} videos failed to process")
            
            if not successful_videos:
                print("Error: No videos were successfully processed")
                return 1
            
            print("Composing final image...")
            
            # Create contact sheet
            contact_sheet = self.image_composer.create_contact_sheet(successful_videos)
            
            # Ensure output directory exists
            output_path = config.get("output_path", "output/overview.jpg")
            if not create_output_directory(output_path):
                print(f"Error: Could not create output directory for {output_path}")
                return 1
            
            # Save the contact sheet
            contact_sheet.save(output_path, quality=95, optimize=True)
            
            # Check for additional pages and save them
            additional_pages = self.image_composer.get_additional_pages()
            saved_files = [output_path]
            
            if additional_pages:
                # Generate filenames for all pages
                total_pages = len(additional_pages) + 1  # +1 for the main page
                all_filenames = generate_multi_page_filenames(output_path, total_pages)
                
                # Save additional pages
                for i, page in enumerate(additional_pages):
                    page_filename = all_filenames[i + 1]  # Skip first filename (already used)
                    page.save(page_filename, quality=95, optimize=True)
                    saved_files.append(page_filename)
                
                print(f"Multi-page output: {total_pages} images created")
            
            # Show completion summary
            elapsed_time = time.time() - self.start_time
            total_output_size = sum(os.path.getsize(f) if os.path.exists(f) else 0 for f in saved_files)
            
            if len(saved_files) == 1:
                print(f"Contact sheet saved to: {output_path}")
                print(f"Output size: {format_file_size(total_output_size)}")
                print(f"Image dimensions: {contact_sheet.size[0]}x{contact_sheet.size[1]} pixels")
            else:
                print(f"Contact sheets saved:")
                for filename in saved_files:
                    if os.path.exists(filename):
                        size = format_file_size(os.path.getsize(filename))
                        print(f"  - {filename} ({size})")
                print(f"Total output size: {format_file_size(total_output_size)}")
            
            print(f"Total processing time: {self._format_elapsed_time(elapsed_time)}")
            
            return 0
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Error: {e}")
            if parsed_args.verbose if 'parsed_args' in locals() else False:
                import traceback
                traceback.print_exc()
            return 1
    
    def _format_elapsed_time(self, seconds: float) -> str:
        """
        Format elapsed time in a human-readable format.
        
        Args:
            seconds: Elapsed time in seconds.
            
        Returns:
            Formatted time string.
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"


def main() -> int:
    """
    Main entry point for the CLI application.
    
    Returns:
        Exit code.
    """
    cli = CLIInterface()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())