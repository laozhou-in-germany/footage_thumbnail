# EDL Thumbnail Adjustment Feature Design

## Overview

This document describes the design for adding a new option in the GUI that allows users to choose whether thumbnails should consider the in and out points from EDL files. Currently, the thumbnail extraction process in EDL mode uses interval positions by default, but users have requested more control over this behavior.

## Architecture

The solution involves modifications to the GUI to expose a new configuration option, and backend logic to respect this setting when extracting thumbnails from EDL-referenced video files.

### Key Components

1. **GUI Application**: New checkbox to control whether thumbnail positions should consider EDL in/out points
2. **ConfigManager**: Store the new configuration option
3. **EDLThumbnailExtractor**: Use the configuration to determine position calculation method
4. **UnifiedProcessor**: Coordinate between components based on the new setting

## Feature Requirements

### Functional Requirements

1. Add a new checkbox in the GUI labeled "Use EDL In/Out Points for Thumbnail Positions"
2. When checked, thumbnail positions should be calculated relative to the EDL clip's in/out points
3. When unchecked, thumbnail positions should be calculated using absolute video positions
4. Default behavior should maintain backward compatibility (checked by default)
5. Configuration should persist between sessions

### Non-functional Requirements

1. The feature should not impact performance significantly
2. Error handling should be robust with appropriate user feedback
3. The UI should be intuitive and clearly indicate the effect of the option

## UI Design

### Location

The new option will be added to the EDL section of the GUI, below the existing EDL file selection controls.

### Component Details

- **Component Type**: Checkbox
- **Label**: "Use EDL In/Out Points for Thumbnail Positions"
- **Default State**: Checked (enabled)
- **Tooltip**: "When enabled, thumbnail positions are calculated relative to the clip's in/out points in the EDL. When disabled, absolute video positions are used."

### UI Mockup

```
📁 Source Folders
[Folder selection controls...]

📄 EDL File (Optional)
[EDL file selection controls...]
[New Checkbox] Use EDL In/Out Points for Thumbnail Positions
```

## Backend Implementation

### Configuration Changes

A new configuration parameter will be added:

```json
{
  "edl_use_interval_positions": true
}
```

### Component Modifications

#### ConfigManager

1. Add `edl_use_interval_positions` to default configuration
2. Add validation for the new parameter
3. Add getter method for the parameter

#### EDLThumbnailExtractor

1. Modify `_extract_from_video_file` method to check the new configuration
2. Pass the setting to `_calculate_interval_positions` method
3. Update method signatures to accept the new parameter

#### UnifiedProcessor

1. Ensure the new configuration parameter is passed through to the EDL thumbnail extractor

## Data Flow

```mermaid
graph TD
    A[User selects EDL file] --> B[ConfigManager loads EDL settings]
    C[User toggles "Use EDL In/Out Points"] --> D[ConfigManager updates setting]
    E[User starts processing] --> F[UnifiedProcessor checks config]
    F --> G{edl_use_interval_positions?}
    G -->|Yes| H[Calculate positions relative to EDL interval]
    G -->|No| I[Calculate positions using absolute video time]
    H --> J[Extract thumbnails]
    I --> J[Extract thumbnails]
    J --> K[Generate contact sheet]
```

## Implementation Plan

### Phase 1: Backend Implementation

1. Add the new configuration parameter to ConfigManager
2. Modify EDLThumbnailExtractor to respect the new setting
3. Update UnifiedProcessor to pass the setting through

### Phase 2: UI Implementation

1. Add the new checkbox to the GUI
2. Connect the checkbox to the configuration
3. Add appropriate labels and tooltips

### Phase 3: Testing

1. Unit tests for the new configuration parameter
2. Integration tests for the thumbnail extraction with different settings
3. UI tests to verify the control works correctly

## Testing Strategy

### Unit Tests

1. Test ConfigManager with the new parameter
2. Test EDLThumbnailExtractor with both settings enabled and disabled
3. Verify position calculation logic for both modes

### Integration Tests

1. Test the complete workflow with the new option enabled
2. Test the complete workflow with the new option disabled
3. Verify backward compatibility

### UI Tests

1. Verify the checkbox appears in the correct location
2. Test that the checkbox state is saved and loaded correctly
3. Confirm that tooltips and labels are clear and accurate

## Backward Compatibility

The feature maintains full backward compatibility by:
1. Defaulting the new option to enabled (existing behavior)
2. Making the configuration parameter optional in validation
3. Ensuring the code gracefully handles missing configuration

## Error Handling

1. If the configuration parameter is missing, default to enabled (existing behavior)
2. If there are issues with position calculation, fall back to absolute positioning
3. Provide clear error messages in the log if position calculation fails

## Performance Considerations

1. The feature should not significantly impact processing time
2. Position calculation logic is already optimized, so no major changes are needed
3. Caching mechanisms in EDLVideoScanner remain unchanged