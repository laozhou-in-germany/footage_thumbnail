# Footage Thumbnailer

A Python-based desktop application for generating visual contact sheets from video collections. The application scans directories for video files, extracts thumbnails at specified time positions, and creates organized contact sheets with metadata overlays.

## Features

- **Recursive Video Scanning**: Automatically discovers video files in directories and subdirectories
- **Multiple Thumbnail Positions**: Extract frames at percentage-based or time-based positions
- **Metadata Overlays**: Display filename, creation date, duration, and timestamps
- **Flexible Grid Layout**: Configurable grid arrangement with customizable spacing
- **Multi-Page Support**: Automatically split large collections into multiple manageable images
- **Visual Frame Borders**: Clear grouping of thumbnails belonging to each video
- **Multiple Video Formats**: Support for MP4, MOV, AVI, MKV, MTS, and more
- **Command-Line Interface**: Full CLI support with argument overrides
- **JSON Configuration**: Easy-to-edit configuration file for persistent settings
- **FCPXML Timeline Support**: Generate thumbnails based on Final Cut Pro XML timeline sequences

## Installation

### Prerequisites

- Python 3.9 or higher
- FFmpeg (for video processing)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install from Source

```bash
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Run with default settings (scans folders from config.json)
python src/main.py

# Specify source folders
python src/main.py --folders "C:/Videos" "D:/Footage"

# Customize output
python src/main.py --output "my_contact_sheet.jpg" --width 400
```

### FCPXML Timeline Mode

```bash
# Process videos based on FCPXML timeline
python src/main.py --folders "C:/Videos" --fcpxml "timeline.fcpxml"

# Customize FCPXML processing
python src/main.py --folders "C:/Videos" --fcpxml "timeline.fcpxml" --positions "0%,50%,99%"
```

### Configuration

The application uses a `config.json` file for default settings:

```json
{
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
  "show_frame": true,
  "frame_color": "#CCCCCC",
  "frame_thickness": 2,
  "frame_padding": 10,
  "max_rows_per_image": 0,
  "fcpxml_file_path": "",
  "fcpxml_show_placeholders": true,
  "fcpxml_use_interval_positions": true,
  "fcpxml_placeholder_color": "#F0F0F0",
  "fcpxml_similarity_threshold": 0.6
}
```

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--folders` | Source folder paths | `--folders "C:/Videos" "D:/Footage"` |
| `--output` | Output file path | `--output "contact_sheet.jpg"` |
| `--width` | Thumbnail width (100-1000px) | `--width 400` |
| `--rows` | Clips per row (1-10) | `--rows 3` |
| `--positions` | Thumbnail positions | `--positions "0%,25%,50%,75%,99%"` |
| `--config` | Custom config file | `--config "my_config.json"` |
| `--no-recursive` | Don't scan subdirectories | `--no-recursive` |
| `--overlay-position` | Text overlay position | `--overlay-position above_thumbnails` |
| `--no-frame` | Disable frame borders | `--no-frame` |
| `--frame-color` | Frame border color | `--frame-color black` |
| `--max-rows` | Maximum rows per image | `--max-rows 3` |
| `--dry-run` | Preview without processing | `--dry-run` |
| `--verbose` | Enable detailed output | `--verbose` |
| `--fcpxml` | FCPXML timeline file path | `--fcpxml "timeline.fcpxml"` |

## Position Formats

Thumbnail positions can be specified in multiple formats:

- **Percentage**: `"0%,50%,99%"` - Extract at start, middle, and near end
- **Absolute Time**: `"30s,1m30s,2m45s"` - Extract at specific timestamps
- **Mixed Format**: `"0%,30s,99%"` - Combine percentage and time-based positions

## Examples

### Basic Contact Sheet

```bash
python src/main.py --folders "C:/MyVideos" --output "overview.jpg"
```

### High-Quality Thumbnails

```bash
python src/main.py --folders "C:/Videos" --width 500 --rows 3 --output "hq_overview.jpg"
```

### Custom Positions

```bash
python src/main.py --folders "C:/Videos" --positions "0%,10%,25%,50%,75%,90%,99%"
```

### Dry Run Preview

```bash
python src/main.py --folders "C:/Videos" --dry-run --verbose
```

### Text Above Thumbnails

```bash
python src/main.py --folders "C:/Videos" --overlay-position above_thumbnails
```

### Custom Frame Colors

```bash
python src/main.py --folders "C:/Videos" --frame-color black
```

### Disable Frames

```bash
python src/main.py --folders "C:/Videos" --no-frame
```

### Multi-Page Output

```bash
# Split into pages with maximum 3 rows each
python src/main.py --folders "C:/Videos" --max-rows 3

