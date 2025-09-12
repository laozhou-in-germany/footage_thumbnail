# Update Script and GUI to Work with FCPXML Files Only

## Overview

This document outlines the changes required to modify the Footage Thumbnailer application to work exclusively with FCPXML files instead of EDL files. The current implementation supports both EDL and FCPXML formats, but the requirement is to remove EDL support and make FCPXML the only supported format for timeline-based thumbnail generation.

## Architecture

### Current State
The application currently supports three processing modes:
1. Standard folder-based processing
2. EDL file-based processing
3. FCPXML file-based processing

Both EDL and FCPXML processing modes use the UnifiedProcessor to handle timeline-based workflows, with specific parsers and processors for each format.

### Target State
After the changes, the application will support:
1. Standard folder-based processing
2. FCPXML file-based processing (renamed from EDL/FCPXML mode)

The EDL-specific components will be removed, and all timeline-based processing will be handled through the FCPXML workflow.

## Component Changes

### 1. Core Processing Layer

#### UnifiedProcessor Changes
- Remove EDL-specific processing methods
- Rename FCPXML processing method to generic timeline processing method
- Simplify mode detection to check only for FCPXML files
- Remove EDL-specific component initialization
- Update processing mode detection

#### Configuration Manager Changes
- Remove EDL-specific configuration parameters
- Remove EDL validation logic
- Update method names to reflect FCPXML focus

#### FCPXML Parser
- Rename entry class to generic timeline entry
- Update references from EDL to Timeline throughout the parser
- Simplify class structure

### 2. GUI Application Changes

#### UI Component Updates
- Rename "EDL File" section to "Timeline File" 
- Update file selection dialog to only show FCPXML files
- Remove EDL-specific labels and help text
- Rename EDL-related UI elements and variables

#### Processing Logic
- Update file validation to check only for FCPXML files
- Modify processing workflow to use timeline mode exclusively
- Update status messages to reflect FCPXML processing

### 3. CLI Interface Changes
- Remove any EDL-specific command line arguments
- Update help text to reference FCPXML files
- Simplify processing logic to use timeline mode

## API Endpoints Reference

### Core Processing APIs

#### UnifiedProcessor API
- process_thumbnails(): Main processing method
- _is_timeline_mode(config): Check if timeline mode should be used
- _process_timeline_mode(config): Process thumbnails based on timeline file
- _process_folder_mode(config): Process thumbnails based on source folders

#### ConfigManager API
- _get_default_config(): Get default configuration
- _validate_config(config): Validate configuration
- is_timeline_mode(): Check if timeline mode is enabled

#### TimelineParser API
- parse_timeline_file(file_path): Parse timeline file and extract video entries
- _parse_resources(root): Parse resources section
- _parse_timeline(root): Parse timeline section

## Data Models

### TimelineEntry
Represents a single video entry from a timeline file.

Fields:
- source_id: int
- file_path: str
- media_type: str
- start_time: Optional[float]
- end_time: Optional[float]
- track_info: Optional[str] = None

### Configuration Parameters
Key configuration parameters for timeline processing:

- timeline_file_path (str): Path to the timeline file
- timeline_show_placeholders (bool): Show placeholders for missing files
- timeline_use_interval_positions (bool): Use timeline in/out points for thumbnail positions
- timeline_placeholder_color (str): Color for placeholder thumbnails
- timeline_similarity_threshold (float): Similarity threshold for file matching

## Business Logic Layer

### Timeline Processing Workflow

The timeline processing workflow follows these steps:

1. Start Processing
2. Check if timeline file is provided
3. If timeline file provided:
   - Validate timeline file
   - Parse timeline file
   - Validate video file paths
   - Extract thumbnails
   - Create contact sheet
   - Save output
4. If no timeline file provided:
   - Standard folder processing
   - Scan folders for videos
   - Extract thumbnails
   - Create contact sheet
   - Save output
5. End

### File Validation Logic
1. Check if timeline file path is provided
2. Verify file exists and is readable
3. Confirm file has .fcpxml extension
4. Parse timeline file to extract video references
5. Validate each referenced video file exists

### Thumbnail Extraction Logic
1. For each timeline entry:
   - If file exists: Extract thumbnails at specified positions
   - If file missing and placeholders enabled: Create placeholder thumbnail
   - If file missing and placeholders disabled: Skip entry
2. Apply timeline in/out point logic based on configuration
3. Generate metadata overlays for each thumbnail

## Middleware & Interceptors

### Configuration Validation
Before processing begins, the system validates:
- Timeline file exists and is accessible
- All referenced video files are accessible
- Configuration parameters are within valid ranges
- Output directory is writable

### Progress Reporting
During processing, progress updates are sent through callbacks:
- File parsing progress
- Video file validation progress
- Thumbnail extraction progress
- Image composition progress
- Output saving progress

## Testing

### Unit Tests

#### Core Processing Tests
- Timeline file parsing and validation
- Video file path validation
- Thumbnail extraction with timeline positions
- Contact sheet generation from timeline data
- Configuration validation for timeline mode

#### GUI Tests
- File selection dialog for timeline files
- UI element updates when timeline file is selected
- Processing workflow with timeline file
- Error handling for missing timeline files
- Error handling for missing video files

#### Configuration Tests
- Default configuration loading
- Timeline-specific parameter validation
- Configuration persistence for timeline settings
- Backward compatibility with existing configurations

### Integration Tests
- End-to-end timeline processing workflow
- File format validation and error handling
- Multi-video timeline processing
- Placeholder generation for missing files
- Large timeline file processing

### Test Scenarios

#### Scenario 1: Valid Timeline Processing
Given a valid FCPXML file with 5 video references, when user processes thumbnails with timeline mode, then contact sheet is generated with 5 video sections.

#### Scenario 2: Missing Video Files
Given FCPXML file with references to non-existent videos, when user processes thumbnails with placeholders enabled, then contact sheet includes placeholder thumbnails for missing files.

#### Scenario 3: Invalid Timeline File
Given an invalid or non-existent timeline file, when user attempts to process thumbnails, then appropriate error message is displayed.

## Implementation Plan

### Phase 1: Core Logic Updates
1. Update UnifiedProcessor to remove EDL support
2. Rename EDL-related methods and variables to timeline equivalents
3. Update configuration manager to remove EDL parameters
4. Update FCPXML parser class names and references

### Phase 2: GUI Updates
1. Rename UI elements from EDL to Timeline/FCPXML
2. Update file selection dialogs
3. Modify processing workflow
4. Update status messages and help text

### Phase 3: CLI Updates
1. Remove EDL-specific command line arguments
2. Update help text and examples
3. Simplify processing logic to use timeline mode

### Phase 4: Testing and Validation
1. Update unit tests for modified components
2. Add new tests for timeline-only workflow
3. Validate end-to-end processing
4. Test error handling scenarios