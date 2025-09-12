"""
Configuration manager for the Footage Thumbnailer application.

This module handles loading, validation, and saving of configuration settings
from JSON files with support for default values and runtime overrides.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class ConfigManager:
    """Manages application configuration with JSON file persistence."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
        """
        if config_path is None:
            # Default config path in the src directory
            self.config_path = Path(__file__).parent.parent / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self._config = {}
        self._load_or_create_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration settings.
        
        Returns:
            Dictionary containing default configuration values.
        """
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
            "max_rows_per_image": 0,  # 0 = unlimited (single image)
            # FCPXML-specific settings
            "fcpxml_file_path": "",
            "fcpxml_show_placeholders": True,
            "fcpxml_use_interval_positions": True,
            "fcpxml_placeholder_color": "#F0F0F0",
            "fcpxml_similarity_threshold": 0.6,
            # UI state settings
            "basic_settings_expanded": False,
            "last_fcpxml_folder": ""
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration values.
        
        Args:
            config: Configuration dictionary to validate.
            
        Returns:
            True if configuration is valid, False otherwise.
        """
        try:
            # Validate required fields exist
            required_fields = [
                "source_folders", "output_path", "thumbnail_width", 
                "clips_per_row", "positions", "padding", "supported_extensions"
            ]
            
            for field in required_fields:
                if field not in config:
                    return False
            
            # Validate data types and ranges
            if not isinstance(config["source_folders"], list):
                return False
            
            if not isinstance(config["output_path"], str):
                return False
            
            if not isinstance(config["thumbnail_width"], int) or not (100 <= config["thumbnail_width"] <= 1000):
                return False
            
            if not isinstance(config["clips_per_row"], int) or not (1 <= config["clips_per_row"] <= 10):
                return False
            
            if not isinstance(config["positions"], str):
                return False
            
            if not isinstance(config["padding"], int) or config["padding"] < 0:
                return False
            
            if not isinstance(config["supported_extensions"], list):
                return False
            
            # Validate FCPXML-specific settings if present
            if "fcpxml_file_path" in config and not isinstance(config["fcpxml_file_path"], str):
                return False
            
            if "fcpxml_show_placeholders" in config and not isinstance(config["fcpxml_show_placeholders"], bool):
                return False
            
            # Validate FCPXML setting
            if "fcpxml_use_interval_positions" in config and not isinstance(config["fcpxml_use_interval_positions"], bool):
                return False
            
            if "fcpxml_similarity_threshold" in config:
                threshold = config["fcpxml_similarity_threshold"]
                if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                    return False
            
            # Validate positions format
            positions = config["positions"].split(",")
            for pos in positions:
                pos = pos.strip()
                if pos.endswith("%"):
                    try:
                        percent = float(pos[:-1])
                        if not (0 <= percent <= 100):
                            return False
                    except ValueError:
                        return False
                elif pos.endswith("s"):
                    try:
                        float(pos[:-1])
                    except ValueError:
                        return False
                else:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _load_or_create_config(self) -> None:
        """Load configuration from file or create default if it doesn't exist."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                if self._validate_config(loaded_config):
                    # Merge with defaults to ensure all required fields exist
                    default_config = self._get_default_config()
                    default_config.update(loaded_config)
                    self._config = default_config
                else:
                    print(f"Warning: Invalid configuration in {self.config_path}. Using defaults.")
                    self._config = self._get_default_config()
                    self.save_config()
            else:
                # Create default configuration
                self._config = self._get_default_config()
                self.save_config()
                
        except Exception as e:
            print(f"Error loading configuration: {e}. Using defaults.")
            self._config = self._get_default_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Dictionary containing current configuration values.
        """
        return self._config.copy()
    
    def is_timeline_mode(self) -> bool:
        """
        Check if timeline mode is enabled based on configuration.
        
        Returns:
            True if timeline file is specified and exists, False otherwise.
        """
        fcpxml_path = self._config.get('fcpxml_file_path', '')
        if not fcpxml_path:
            return False
        
        return os.path.exists(fcpxml_path) and os.path.isfile(fcpxml_path)
    
    def get_timeline_config(self) -> Dict[str, Any]:
        """
        Get timeline-specific configuration settings.
        
        Returns:
            Dictionary containing timeline configuration values.
        """
        return {
            'fcpxml_file_path': self._config.get('fcpxml_file_path', ''),
            'fcpxml_show_placeholders': self._config.get('fcpxml_show_placeholders', True),
            'fcpxml_use_interval_positions': self._config.get('fcpxml_use_interval_positions', True),
            'fcpxml_placeholder_color': self._config.get('fcpxml_placeholder_color', '#F0F0F0'),
            'fcpxml_similarity_threshold': self._config.get('fcpxml_similarity_threshold', 0.6)
        }
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save. If None, saves current config.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            config_to_save = config if config is not None else self._config
            
            if not self._validate_config(config_to_save):
                print("Error: Invalid configuration. Cannot save.")
                return False
            
            # Ensure the directory exists
            os.makedirs(self.config_path.parent, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            if config is not None:
                self._config = config.copy()
            
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def set_fcpxml_file(self, fcpxml_file_path: str) -> bool:
        """
        Set the timeline file path in configuration.
        
        Args:
            timeline_file_path: Path to the timeline file.
            
        Returns:
            True if successfully set, False otherwise.
        """
        if fcpxml_file_path and not os.path.exists(fcpxml_file_path):
            print(f"Warning: FCPXML file does not exist: {fcpxml_file_path}")
        
        return self.update_config({'fcpxml_file_path': fcpxml_file_path})
    
    def clear_fcpxml_file(self) -> bool:
        """
        Clear the timeline file path from configuration.
        
        Returns:
            True if successfully cleared, False otherwise.
        """
        return self.update_config({'fcpxml_file_path': ''})
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update specific configuration values.
        
        Args:
            updates: Dictionary containing configuration updates.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        try:
            updated_config = self._config.copy()
            updated_config.update(updates)
            
            if self._validate_config(updated_config):
                self._config = updated_config
                return self.save_config()
            else:
                print("Error: Invalid configuration update.")
                return False
                
        except Exception as e:
            print(f"Error updating configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value if key doesn't exist.
            
        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a specific configuration value.
        
        Args:
            key: Configuration key to set.
            value: Value to set.
            
        Returns:
            True if set successfully, False otherwise.
        """
        return self.update_config({key: value})
    
    def get_source_folders(self) -> List[str]:
        """Get the list of source folders."""
        return self._config.get("source_folders", [])
    
    def add_source_folder(self, folder_path: str) -> bool:
        """
        Add a source folder to the configuration.
        
        Args:
            folder_path: Path to the folder to add.
            
        Returns:
            True if added successfully, False otherwise.
        """
        folders = self.get_source_folders()
        if folder_path not in folders:
            folders.append(folder_path)
            return self.set("source_folders", folders)
        return True
    
    def remove_source_folder(self, folder_path: str) -> bool:
        """
        Remove a source folder from the configuration.
        
        Args:
            folder_path: Path to the folder to remove.
            
        Returns:
            True if removed successfully, False otherwise.
        """
        folders = self.get_source_folders()
        if folder_path in folders:
            folders.remove(folder_path)
            return self.set("source_folders", folders)
        return True
    
    def clear_source_folders(self) -> bool:
        """
        Clear all source folders from the configuration.
        
        Returns:
            True if cleared successfully, False otherwise.
        """
        return self.set("source_folders", [])
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value if key doesn't exist.
            
        Returns:
            Configuration value or default.
        """
        return self._config[key] if key in self._config else default
    
    def validate_fcpxml_config(self) -> Tuple[bool, List[str]]:
        """
        Validate FCPXML-specific configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []
        timeline_config = self.get_timeline_config()
        
        # Check FCPXML file path
        fcpxml_path = timeline_config['fcpxml_file_path']
        if fcpxml_path:
            if not os.path.exists(fcpxml_path):
                errors.append(f"FCPXML file does not exist: {fcpxml_path}")
            elif not os.path.isfile(fcpxml_path):
                errors.append(f"FCPXML path is not a file: {fcpxml_path}")
            else:
                # Validate file extension
                file_extension = Path(fcpxml_path).suffix.lower()
                if file_extension not in ['.fcpxml']:
                    errors.append(f"Unsupported file format: {file_extension}. Supported formats: .fcpxml")
        
        # Check similarity threshold
        threshold = timeline_config['fcpxml_similarity_threshold']
        if not (0.0 <= threshold <= 1.0):
            errors.append(f"FCPXML similarity threshold must be between 0.0 and 1.0, got: {threshold}")
        
        return len(errors) == 0, errors
    
    def export_config_template(self, output_path: str, include_fcpxml: bool = True) -> bool:
        """
        Export a configuration template with comments.
        
        Args:
            output_path: Path to save the template.
            include_fcpxml: Whether to include FCPXML-specific settings.
            
        Returns:
            True if export was successful, False otherwise.
        """
        try:
            template_config = self._get_default_config()
            
            if not include_fcpxml:
                # Remove FCPXML-specific keys
                fcpxml_keys = ['fcpxml_file_path', 'fcpxml_show_placeholders', 
                              'fcpxml_use_interval_positions', 'fcpxml_placeholder_color', 
                              'fcpxml_similarity_threshold']
                for key in fcpxml_keys:
                    template_config.pop(key, None)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template_config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting config template: {e}")
            return False