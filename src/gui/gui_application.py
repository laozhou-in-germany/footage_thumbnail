"""
GUI Application for the Footage Thumbnailer.

This module provides a modern, user-friendly graphical interface for the 
Footage Thumbnailer application using CustomTkinter framework.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import customtkinter as ctk
import threading
import queue
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import json

# Add parent directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.config_manager import ConfigManager
from core.video_scanner import VideoScanner
from core.thumbnail_extractor import ThumbnailExtractor
from core.image_composer import ImageComposer, CompositionSettings
from core.unified_processor import UnifiedProcessor
from cli.cli_interface import CLIInterface


class GUIApplication:
    """Main GUI application class using CustomTkinter."""
    
    def __init__(self):
        """Initialize the GUI application."""
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("system")  # "dark" or "light"
        ctk.set_default_color_theme("blue")
        
        # Initialize core components
        self.config_manager = ConfigManager()
        self.video_scanner = VideoScanner()
        self.thumbnail_extractor = ThumbnailExtractor()
        self.image_composer = ImageComposer()
        
        # GUI state variables
        self.processing = False
        self.processing_thread = None
        self.progress_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # Initialize main window
        self.root = ctk.CTk()
        self.setup_main_window()
        
        # Create UI components first
        self.create_ui_components()
        
        # Then load configuration and setup
        self.load_configuration()
        self.setup_event_handlers()
        
        # Start queue monitoring
        self.monitor_queues()
    
    def setup_main_window(self):
        """Configure the main application window."""
        self.root.title("Footage Thumbnailer")
        self.root.geometry("900x800")
        self.root.minsize(800, 600)
        
        # Configure grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main container with scrollable frame
        self.main_container = ctk.CTkScrollableFrame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
    
    def create_ui_components(self):
        """Create all UI components."""
        current_row = 0
        
        # Source Folders Section
        current_row = self.create_source_folders_section(current_row)
        
        # Basic Settings Section
        current_row = self.create_basic_settings_section(current_row)
        
        # Text & Overlay Settings Section
        current_row = self.create_text_overlay_section(current_row)
        
        # Frame Settings Section
        current_row = self.create_frame_settings_section(current_row)
        
        # Output Section
        current_row = self.create_output_section(current_row)
        
        # Processing Section
        current_row = self.create_processing_section(current_row)
        
        # Preview Section
        current_row = self.create_preview_section(current_row)
        
        # Log Section
        current_row = self.create_log_section(current_row)
    
    def create_source_folders_section(self, row: int) -> int:
        """Create the source folders selection section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(0, weight=1)
        
        # Section title
        title_label = ctk.CTkLabel(section_frame, text="📁 Source Folders", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Folder list display
        self.folder_list_text = ctk.CTkTextbox(section_frame, height=80)
        self.folder_list_text.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Buttons
        self.select_folders_btn = ctk.CTkButton(button_frame, text="Select Folders...",
                                               command=self.select_folders)
        self.select_folders_btn.grid(row=0, column=0, padx=(0, 10), pady=5)
        
        self.clear_folders_btn = ctk.CTkButton(button_frame, text="Clear All",
                                              command=self.clear_folders)
        self.clear_folders_btn.grid(row=0, column=1, pady=5)
        
        # FCPXML File Section (seamlessly integrated)
        fcpxml_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        fcpxml_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(10, 0))
        fcpxml_frame.grid_columnconfigure(0, weight=1)
        
        # FCPXML file label
        fcpxml_label = ctk.CTkLabel(fcpxml_frame, text="📄 FCPXML File (Optional)", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        fcpxml_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # FCPXML file selection frame
        fcpxml_selection_frame = ctk.CTkFrame(fcpxml_frame, fg_color="transparent")
        fcpxml_selection_frame.grid(row=1, column=0, sticky="ew", pady=5)
        fcpxml_selection_frame.grid_columnconfigure(0, weight=1)
        
        # FCPXML file path entry
        self.fcpxml_file_var = ctk.StringVar(value="")
        self.fcpxml_file_entry = ctk.CTkEntry(fcpxml_selection_frame, textvariable=self.fcpxml_file_var,
                                          placeholder_text="No FCPXML file selected")
        self.fcpxml_file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # FCPXML file buttons frame
        fcpxml_buttons_frame = ctk.CTkFrame(fcpxml_selection_frame, fg_color="transparent")
        fcpxml_buttons_frame.grid(row=0, column=1)
        
        self.browse_fcpxml_btn = ctk.CTkButton(fcpxml_buttons_frame, text="Browse...", width=80,
                                           command=self.browse_fcpxml_file)
        self.browse_fcpxml_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.clear_fcpxml_btn = ctk.CTkButton(fcpxml_buttons_frame, text="Clear", width=60,
                                          command=self.clear_fcpxml_file)
        self.clear_fcpxml_btn.grid(row=0, column=1)
        
        # FCPXML info label
        self.fcpxml_info_label = ctk.CTkLabel(fcpxml_frame, 
                                          text="ℹ️ When FCPXML file is provided, videos will be sourced from FCPXML references",
                                          font=ctk.CTkFont(size=11), 
                                          text_color="gray")
        self.fcpxml_info_label.grid(row=2, column=0, sticky="w", pady=(5, 10))
        
        # New checkbox for FCPXML interval positions
        self.fcpxml_use_interval_positions_var = ctk.BooleanVar(value=True)
        self.fcpxml_use_interval_positions_checkbox = ctk.CTkCheckBox(
            fcpxml_frame, 
            text="Use FCPXML In/Out Points for Thumbnail Positions",
            variable=self.fcpxml_use_interval_positions_var,
            hover=True
        )
        self.fcpxml_use_interval_positions_checkbox.grid(row=3, column=0, sticky="w", pady=(0, 10))
        
        # Add tooltip as a label below the checkbox
        tooltip_label = ctk.CTkLabel(
            fcpxml_frame, 
            text="When enabled, thumbnail positions are calculated relative to the clip's in/out points in the FCPXML. When disabled, absolute video positions are used.",
            font=ctk.CTkFont(size=10), 
            text_color="gray"
        )
        tooltip_label.grid(row=4, column=0, sticky="w", padx=(20, 0), pady=(0, 10))
        
        return row + 1
    
    def create_basic_settings_section(self, row: int) -> int:
        """Create the basic settings section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(1, weight=1)
        
        # Section title with expand/collapse button
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        title_frame.grid_columnconfigure(1, weight=1)
        
        self.basic_settings_expanded = ctk.BooleanVar(value=False)  # Collapsed by default
        self.basic_settings_toggle_btn = ctk.CTkButton(title_frame, text="▶", width=30, height=30,
                                                    command=self.toggle_basic_settings_section)
        self.basic_settings_toggle_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(title_frame, text="⚙️ Basic Settings", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=1, sticky="w")
        
        # Content frame (initially hidden)
        self.basic_settings_content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        self.basic_settings_content_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.basic_settings_content_frame.grid_columnconfigure((0, 1), weight=1)
        self.basic_settings_content_frame.grid_remove()  # Hide initially
        
        # Left column frame
        left_frame = ctk.CTkFrame(self.basic_settings_content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        
        # Right column frame
        right_frame = ctk.CTkFrame(self.basic_settings_content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)
        
        # Thumbnail Width
        ctk.CTkLabel(left_frame, text="Thumbnail Width:").grid(row=0, column=0, sticky="w", pady=2)
        width_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        width_frame.grid(row=1, column=0, sticky="ew", pady=2)
        self.thumbnail_width_var = ctk.StringVar(value="320")
        self.thumbnail_width_entry = ctk.CTkEntry(width_frame, textvariable=self.thumbnail_width_var, width=100)
        self.thumbnail_width_entry.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(width_frame, text="px").grid(row=0, column=1)
        
        # Clips Per Row
        ctk.CTkLabel(right_frame, text="Clips Per Row:").grid(row=0, column=0, sticky="w", pady=2)
        self.clips_per_row_var = ctk.StringVar(value="5")
        self.clips_per_row_entry = ctk.CTkEntry(right_frame, textvariable=self.clips_per_row_var, width=100)
        self.clips_per_row_entry.grid(row=1, column=0, sticky="w", pady=2)
        
        # Thumbnail Positions
        ctk.CTkLabel(left_frame, text="Thumbnail Positions:").grid(row=2, column=0, sticky="w", pady=2)
        self.positions_var = ctk.StringVar(value="0%,50%,99%")
        self.positions_entry = ctk.CTkEntry(left_frame, textvariable=self.positions_var, width=200)
        self.positions_entry.grid(row=3, column=0, sticky="ew", pady=2)
        
        # Output Format
        ctk.CTkLabel(right_frame, text="Output Format:").grid(row=2, column=0, sticky="w", pady=2)
        self.format_var = ctk.StringVar(value="JPEG")
        self.format_combo = ctk.CTkComboBox(right_frame, variable=self.format_var, 
                                           values=["JPEG", "PNG"], width=100)
        self.format_combo.grid(row=3, column=0, sticky="w", pady=2)
        
        # Max Rows Per Image
        ctk.CTkLabel(left_frame, text="Max Rows Per Image:").grid(row=4, column=0, sticky="w", pady=2)
        max_rows_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        max_rows_frame.grid(row=5, column=0, sticky="ew", pady=2)
        self.max_rows_var = ctk.StringVar(value="0")
        self.max_rows_entry = ctk.CTkEntry(max_rows_frame, textvariable=self.max_rows_var, width=100)
        self.max_rows_entry.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(max_rows_frame, text="(0=all)").grid(row=0, column=1)
        
        # Padding
        ctk.CTkLabel(right_frame, text="Padding:").grid(row=4, column=0, sticky="w", pady=2)
        padding_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        padding_frame.grid(row=5, column=0, sticky="ew", pady=2)
        self.padding_var = ctk.StringVar(value="5")
        self.padding_entry = ctk.CTkEntry(padding_frame, textvariable=self.padding_var, width=100)
        self.padding_entry.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(padding_frame, text="px").grid(row=0, column=1)
        
        return row + 1
    
    def create_text_overlay_section(self, row: int) -> int:
        """Create the text & overlay settings section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(1, weight=1)
        
        # Section title with expand/collapse button
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        title_frame.grid_columnconfigure(1, weight=1)
        
        self.text_overlay_expanded = ctk.BooleanVar(value=False)  # Collapsed by default
        self.text_overlay_toggle_btn = ctk.CTkButton(title_frame, text="▶", width=30, height=30,
                                                    command=self.toggle_text_overlay_section)
        self.text_overlay_toggle_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(title_frame, text="🎨 Text & Overlay Settings", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=1, sticky="w")
        
        # Content frame (initially hidden)
        self.text_overlay_content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        self.text_overlay_content_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.text_overlay_content_frame.grid_columnconfigure((0, 1), weight=1)
        self.text_overlay_content_frame.grid_remove()  # Hide initially
        
        # Left column frame
        left_frame = ctk.CTkFrame(self.text_overlay_content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        
        # Right column frame
        right_frame = ctk.CTkFrame(self.text_overlay_content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)
        
        # Font Size
        ctk.CTkLabel(left_frame, text="Font Size:").grid(row=0, column=0, sticky="w", pady=2)
        font_size_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        font_size_frame.grid(row=1, column=0, sticky="ew", pady=2)
        self.font_size_var = ctk.StringVar(value="12")
        self.font_size_entry = ctk.CTkEntry(font_size_frame, textvariable=self.font_size_var, width=100)
        self.font_size_entry.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(font_size_frame, text="px").grid(row=0, column=1)
        
        # Overlay Position
        ctk.CTkLabel(right_frame, text="Overlay Position:").grid(row=0, column=0, sticky="w", pady=2)
        position_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        position_frame.grid(row=1, column=0, sticky="ew", pady=2)
        self.overlay_position_var = ctk.StringVar(value="above_thumbnails")
        self.position_radio1 = ctk.CTkRadioButton(position_frame, text="Above Thumbnails", 
                                                 variable=self.overlay_position_var, 
                                                 value="above_thumbnails")
        self.position_radio1.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.position_radio2 = ctk.CTkRadioButton(position_frame, text="On Thumbnails", 
                                                 variable=self.overlay_position_var, 
                                                 value="on_thumbnails")
        self.position_radio2.grid(row=0, column=1, sticky="w")
        
        # Text Color
        ctk.CTkLabel(left_frame, text="Text Color:").grid(row=2, column=0, sticky="w", pady=2)
        text_color_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        text_color_frame.grid(row=3, column=0, sticky="ew", pady=2)
        self.text_color_var = ctk.StringVar(value="black")
        self.text_color_btn = ctk.CTkButton(text_color_frame, text="⬛ Black", width=100,
                                           command=lambda: self.choose_color("text"))
        self.text_color_btn.grid(row=0, column=0)
        
        # Background Color
        ctk.CTkLabel(right_frame, text="Background Color:").grid(row=2, column=0, sticky="w", pady=2)
        bg_color_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        bg_color_frame.grid(row=3, column=0, sticky="ew", pady=2)
        self.bg_color_var = ctk.StringVar(value="black")
        self.bg_color_btn = ctk.CTkButton(bg_color_frame, text="⬛ Black", width=100,
                                         command=lambda: self.choose_color("background"))
        self.bg_color_btn.grid(row=0, column=0)
        
        # Text Opacity
        ctk.CTkLabel(left_frame, text="Text Opacity:").grid(row=4, column=0, sticky="w", pady=2)
        self.text_opacity_var = ctk.DoubleVar(value=0.7)
        self.text_opacity_slider = ctk.CTkSlider(left_frame, from_=0, to=1, 
                                                variable=self.text_opacity_var)
        self.text_opacity_slider.grid(row=5, column=0, sticky="ew", pady=2)
        self.text_opacity_label = ctk.CTkLabel(left_frame, text="70%")
        self.text_opacity_label.grid(row=6, column=0, pady=2)
        
        # Background Opacity
        ctk.CTkLabel(right_frame, text="Background Opacity:").grid(row=4, column=0, sticky="w", pady=2)
        self.bg_opacity_var = ctk.DoubleVar(value=0.7)
        self.bg_opacity_slider = ctk.CTkSlider(right_frame, from_=0, to=1, 
                                              variable=self.bg_opacity_var)
        self.bg_opacity_slider.grid(row=5, column=0, sticky="ew", pady=2)
        self.bg_opacity_label = ctk.CTkLabel(right_frame, text="70%")
        self.bg_opacity_label.grid(row=6, column=0, pady=2)
        
        # Bind slider events
        self.text_opacity_slider.configure(command=lambda v: self.update_opacity_label("text", v))
        self.bg_opacity_slider.configure(command=lambda v: self.update_opacity_label("bg", v))
        
        return row + 1
    
    def create_frame_settings_section(self, row: int) -> int:
        """Create the frame settings section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(1, weight=1)
        
        # Section title with expand/collapse button
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        title_frame.grid_columnconfigure(1, weight=1)
        
        self.frame_settings_expanded = ctk.BooleanVar(value=False)  # Collapsed by default
        self.frame_settings_toggle_btn = ctk.CTkButton(title_frame, text="▶", width=30, height=30,
                                                      command=self.toggle_frame_settings_section)
        self.frame_settings_toggle_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(title_frame, text="🖼️ Frame Settings", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=1, sticky="w")
        
        # Content frame (initially hidden)
        self.frame_settings_content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        self.frame_settings_content_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.frame_settings_content_frame.grid_columnconfigure(0, weight=1)
        self.frame_settings_content_frame.grid_remove()  # Hide initially
        
        # Frame enable checkbox
        self.show_frame_var = ctk.BooleanVar(value=True)
        self.show_frame_checkbox = ctk.CTkCheckBox(self.frame_settings_content_frame, text="Show Frame Borders",
                                                  variable=self.show_frame_var,
                                                  command=self.toggle_frame_settings)
        self.show_frame_checkbox.grid(row=0, column=0, sticky="w", padx=0, pady=5)
        
        # Frame settings frame
        self.frame_settings_frame = ctk.CTkFrame(self.frame_settings_content_frame, fg_color="transparent")
        self.frame_settings_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=5)
        self.frame_settings_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Frame Color
        color_frame = ctk.CTkFrame(self.frame_settings_frame, fg_color="transparent")
        color_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(color_frame, text="Frame Color:").grid(row=0, column=0, sticky="w", pady=2)
        self.frame_color_var = ctk.StringVar(value="#CCCCCC")
        self.frame_color_btn = ctk.CTkButton(color_frame, text="⬛ #CCCCCC", width=100,
                                            command=lambda: self.choose_color("frame"))
        self.frame_color_btn.grid(row=1, column=0, pady=2)
        
        # Frame Thickness
        thickness_frame = ctk.CTkFrame(self.frame_settings_frame, fg_color="transparent")
        thickness_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(thickness_frame, text="Thickness:").grid(row=0, column=0, sticky="w", pady=2)
        thick_entry_frame = ctk.CTkFrame(thickness_frame, fg_color="transparent")
        thick_entry_frame.grid(row=1, column=0, sticky="ew", pady=2)
        self.frame_thickness_var = ctk.StringVar(value="2")
        self.frame_thickness_entry = ctk.CTkEntry(thick_entry_frame, textvariable=self.frame_thickness_var, width=60)
        self.frame_thickness_entry.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(thick_entry_frame, text="px").grid(row=0, column=1)
        
        # Frame Padding
        padding_frame = ctk.CTkFrame(self.frame_settings_frame, fg_color="transparent")
        padding_frame.grid(row=0, column=2, sticky="ew")
        ctk.CTkLabel(padding_frame, text="Frame Padding:").grid(row=0, column=0, sticky="w", pady=2)
        pad_entry_frame = ctk.CTkFrame(padding_frame, fg_color="transparent")
        pad_entry_frame.grid(row=1, column=0, sticky="ew", pady=2)
        self.frame_padding_var = ctk.StringVar(value="10")
        self.frame_padding_entry = ctk.CTkEntry(pad_entry_frame, textvariable=self.frame_padding_var, width=60)
        self.frame_padding_entry.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(pad_entry_frame, text="px").grid(row=0, column=1)
        
        return row + 1
    
    def create_output_section(self, row: int) -> int:
        """Create the output section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(0, weight=1)
        
        # Section title
        title_label = ctk.CTkLabel(section_frame, text="📤 Output", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Output path frame
        path_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        path_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        path_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(path_frame, text="Output Path:").grid(row=0, column=0, sticky="w", pady=2)
        
        entry_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        entry_frame.grid(row=1, column=0, sticky="ew", pady=2)
        entry_frame.grid_columnconfigure(0, weight=1)
        
        self.output_path_var = ctk.StringVar(value="output/overview.jpg")
        self.output_path_entry = ctk.CTkEntry(entry_frame, textvariable=self.output_path_var)
        self.output_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(entry_frame, text="Browse...", width=100,
                                       command=self.browse_output_path)
        self.browse_btn.grid(row=0, column=1)
        
        return row + 1
    
    def create_processing_section(self, row: int) -> int:
        """Create the processing control section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(0, weight=1)
        
        # Generate button
        self.generate_btn = ctk.CTkButton(section_frame, text="Generate Overview", 
                                         font=ctk.CTkFont(size=16, weight="bold"),
                                         height=40, command=self.start_processing)
        self.generate_btn.grid(row=0, column=0, padx=20, pady=20)
        
        # Progress frame
        progress_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        progress_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = ctk.DoubleVar(value=0.0)
        self.progress_bar = ctk.CTkProgressBar(progress_frame, variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Status label
        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, pady=5)
        
        return row + 1
    
    def create_preview_section(self, row: int) -> int:
        """Create the preview section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(0, weight=1)
        section_frame.grid_rowconfigure(1, weight=1)
        
        # Section title
        title_label = ctk.CTkLabel(section_frame, text="👁️ Preview", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Content frame
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Create a frame for the file list and preview area
        preview_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        preview_frame.grid(row=0, column=0, sticky="nsew")
        preview_frame.grid_columnconfigure(1, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        # File list frame
        file_list_frame = ctk.CTkFrame(preview_frame)
        file_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        file_list_frame.grid_columnconfigure(0, weight=1)
        file_list_frame.grid_rowconfigure(1, weight=1)
        
        # File list label
        file_list_label = ctk.CTkLabel(file_list_frame, text="Generated Files:")
        file_list_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Replace the CTkTextbox with CTkScrollableFrame for better file list display
        self.preview_file_list_frame = ctk.CTkScrollableFrame(file_list_frame, width=200, height=150)
        self.preview_file_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.preview_file_list_items = []  # Track list items for selection management
        self.selected_file_item = None    # Track currently selected item
        
        # Preview area frame
        preview_area_frame = ctk.CTkFrame(preview_frame)
        preview_area_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        preview_area_frame.grid_columnconfigure(0, weight=1)
        preview_area_frame.grid_rowconfigure(1, weight=1)
        
        # Preview label
        preview_label = ctk.CTkLabel(preview_area_frame, text="Preview:")
        preview_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Preview image label
        self.preview_image_label = ctk.CTkLabel(preview_area_frame, text="No preview available", 
                                               fg_color=("gray80", "gray20"))
        self.preview_image_label.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        
        # Refresh button
        self.refresh_preview_btn = ctk.CTkButton(buttons_frame, text="Refresh Preview", 
                                                command=self.refresh_preview)
        self.refresh_preview_btn.grid(row=0, column=0)
        
        # Load initial preview
        self.refresh_preview()
        
        return row + 1
    
    def create_log_section(self, row: int) -> int:
        """Create the logging section."""
        # Section frame
        section_frame = ctk.CTkFrame(self.main_container)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(0, weight=1)
        section_frame.grid_rowconfigure(1, weight=1)
        
        # Section title and clear button frame
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(title_frame, text="📋 Log", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        self.clear_log_btn = ctk.CTkButton(title_frame, text="Clear Log", width=100,
                                          command=self.clear_log)
        self.clear_log_btn.grid(row=0, column=1)
        
        # Log text area
        self.log_text = ctk.CTkTextbox(section_frame, height=150)
        self.log_text.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        return row + 1
    
    def setup_event_handlers(self):
        """Setup event handlers for UI components."""
        # Bind validation events
        self.thumbnail_width_entry.bind('<FocusOut>', self.validate_thumbnail_width)
        self.clips_per_row_entry.bind('<FocusOut>', self.validate_clips_per_row)
        self.positions_entry.bind('<FocusOut>', self.validate_positions)
        self.font_size_entry.bind('<FocusOut>', self.validate_font_size)
        self.frame_thickness_entry.bind('<FocusOut>', self.validate_frame_thickness)
        self.frame_padding_entry.bind('<FocusOut>', self.validate_frame_padding)
        self.max_rows_entry.bind('<FocusOut>', self.validate_max_rows)
        self.padding_entry.bind('<FocusOut>', self.validate_padding)
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_configuration(self):
        """Load configuration from config manager and populate UI fields."""
        config = self.config_manager.load_config()
        
        # Source folders
        source_folders = config.get('source_folders', [])
        self.update_folder_display(source_folders)
        
        # Basic settings
        self.thumbnail_width_var.set(str(config.get('thumbnail_width', 320)))
        self.clips_per_row_var.set(str(config.get('clips_per_row', 5)))
        self.positions_var.set(config.get('positions', '0%,50%,99%'))
        self.padding_var.set(str(config.get('padding', 5)))
        self.max_rows_var.set(str(config.get('max_rows_per_image', 0)))
        
        # Format
        output_path = config.get('output_path', 'output/overview.jpg')
        self.output_path_var.set(output_path)
        if output_path.lower().endswith('.png'):
            self.format_var.set('PNG')
        else:
            self.format_var.set('JPEG')
        
        # Text & overlay settings
        self.font_size_var.set(str(config.get('font_size', 12)))
        self.overlay_position_var.set(config.get('overlay_position', 'above_thumbnails'))
        self.text_color_var.set(config.get('text_color', 'black'))
        self.bg_color_var.set(config.get('overlay_background_color', 'black'))
        self.text_opacity_var.set(config.get('overlay_opacity', 0.7))
        self.bg_opacity_var.set(config.get('overlay_background_opacity', 0.7))
        
        # Frame settings
        self.show_frame_var.set(config.get('show_frame', True))
        self.frame_color_var.set(config.get('frame_color', '#CCCCCC'))
        self.frame_thickness_var.set(str(config.get('frame_thickness', 2)))
        self.frame_padding_var.set(str(config.get('frame_padding', 10)))
        
        # FCPXML settings
        fcpxml_file_path = config.get('fcpxml_file_path', '')
        self.fcpxml_file_var.set(fcpxml_file_path)
        
        # New FCPXML setting for interval positions
        self.fcpxml_use_interval_positions_var.set(config.get('fcpxml_use_interval_positions', True))
        
        # UI state settings
        self.basic_settings_expanded.set(config.get('basic_settings_expanded', False))
        # Update the UI based on the expanded state
        if self.basic_settings_expanded.get():
            self.basic_settings_content_frame.grid()
            self.basic_settings_toggle_btn.configure(text="▼")
        else:
            self.basic_settings_content_frame.grid_remove()
            self.basic_settings_toggle_btn.configure(text="▶")
        
        # Update FCPXML info label based on file presence
        if fcpxml_file_path and os.path.exists(fcpxml_file_path):
            self.fcpxml_info_label.configure(
                text="✅ FCPXML mode active - thumbnails will be generated from FCPXML references",
                text_color="green"
            )
        else:
            self.fcpxml_info_label.configure(
                text="ℹ️ When FCPXML file is provided, videos will be sourced from FCPXML references",
                text_color="gray"
            )
        
        # Update color button displays
        self.update_color_button('text', self.text_color_var.get())
        self.update_color_button('background', self.bg_color_var.get())
        self.update_color_button('frame', self.frame_color_var.get())
        
        # Update opacity labels
        self.update_opacity_label('text', self.text_opacity_var.get())
        self.update_opacity_label('bg', self.bg_opacity_var.get())
        
        # Update frame settings visibility
        self.toggle_frame_settings()
    
    def save_configuration(self):
        """Save current UI settings to configuration."""
        try:
            # Validate all inputs first
            if not self.validate_all_inputs():
                return False
            
            # Get current values
            config_updates = {
                'source_folders': self.get_current_folders(),
                'thumbnail_width': int(self.thumbnail_width_var.get()),
                'clips_per_row': int(self.clips_per_row_var.get()),
                'positions': self.positions_var.get().strip(),
                'padding': int(self.padding_var.get()),
                'max_rows_per_image': int(self.max_rows_var.get()),
                'output_path': self.output_path_var.get().strip(),
                'font_size': int(self.font_size_var.get()),
                'overlay_position': self.overlay_position_var.get(),
                'text_color': self.text_color_var.get(),
                'overlay_background_color': self.bg_color_var.get(),
                'overlay_opacity': float(self.text_opacity_var.get()),
                'overlay_background_opacity': float(self.bg_opacity_var.get()),
                'show_frame': self.show_frame_var.get(),
                'frame_color': self.frame_color_var.get(),
                'frame_thickness': int(self.frame_thickness_var.get()),
                'frame_padding': int(self.frame_padding_var.get()),
                # FCPXML settings
                'fcpxml_file_path': self.fcpxml_file_var.get().strip(),
                'fcpxml_use_interval_positions': self.fcpxml_use_interval_positions_var.get(),
                # UI state settings
                'basic_settings_expanded': self.basic_settings_expanded.get()
            }
            
            # Update output format based on file extension
            output_path = config_updates['output_path']
            if self.format_var.get() == 'PNG':
                if not output_path.lower().endswith('.png'):
                    output_path = str(Path(output_path).with_suffix('.png'))
            else:
                if not output_path.lower().endswith(('.jpg', '.jpeg')):
                    output_path = str(Path(output_path).with_suffix('.jpg'))
            
            config_updates['output_path'] = output_path
            self.output_path_var.set(output_path)
            
            # Save to config manager
            success = self.config_manager.update_config(config_updates)
            
            if success:
                self.log_message("Configuration saved successfully")
                return True
            else:
                self.log_message("Error: Failed to save configuration")
                return False
                
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}")
            return False
    
    def select_folders(self):
        """Open folder selection dialog."""
        try:
            # Use tkinter's askdirectory with multiple selection simulation
            folder = filedialog.askdirectory(
                title="Select Source Folder",
                mustexist=True
            )
            
            if folder:
                current_folders = self.get_current_folders()
                if folder not in current_folders:
                    current_folders.append(folder)
                    self.update_folder_display(current_folders)
                    self.log_message(f"Added folder: {folder}")
                else:
                    self.log_message(f"Folder already selected: {folder}")
                    
        except Exception as e:
            self.log_message(f"Error selecting folder: {e}")
    
    def clear_folders(self):
        """Clear all selected folders."""
        self.folder_list_text.delete("1.0", "end")
        self.log_message("Cleared all source folders")
    
    def browse_fcpxml_file(self):
        """Open FCPXML file selection dialog."""
        try:
            # File types for FCPXML files
            filetypes = [
                ("FCPXML files", "*.fcpxml"),
                ("XML files", "*.xml"),
                ("All files", "*.*")
            ]
            
            # Get the last used FCPXML folder from config, fallback to current directory
            last_fcpxml_folder = self.config_manager.get('last_fcpxml_folder', '')
            if not last_fcpxml_folder or not os.path.exists(last_fcpxml_folder):
                initial_dir = os.getcwd()
            else:
                initial_dir = last_fcpxml_folder
            
            filename = filedialog.askopenfilename(
                title="Select FCPXML File",
                filetypes=filetypes,
                initialdir=initial_dir
            )
            
            if filename:
                self.fcpxml_file_var.set(filename)
                self.log_message(f"Selected FCPXML file: {filename}")
                
                # Save the folder path for next time
                folder_path = os.path.dirname(filename)
                self.config_manager.set('last_fcpxml_folder', folder_path)
                
                # Update info label to show FCPXML mode is active
                self.fcpxml_info_label.configure(
                    text="✅ FCPXML mode active - thumbnails will be generated from FCPXML references",
                    text_color="green"
                )
                
        except Exception as e:
            self.log_message(f"Error selecting FCPXML file: {e}")
    
    def clear_fcpxml_file(self):
        """Clear the selected FCPXML file."""
        self.fcpxml_file_var.set("")
        self.log_message("Cleared FCPXML file")
        
        # Reset info label
        self.fcpxml_info_label.configure(
            text="ℹ️ When FCPXML file is provided, videos will be sourced from FCPXML references",
            text_color="gray"
        )
    
    def get_current_folders(self) -> List[str]:
        """Get list of currently selected folders."""
        folder_text = self.folder_list_text.get("1.0", "end").strip()
        if not folder_text:
            return []
        return [folder.strip() for folder in folder_text.split('\n') if folder.strip()]
    
    def update_folder_display(self, folders: List[str]):
        """Update the folder display textbox."""
        self.folder_list_text.delete("1.0", "end")
        if folders:
            self.folder_list_text.insert("1.0", '\n'.join(folders))
    
    def browse_output_path(self):
        """Open file save dialog for output path."""
        try:
            # Determine file types based on current format
            if self.format_var.get() == 'PNG':
                filetypes = [("PNG files", "*.png"), ("All files", "*.*")]
                default_ext = ".png"
            else:
                filetypes = [("JPEG files", "*.jpg;*.jpeg"), ("All files", "*.*")]
                default_ext = ".jpg"
            
            filename = filedialog.asksaveasfilename(
                title="Save Output As",
                defaultextension=default_ext,
                filetypes=filetypes,
                initialfile=os.path.basename(self.output_path_var.get())
            )
            
            if filename:
                self.output_path_var.set(filename)
                self.log_message(f"Output path set to: {filename}")
                
        except Exception as e:
            self.log_message(f"Error selecting output path: {e}")
    
    def choose_color(self, color_type: str):
        """Open color picker dialog."""
        try:
            if color_type == "text":
                current_color = self.text_color_var.get()
                title = "Choose Text Color"
            elif color_type == "background":
                current_color = self.bg_color_var.get()
                title = "Choose Background Color"
            elif color_type == "frame":
                current_color = self.frame_color_var.get()
                title = "Choose Frame Color"
            else:
                return
            
            # Convert color name to hex if needed
            if current_color.lower() == "black":
                initial_color = "#000000"
            elif current_color.lower() == "white":
                initial_color = "#FFFFFF"
            elif current_color.startswith("#"):
                initial_color = current_color
            else:
                initial_color = "#000000"
            
            color = colorchooser.askcolor(
                title=title,
                color=initial_color
            )
            
            if color[1]:  # color[1] is the hex value
                hex_color = color[1].upper()
                
                if color_type == "text":
                    self.text_color_var.set(hex_color)
                elif color_type == "background":
                    self.bg_color_var.set(hex_color)
                elif color_type == "frame":
                    self.frame_color_var.set(hex_color)
                
                self.update_color_button(color_type, hex_color)
                self.log_message(f"Updated {color_type} color to: {hex_color}")
                
        except Exception as e:
            self.log_message(f"Error choosing {color_type} color: {e}")
    
    def update_color_button(self, color_type: str, hex_color: str):
        """Update color button display."""
        try:
            # Determine button and display text
            if color_type == "text":
                button = self.text_color_btn
            elif color_type == "background":
                button = self.bg_color_btn
            elif color_type == "frame":
                button = self.frame_color_btn
            else:
                return
            
            # Update button text
            if hex_color.upper() == "#000000":
                display_text = "⬛ Black"
            elif hex_color.upper() == "#FFFFFF":
                display_text = "⬜ White"
            else:
                display_text = f"🟪 {hex_color}"
            
            button.configure(text=display_text)
            
        except Exception as e:
            self.log_message(f"Error updating color button: {e}")
    
    def update_opacity_label(self, opacity_type: str, value: float):
        """Update opacity percentage label."""
        try:
            percentage = int(value * 100)
            
            if opacity_type == "text":
                self.text_opacity_label.configure(text=f"{percentage}%")
            elif opacity_type == "bg":
                self.bg_opacity_label.configure(text=f"{percentage}%")
                
        except Exception as e:
            self.log_message(f"Error updating opacity label: {e}")
    
    def toggle_frame_settings(self):
        """Toggle frame settings visibility based on checkbox."""
        if self.show_frame_var.get():
            # Enable frame settings
            for widget in self.frame_settings_frame.winfo_children():
                self._enable_widget_recursive(widget)
        else:
            # Disable frame settings
            for widget in self.frame_settings_frame.winfo_children():
                self._disable_widget_recursive(widget)
    
    def toggle_text_overlay_section(self):
        """Toggle text overlay section expand/collapse."""
        if self.text_overlay_expanded.get():
            # Currently expanded, collapse it
            self.text_overlay_content_frame.grid_remove()
            self.text_overlay_toggle_btn.configure(text="▶")
            self.text_overlay_expanded.set(False)
        else:
            # Currently collapsed, expand it
            self.text_overlay_content_frame.grid()
            self.text_overlay_toggle_btn.configure(text="▼")
            self.text_overlay_expanded.set(True)
    
    def toggle_frame_settings_section(self):
        """Toggle frame settings section expand/collapse."""
        if self.frame_settings_expanded.get():
            # Currently expanded, collapse it
            self.frame_settings_content_frame.grid_remove()
            self.frame_settings_toggle_btn.configure(text="▶")
            self.frame_settings_expanded.set(False)
        else:
            # Currently collapsed, expand it
            self.frame_settings_content_frame.grid()
            self.frame_settings_toggle_btn.configure(text="▼")
            self.frame_settings_expanded.set(True)
    
    def toggle_basic_settings_section(self):
        """Toggle basic settings section expand/collapse."""
        if self.basic_settings_expanded.get():
            # Currently expanded, collapse it
            self.basic_settings_content_frame.grid_remove()
            self.basic_settings_toggle_btn.configure(text="▶")
            self.basic_settings_expanded.set(False)
        else:
            # Currently collapsed, expand it
            self.basic_settings_content_frame.grid()
            self.basic_settings_toggle_btn.configure(text="▼")
            self.basic_settings_expanded.set(True)
    
    def _enable_widget_recursive(self, widget):
        """Recursively enable a widget and its children."""
        try:
            if hasattr(widget, 'configure'):
                if 'state' in widget.configure():
                    widget.configure(state='normal')
            
            for child in widget.winfo_children():
                self._enable_widget_recursive(child)
        except Exception:
            pass
    
    def _disable_widget_recursive(self, widget):
        """Recursively disable a widget and its children."""
        try:
            if hasattr(widget, 'configure'):
                if 'state' in widget.configure():
                    widget.configure(state='disabled')
            
            for child in widget.winfo_children():
                self._disable_widget_recursive(child)
        except Exception:
            pass
    
    # Validation Methods
    def validate_thumbnail_width(self, event=None):
        """Validate thumbnail width input."""
        try:
            value = int(self.thumbnail_width_var.get())
            if not (100 <= value <= 1000):
                raise ValueError("Width must be between 100 and 1000 pixels")
            self._set_valid_style(self.thumbnail_width_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.thumbnail_width_entry)
            return False
    
    def validate_clips_per_row(self, event=None):
        """Validate clips per row input."""
        try:
            value = int(self.clips_per_row_var.get())
            if not (1 <= value <= 10):
                raise ValueError("Clips per row must be between 1 and 10")
            self._set_valid_style(self.clips_per_row_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.clips_per_row_entry)
            return False
    
    def validate_positions(self, event=None):
        """Validate positions input."""
        try:
            positions_str = self.positions_var.get().strip()
            if not positions_str:
                raise ValueError("Positions cannot be empty")
            
            positions = positions_str.split(",")
            if len(positions) < 1:
                raise ValueError("At least one position required")
            
            for pos in positions:
                pos = pos.strip()
                if pos.endswith("%"):
                    percent = float(pos[:-1])
                    if not (0 <= percent <= 100):
                        raise ValueError("Percentage must be between 0 and 100")
                elif pos.endswith("s"):
                    float(pos[:-1])  # Just check if it's a valid number
                else:
                    raise ValueError("Position must end with % or s")
            
            self._set_valid_style(self.positions_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.positions_entry)
            return False
    
    def validate_font_size(self, event=None):
        """Validate font size input."""
        try:
            value = int(self.font_size_var.get())
            if not (8 <= value <= 72):
                raise ValueError("Font size must be between 8 and 72 pixels")
            self._set_valid_style(self.font_size_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.font_size_entry)
            return False
    
    def validate_frame_thickness(self, event=None):
        """Validate frame thickness input."""
        try:
            value = int(self.frame_thickness_var.get())
            if not (1 <= value <= 20):
                raise ValueError("Frame thickness must be between 1 and 20 pixels")
            self._set_valid_style(self.frame_thickness_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.frame_thickness_entry)
            return False
    
    def validate_frame_padding(self, event=None):
        """Validate frame padding input."""
        try:
            value = int(self.frame_padding_var.get())
            if not (0 <= value <= 50):
                raise ValueError("Frame padding must be between 0 and 50 pixels")
            self._set_valid_style(self.frame_padding_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.frame_padding_entry)
            return False
    
    def validate_max_rows(self, event=None):
        """Validate max rows input."""
        try:
            value = int(self.max_rows_var.get())
            if value < 0:
                raise ValueError("Max rows must be 0 or greater")
            self._set_valid_style(self.max_rows_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.max_rows_entry)
            return False
    
    def validate_padding(self, event=None):
        """Validate padding input."""
        try:
            value = int(self.padding_var.get())
            if not (0 <= value <= 50):
                raise ValueError("Padding must be between 0 and 50 pixels")
            self._set_valid_style(self.padding_entry)
            return True
        except ValueError:
            self._set_invalid_style(self.padding_entry)
            return False
    
    def validate_all_inputs(self) -> bool:
        """Validate all input fields."""
        validators = [
            self.validate_thumbnail_width,
            self.validate_clips_per_row,
            self.validate_positions,
            self.validate_font_size,
            self.validate_frame_thickness,
            self.validate_frame_padding,
            self.validate_max_rows,
            self.validate_padding
        ]
        
        all_valid = all(validator() for validator in validators)
        
        # Validate source folders
        folders = self.get_current_folders()
        if not folders:
            self.log_message("Error: No source folders selected")
            all_valid = False
        
        # Validate output path
        output_path = self.output_path_var.get().strip()
        if not output_path:
            self.log_message("Error: Output path cannot be empty")
            all_valid = False
        
        return all_valid
    
    def _set_valid_style(self, widget):
        """Set valid style for input widget."""
        try:
            widget.configure(border_color="green")
        except Exception:
            pass
    
    def _set_invalid_style(self, widget):
        """Set invalid style for input widget."""
        try:
            widget.configure(border_color="red")
        except Exception:
            pass
    
    # Processing Methods
    def start_processing(self):
        """Start the thumbnail generation process."""
        if self.processing:
            self.log_message("Processing already in progress")
            return
        
        # Validate inputs
        if not self.validate_all_inputs():
            messagebox.showerror("Validation Error", 
                               "Please fix input validation errors before processing")
            return
        
        # Save configuration
        if not self.save_configuration():
            messagebox.showerror("Configuration Error", 
                               "Failed to save configuration")
            return
        
        # Set processing state
        self.processing = True
        self.generate_btn.configure(state="disabled", text="Processing...")
        self.progress_var.set(0.0)
        self.status_var.set("Starting...")
        
        # Clear progress and log queues
        while not self.progress_queue.empty():
            self.progress_queue.get()
        while not self.log_queue.empty():
            self.log_queue.get()
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_worker,
            daemon=True
        )
        self.processing_thread.start()
        
        self.log_message("Started thumbnail generation process")
    
    def _processing_worker(self):
        """Worker method for background processing using unified processor."""
        try:
            # Create unified processor
            unified_processor = UnifiedProcessor(self.config_manager)
            
            # Set callbacks for progress and logging
            unified_processor.set_progress_callback(lambda progress, message: self.progress_queue.put((progress, message)))
            unified_processor.set_log_callback(lambda message: self.log_queue.put(message))
            
            # Validate configuration
            is_valid, errors = unified_processor.validate_configuration()
            if not is_valid:
                for error in errors:
                    self.log_queue.put(f"Configuration error: {error}")
                self.progress_queue.put((1.0, "Configuration errors"))
                return
            
            # Process thumbnails using unified workflow
            success = unified_processor.process_thumbnails()
            
            if not success:
                self.progress_queue.put((1.0, "Processing failed"))
            
        except Exception as e:
            self.log_queue.put(f"Error during processing: {e}")
            self.progress_queue.put((1.0, "Error occurred"))
        
        finally:
            # Reset processing state
            self.progress_queue.put((None, None))  # Signal completion
    
    def refresh_preview(self):
        """Refresh the preview file list using the new list component."""
        try:
            # Clear existing items
            for item in self.preview_file_list_items:
                item.destroy()
            self.preview_file_list_items.clear()
            
            # Get output path from config
            config = self.config_manager.load_config()
            output_path = config.get('output_path', 'output/overview.jpg')
            output_dir = Path(output_path).parent
            
            # Check if directory exists
            if not output_dir.exists():
                # Handle missing directory case
                return
            
            # List image files in the directory
            image_extensions = ['.jpg', '.jpeg', '.png']
            image_files = []
            
            for file_path in output_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
            
            # Sort files by modification time (newest first)
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Create list items for each file
            for file_path in image_files:
                item = self.create_file_item(self.preview_file_list_frame, file_path)
                self.preview_file_list_items.append(item)
            
            # Select the first file and show its preview if available
            if image_files:
                self.selected_preview_file = image_files[0]
                self.show_preview_image(image_files[0])
                
        except Exception as e:
            self.log_message(f"Error refreshing preview: {e}")
    
    def show_preview_image(self, file_path):
        """Show preview of the selected image file."""
        try:
            from PIL import Image
            
            # Open the image
            image = Image.open(file_path)
            
            # Get the current size of the preview label to determine available space
            preview_width = self.preview_image_label.winfo_width()
            preview_height = self.preview_image_label.winfo_height()
            
            # If the label size is not yet determined, use a default larger size
            if preview_width <= 1 or preview_height <= 1:
                preview_width = 500
                preview_height = 400
            
            # Resize to fit in the preview area while maintaining aspect ratio
            image.thumbnail((preview_width, preview_height), Image.Resampling.LANCZOS)
            
            # Convert to CTkImage for display
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            
            # Update the preview label to fill the available space
            self.preview_image_label.configure(image=ctk_image, text="")
            
        except Exception as e:
            self.log_message(f"Error showing preview image: {e}")
            self.preview_image_label.configure(image=None, text=f"Error loading image: {e}")
    
    def create_file_item(self, parent, file_path):
        """Create an individual file item frame with filename and modification time."""
        # Create item frame with visual styling
        item_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=6)
        item_frame.grid_columnconfigure(0, weight=1)
        item_frame.grid(sticky="ew", padx=2, pady=1)
        
        # Store file path reference using setattr
        setattr(item_frame, 'file_path', file_path)
        
        # Make the frame clickable
        item_frame.bind("<Button-1>", lambda e: self.on_file_item_click(item_frame))
        item_frame.bind("<Double-Button-1>", lambda e: self.on_file_item_double_click(file_path))
        
        # Filename label
        filename_label = ctk.CTkLabel(item_frame, text=file_path.name, anchor="w")
        filename_label.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        filename_label.bind("<Button-1>", lambda e: self.on_file_item_click(item_frame))
        filename_label.bind("<Double-Button-1>", lambda e: self.on_file_item_double_click(file_path))
        
        # Modification time label
        mod_time = file_path.stat().st_mtime
        from datetime import datetime
        mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        time_label = ctk.CTkLabel(item_frame, text=mod_time_str, text_color="gray70", font=ctk.CTkFont(size=10), anchor="w")
        time_label.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 2))
        time_label.bind("<Button-1>", lambda e: self.on_file_item_click(item_frame))
        time_label.bind("<Double-Button-1>", lambda e: self.on_file_item_double_click(file_path))
        
        # Store label references for styling using setattr
        setattr(item_frame, 'filename_label', filename_label)
        setattr(item_frame, 'time_label', time_label)
        
        return item_frame

    def on_file_item_click(self, item_frame):
        """Handle single click on a file item."""
        # Update visual selection
        if self.selected_file_item:
            try:
                self.selected_file_item.configure(fg_color="transparent")
                # Also reset label colors
                filename_label = getattr(self.selected_file_item, 'filename_label', None)
                time_label = getattr(self.selected_file_item, 'time_label', None)
                if filename_label:
                    filename_label.configure(text_color="white" if ctk.get_appearance_mode() == "Dark" else "black")
                if time_label:
                    time_label.configure(text_color="gray70")
            except tk.TclError:
                # Widget may have been destroyed, clear the reference
                self.selected_file_item = None
        
        try:
            # Highlight the selected item with a more visible color
            item_frame.configure(fg_color=("#3a7ebf", "#1f538d"))  # Blue color for selection
            self.selected_file_item = item_frame
            
            # Also highlight the text labels
            filename_label = getattr(item_frame, 'filename_label', None)
            time_label = getattr(item_frame, 'time_label', None)
            if filename_label:
                filename_label.configure(text_color="white")
            if time_label:
                time_label.configure(text_color="lightgray")
            
            # Update preview
            file_path = getattr(item_frame, 'file_path', None)
            if file_path:
                self.selected_preview_file = file_path
                self.show_preview_image(file_path)
        except tk.TclError:
            # Widget may have been destroyed
            self.selected_file_item = None
            self.selected_preview_file = None

    def on_file_item_double_click(self, file_path):
        """Handle double click on a file item to open in default viewer."""
        try:
            import subprocess
            import platform
            
            # Open file with default application based on OS
            system = platform.system()
            if system == "Windows":
                subprocess.run(["start", str(file_path)], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)])
            else:  # Linux and others
                subprocess.run(["xdg-open", str(file_path)])
        except Exception as e:
            self.log_message(f"Error opening file: {e}")
            messagebox.showerror("Error", f"Could not open file: {e}")

    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete("1.0", "end")
    
    def log_message(self, message: str):
        """Add a message to the log."""
        try:
            # Get current time
            timestamp = threading.current_thread().name
            if timestamp == "MainThread":
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {message}\n"
                
                # Insert at end
                self.log_text.insert("end", formatted_message)
                
                # Auto-scroll to bottom
                self.log_text.see("end")
            else:
                # From background thread - use queue
                self.log_queue.put(message)
                
        except Exception as e:
            print(f"Error logging message: {e}")
    
    def monitor_queues(self):
        """Monitor progress and log queues for updates from background thread."""
        try:
            # Check progress queue
            try:
                while True:
                    progress, status = self.progress_queue.get_nowait()
                    if progress is None:  # Completion signal
                        self.processing = False
                        self.generate_btn.configure(state="normal", text="Generate Overview")
                        # Refresh preview when processing is complete
                        self.refresh_preview()
                        break
                    else:
                        self.progress_var.set(progress)
                        if status:
                            self.status_var.set(status)
            except queue.Empty:
                pass
            
            # Check log queue
            try:
                while True:
                    message = self.log_queue.get_nowait()
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    formatted_message = f"[{timestamp}] {message}\n"
                    
                    self.log_text.insert("end", formatted_message)
                    self.log_text.see("end")
            except queue.Empty:
                pass
                
        except Exception as e:
            print(f"Error monitoring queues: {e}")
        
        # Schedule next check
        self.root.after(100, self.monitor_queues)
    
    def on_closing(self):
        """Handle application closing."""
        if self.processing:
            if messagebox.askokcancel("Quit", "Processing is in progress. Do you want to quit?"):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the GUI application."""
        try:
            self.log_message("GUI Application started")
            self.root.mainloop()
        except Exception as e:
            print(f"Error running GUI: {e}")


def main():
    """Main function to run the GUI application."""
    try:
        app = GUIApplication()
        app.run()
    except Exception as e:
        print(f"Error starting GUI application: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())