# Create multiple pages when many videos
python src/main.py --folders "C:/Videos" --max-rows 2 --rows 4
```

### FCPXML Timeline Processing

```bash
# Process based on FCPXML timeline
python src/main.py --folders "C:/Videos" --fcpxml "my_timeline.fcpxml"

# FCPXML with custom positions
python src/main.py --folders "C:/Videos" --fcpxml "my_timeline.fcpxml" --positions "0%,25%,50%,75%,99%"

# FCPXML with interval-based positioning
python src/main.py --folders "C:/Videos" --fcpxml "my_timeline.fcpxml" --use-interval-positions
```

## Project Structure

```
footage_thumbnailer/
├── src/
│   ├── core/
│   │   ├── config_manager.py      # Configuration handling
│   │   ├── video_scanner.py       # File discovery and validation
│   │   ├── thumbnail_extractor.py # Frame extraction and metadata
│   │   ├── image_composer.py      # Contact sheet generation
│   │   └── fcpxml_parser.py       # FCPXML timeline parsing
│   ├── cli/
│   │   └── cli_interface.py       # Command-line interface
│   ├── utils/
│   │   ├── file_utils.py          # File system utilities
│   │   └── image_utils.py         # Image processing helpers
│   ├── config.json                # Default configuration
│   └── main.py                    # Application entry point
├── tests/
├── requirements.txt
├── setup.py
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_config_manager

# Run with verbose output
python -m unittest discover tests -v
```

### Code Structure

The application follows a modular architecture with clear separation of concerns:

- **Core Components**: Video processing, thumbnail extraction, image composition
- **CLI Interface**: Command-line argument parsing and execution logic
- **Utilities**: Reusable file system and image processing functions
- **Configuration**: JSON-based configuration management with validation
- **FCPXML Support**: Timeline-based processing using Final Cut Pro XML files

### Adding New Features

1. **New Video Formats**: Add extensions to `supported_extensions` in config
2. **Custom Overlays**: Extend the `ImageComposer` class with new overlay types
3. **New Position Formats**: Extend `parse_time_position()` in `ThumbnailExtractor`

## Troubleshooting

### Common Issues

**Missing Metadata**
- Some video files may not contain creation timestamps
- The system gracefully handles missing metadata by using file modification time

**Thumbnail Extraction Failures**
- Ensure FFmpeg is properly installed and accessible
- Check that video files are not corrupted or in use by other applications

**Large File Processing**
- Processing time scales with video file size and number of positions
- Use `--dry-run` to estimate processing time before actual execution

**Memory Usage**
- For large collections, consider processing in smaller batches
- Reduce thumbnail width or number of positions to decrease memory usage

### Error Messages

- **"No accessible video files found"**: Check folder paths and file permissions
- **"Failed to extract video metadata"**: Verify FFmpeg installation
- **"Invalid configuration"**: Check config.json syntax and value ranges
- **"FCPXML file not found"**: Verify FCPXML file path and accessibility

## Performance Tips

1. **Optimize Thumbnail Width**: Balance quality vs. processing time (320px recommended)
2. **Limit Positions**: More positions = longer processing time
3. **Use SSD Storage**: Faster disk I/O significantly improves performance
4. **Batch Processing**: Process related videos together for better efficiency

## Requirements

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Python**: 3.9 or higher

### Python Dependencies

- `opencv-python>=4.8.0` - Video frame extraction
- `ffmpeg-python>=0.2.0` - Video metadata and processing
- `Pillow>=10.0.0` - Image composition and manipulation
- `customtkinter>=5.2.0` - GUI framework (future GUI implementation)

## License

This project is released under the MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m unittest discover tests`
4. Make your changes and ensure tests pass
5. Submit a pull request

## Roadmap

### Phase 1 (Current) - CLI Implementation
- [x] Core video processing engine
- [x] Command-line interface
- [x] Configuration management
- [x] Unit tests
- [x] FCPXML timeline support

### Phase 2 (Planned) - GUI Implementation
- [ ] CustomTkinter-based GUI
- [ ] Real-time progress tracking
- [ ] Drag-and-drop folder selection
- [ ] Live preview capabilities
- [ ] FCPXML file selection and processing

### Phase 3 (Future) - Advanced Features
- [ ] Parallel processing for large collections
- [ ] Custom overlay templates
- [ ] Video preview integration
- [ ] Batch processing automation

## Support

For questions, issues, or feature requests, please:

1. Check the troubleshooting section above
2. Search existing issues on the project repository
3. Create a new issue with detailed information about your problem

---

**Footage Thumbnailer** - Making video collection overview simple and efficient.