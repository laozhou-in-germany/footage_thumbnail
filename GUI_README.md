# GUI Implementation - Footage Thumbnailer

This document describes the GUI implementation for the Footage Thumbnailer application.

## Overview

The GUI application provides a modern, user-friendly interface built with CustomTkinter framework. It offers complete feature parity with the CLI version while adding intuitive visual controls and real-time feedback.

## Features

### Source Folder Management
- **Multi-select folder dialog**: Select multiple source directories
- **Visual folder list**: Display selected folders in a scrollable text area
- **Clear all functionality**: Remove all selected folders with one click
- **Persistent storage**: Folder selections are saved in configuration

### Timeline File Management
- **FCPXML file selection**: Optional FCPXML timeline file for sequence-based processing
- **Visual file path display**: Show selected FCPXML file
- **Clear file functionality**: Remove selected FCPXML file
- **File dialog integration**: Native file browser for FCPXML selection

### Basic Settings
- **Thumbnail Width**: Input with validation (100-1000 pixels)
- **Clips Per Row**: Grid layout control (1-10 clips)
- **Thumbnail Positions**: Frame extraction points (percentages or time)
- **Output Format**: JPEG or PNG selection
- **Max Rows Per Image**: Multi-page output control
- **Padding**: Spacing between thumbnails

### Text & Overlay Settings
- **Font Size**: Customizable text size with validation
- **Overlay Position**: Choose between "Above Thumbnails" or "On Thumbnails"
- **Color Pickers**: Interactive color selection for text and background
- **Opacity Sliders**: Real-time opacity adjustment for overlays
- **Visual Preview**: Color buttons show current selections

### Frame Settings
- **Enable/Disable**: Toggle frame borders around video groups
- **Frame Color**: Customizable border color with color picker
- **Frame Thickness**: Adjustable border width (1-20 pixels)
- **Frame Padding**: Internal spacing within frames

### Output Management
- **Output Path**: File path input with validation
- **Browse Dialog**: Native "Save As" dialog integration
- **Format Auto-detection**: Automatically sets format based on file extension

### Processing Controls
- **Generate Button**: Large, prominent action button
- **Progress Bar**: Real-time processing progress indicator
- **Status Display**: Current processing stage information
- **Background Processing**: Non-blocking thumbnail generation

### Logging System
- **Scrollable Log**: Real-time processing updates with timestamps
- **Auto-scroll**: Automatically shows latest entries
- **Clear Log**: Reset log for new operations
- **Detailed Feedback**: Comprehensive processing information

## Technical Implementation

### Architecture
```
GUIApplication
├── ConfigManager Integration
├── Core Engine Components
│   ├── VideoScanner
│   ├── ThumbnailExtractor
│   ├── ImageComposer
│   └── FCPXMLParser
├── UI Components
│   ├── Source Folders Frame
│   ├── Timeline File Frame
│   ├── Basic Settings Frame
│   ├── Text & Overlay Frame
│   ├── Frame Settings Frame
│   ├── Output Frame
│   ├── Processing Frame
│   └── Log Frame
└── Background Processing
    ├── Threading
    ├── Progress Updates
    └── Error Handling
```

### Key Classes

#### GUIApplication
Main application class that orchestrates all GUI components and integrates with the core engine.

**Key Methods:**
- `__init__()`: Initialize GUI components and core modules
- `create_ui_components()`: Build all UI sections
- `load_configuration()`: Populate UI from saved settings
- `save_configuration()`: Persist UI settings to config file
- `start_processing()`: Begin thumbnail generation in background
- `validate_all_inputs()`: Comprehensive input validation

#### Background Processing
Uses Python threading to maintain UI responsiveness during video processing.

**Features:**
- Queue-based progress updates
- Thread-safe logging
- Graceful error handling
- Processing completion signals

### Input Validation

#### Real-time Validation
- **Field-level validation**: Immediate feedback on input changes
- **Visual indicators**: Border colors indicate validation status
- **Range checking**: Numeric inputs validated against acceptable ranges
- **Format validation**: Positions and colors checked for correct format

#### Validation Rules
| Field | Rules |
|-------|-------|
| Thumbnail Width | 100-1000 pixels |
| Clips Per Row | 1-10 clips |
| Font Size | 8-72 pixels |
| Frame Thickness | 1-20 pixels |
| Frame Padding | 0-50 pixels |
| Positions | Valid percentage (0-100%) or time (Ns) format |
| Colors | Valid hex color codes |
| FCPXML File | Valid .fcpxml file extension

