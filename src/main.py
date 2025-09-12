"""
Main application entry point for the Footage Thumbnailer.

This module serves as the primary entry point for the application,
handling both CLI and future GUI mode selection.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from cli.cli_interface import CLIInterface


def main():
    """
    Main application entry point.
    
    Determines the execution mode and delegates to the appropriate interface.
    Supports both CLI and GUI modes.
    """
    # Check for GUI mode arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["--gui", "gui"]:
        try:
            # Import GUI here to avoid dependency issues if CustomTkinter is not available
            from gui.gui_application import GUIApplication
            
            print("Starting GUI mode...")
            app = GUIApplication()
            return app.run()
            
        except ImportError as e:
            print(f"Error: GUI dependencies not available: {e}")
            print("Please install CustomTkinter: pip install customtkinter")
            return 1
        except Exception as e:
            print(f"Error starting GUI: {e}")
            return 1
    
    # Default to CLI interface
    cli = CLIInterface()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())