### Configuration Integration

The GUI seamlessly integrates with the existing configuration system:

1. **Startup**: Load saved settings and populate UI fields
2. **Runtime**: Real-time validation and UI updates
3. **Save**: Persist all changes to config.json
4. **Processing**: Use saved configuration for thumbnail generation

### Error Handling

#### User-Friendly Error Messages
- Input validation errors shown immediately
- Processing errors logged with context
- Network/file access issues handled gracefully
- Recovery suggestions provided where applicable

#### Graceful Degradation
- Missing dependencies detected and reported
- Invalid configurations reset to defaults
- Corrupted files skipped with warnings
- Processing continues despite individual file failures

## Usage

### Starting the GUI
```bash
# Launch GUI mode
python src/main.py --gui

# Or use the gui command
python src/main.py gui
```

### Typical Workflow
1. **Select Folders**: Click "Select Folders..." to choose source directories
2. **Optional FCPXML**: Select an FCPXML file for timeline-based processing
3. **Configure Settings**: Adjust thumbnail width, layout, and visual options
4. **Set Output**: Choose destination file path and format
5. **Generate**: Click "Generate Overview" to start processing
6. **Monitor Progress**: Watch real-time progress and log updates
7. **Review Results**: Check completion status and output location

### Timeline Processing Mode

When an FCPXML file is selected, the application will:
1. Parse the FCPXML timeline to extract video references
2. Match timeline entries with actual video files in selected folders
3. Generate thumbnails based on timeline positions
4. Create contact sheets following the timeline sequence

### Advanced Features

#### Multi-Page Output
When enabled (Max Rows > 0), large video collections are automatically split into multiple manageable images:
- Sequential file naming (e.g., overview_page02.jpg)
- Consistent layout across pages
- Progress tracking for each page

#### Frame Visual Grouping
Frame borders help identify which thumbnails belong to each video:
- Customizable colors and thickness
- Internal padding for better separation
- Enable/disable per user preference

#### Overlay Positioning
Two overlay modes for different use cases:
- **Above Thumbnails**: Clean header with metadata
- **On Thumbnails**: Traditional overlay text on images

#### FCPXML Placeholder Handling
When video files referenced in the FCPXML timeline are not found:
- Generate placeholder thumbnails with clear labeling
- Customizable placeholder background color
- Configurable similarity threshold for fuzzy matching

## Testing

### Unit Tests
- Input validation logic
- Configuration integration
- Core component interaction
- Error handling scenarios

### Integration Tests
- Complete workflow testing
- Configuration persistence
- Multi-component interaction
- Performance with large datasets

### Run Tests
```bash
# GUI integration tests
python -m pytest tests/test_gui_integration.py -v

# All tests
python -m pytest tests/ -v
```

## Dependencies

### Required
- **CustomTkinter**: Modern GUI framework
- **Pillow**: Image processing
- **FFmpeg**: Video frame extraction

### Installation
```bash
pip install -r requirements.txt
```

## Future Enhancements

### Planned Features
- **Batch Processing**: Multiple output configurations
- **Template System**: Save/load processing templates
- **Preview Mode**: Quick thumbnail preview before full generation
- **Drag & Drop**: Direct folder selection via drag and drop
- **Progress Cancellation**: Cancel long-running operations
- **Timeline Visualization**: Visual representation of FCPXML timeline

### Performance Optimizations
- **Lazy Loading**: Load UI components on demand
- **Background Validation**: Validate inputs without blocking UI
- **Memory Management**: Efficient handling of large video collections
- **Caching**: Cache processed thumbnails for quick regeneration

## Troubleshooting

### Common Issues

#### GUI Won't Start
```
Error: GUI dependencies not available
```
**Solution**: Install CustomTkinter: `pip install customtkinter`

#### Processing Errors
```
Error processing video_file.mp4: [Errno 2] No such file or directory
```
**Solution**: Ensure FFmpeg is installed and accessible in PATH

#### FCPXML File Issues
```
Error: Invalid FCPXML file format
```
**Solution**: Verify the file is a valid Final Cut Pro XML export

#### Performance Issues
- **Large Collections**: Use Max Rows setting to create multiple pages
- **High Resolution**: Reduce thumbnail width for faster processing
- **Memory Usage**: Close other applications during processing

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
python src/main.py --gui --verbose
```

## Support

For issues, feature requests, or contributions, please refer to the main project documentation.