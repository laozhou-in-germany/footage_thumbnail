# Product Requirements Document: Footage Thumbnailer
**Version:** 1.8

**Date:** September 10, 2025

**Author:** Gemini

**Revision Note:** Added detailed GUI mockup and exported picture mockup sections to provide clear visual specifications for development and design teams.

## 1. Introduction & Vision

### 1.1. Problem Statement
Videographers, especially travel vloggers and content creators, often accumulate a large volume of raw footage spread across multiple folders. Quickly reviewing and identifying specific clips is a time-consuming and inefficient process. There is no simple way to get a quick, visual overview of dozens or hundreds of video files at a glance.

### 1.2. Product Vision
To create a tool that automates the generation of visual "contact sheets" or thumbnail overviews for video footage.

**Phase 1 (MVP):** Deliver a powerful and scriptable command-line tool that contains all the core video processing and image composition logic, configured via a simple JSON file.

**Phase 2 (GUI):** Wrap the core engine from Phase 1 into a user-friendly desktop application with an intuitive graphical interface, making the tool accessible to a broader, non-technical audience.

### 1.3. Key Goals
- **Efficiency:** Drastically reduce the time needed to review and catalogue raw footage.
- **Customization:** Allow users to control the output to fit their specific needs through a persistent configuration file.
- **Usability:** Provide a simple, intuitive interface appropriate for each phase (a clear config file for the CLI, a point-and-click GUI for the final application).

### 1.4. Target Output Mockup (Exported Picture)
The final exported image will be a single grid-based "contact sheet" by default. When dealing with large collections, the application can automatically split the output into multiple manageable images based on a maximum row limit to avoid excessively long single images.

**Multi-Page Support:**
- **Automatic Pagination:** When `max_rows_per_image` is set (> 0), large collections are split into multiple pages
- **File Naming:** Additional pages are named with sequential suffixes (e.g., `overview.jpg`, `overview_page02.jpg`, `overview_page03.jpg`)
- **Configurable Limit:** Users can set the maximum number of rows per image to control output size
- **Practical Benefits:** Prevents unwieldy long images, improves shareability and viewing on different devices

Each row will contain thumbnails for multiple video clips. For each video clip, a set of thumbnails (e.g., from the start, middle, and end) will be displayed. These thumbnails will have an overlay containing the video's filename, creation date/time, and duration for quick identification.

#### 1.4.1. Detailed Exported Picture Specifications

**Overall Layout:**
- Grid-based structure with configurable rows and columns
- Each video clip occupies one "cell" containing multiple thumbnails
- White or light gray background for the entire contact sheet
- Consistent spacing between all elements

**Individual Video Clip Cell Structure:**
```
┌─────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────┐ │ ← Frame border
│ │ filename.mp4          2024-08-15 14:32:17  │ │
│ │ ┌────────┐ ┌────────┐ ┌────────┐           │ │
│ │ │ Frame  │ │ Frame  │ │ Frame  │           │ │
│ │ │   1    │ │   2    │ │   3    │           │ │
│ │ │ (0%)   │ │ (50%)  │ │ (99%)  │           │ │
│ │ └────────┘ └────────┘ └────────┘     03:47 │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Text Overlay Specifications:**
- **Positioning Options:** 
  - `"above_thumbnails"` (default): Text displayed in a header above the thumbnails for cleaner thumbnail viewing
  - `"on_thumbnails"`: Text overlaid directly on thumbnails (original behavior)
- **Filename:** Displayed in header (above_thumbnails mode) or top-left (on_thumbnails mode)
- **Creation Date/Time:** Displayed in header (above_thumbnails mode) or top-right (on_thumbnails mode), format "YYYY-MM-DD HH:MM:SS"
- **Duration:** Displayed in header (above_thumbnails mode) or bottom-right of last thumbnail (on_thumbnails mode), format "MM:SS"
- **Timestamp:** Always displayed on thumbnails bottom-left for time reference
- **Font:** Clear, readable sans-serif font
- **Background:** Semi-transparent black overlay (opacity ~70%) behind text for readability

**Thumbnail Specifications:**
- **Size:** Configurable width (default 320px), height auto-calculated maintaining aspect ratio
- **Positions:** Configurable frame extraction points (default: 0%, 50%, 99%)
- **Border:** Thin border around each thumbnail for definition
- **Quality:** High enough for clear preview but optimized for file size

**Frame Specifications:**
- **Purpose:** Visual grouping to clearly identify which thumbnails belong to each video
- **Default:** Enabled with light gray border (#CCCCCC)
- **Thickness:** 2px border with 10px internal padding
- **Color Options:** Customizable (hex colors, named colors like 'black', 'gray')
- **Disable Option:** Can be turned off via configuration or CLI flag

**Example Full Contact Sheet Layout (5 clips per row):**
```
Row 1: [Clip1] [Clip2] [Clip3] [Clip4] [Clip5]
Row 2: [Clip6] [Clip7] [Clip8] [Clip9] [Clip10]
Row 3: [Clip11] [Clip12] [Clip13] [Clip14] [Clip15]
...
```

### 1.5. GUI Application Mockup

#### 1.5.1. Main Window Layout
The GUI will feature a clean, modern interface with the following sections arranged vertically:

```
┌─────────────────────────────────────────────────────────────────┐
│ Footage Thumbnailer                                    [_][□][×] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📁 Source Folders                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ C:\Users\YourUser\Videos\Trip1                              │ │
│ │ D:\Footage\Project_Alpha                                    │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [Select Folders...] [Clear All]                                 │
│                                                                 │
│ ⚙️ Settings                                                     │
│ ┌─────────────────────────┬─────────────────────────────────────┐ │
│ │ Thumbnail Width:        │ Clips Per Row:                      │ │
│ │ [320        ] px        │ [5        ]                         │ │
│ │                         │                                     │ │
│ │ Thumbnail Positions:    │ Output Format:                      │ │
│ │ [0%,50%,99%      ]      │ [JPEG ▼]                            │ │
│ └─────────────────────────┴─────────────────────────────────────┘ │
│                                                                 │
│ 📤 Output                                                       │
│ Output Path: [C:\Users\YourUser\Documents\overview.jpg        ] │
│ [Browse...]                                                     │
│                                                                 │
│                        [Generate Overview]                      │
│                                                                 │
│ Progress: ████████████████████░░░░░░░░░░ 67% (Processing...)    │
│                                                                 │
│ 📋 Log                                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Found 24 video files in selected folders                   │ │
│ │ Processing video: family_dinner.mp4 (12 of 24)            │ │
│ │ Extracted 3 thumbnails from family_dinner.mp4             │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.5.2. Detailed GUI Component Specifications

**Window Properties:**
- **Title:** "Footage Thumbnailer"
- **Size:** 800x700 pixels (resizable)
- **Minimum Size:** 600x500 pixels
- **Style:** Modern, clean design with proper spacing and typography

**Source Folders Section:**
- **Multi-line text area** displaying selected folder paths (one per line)
- **"Select Folders..." button** opens native folder selection dialog (multi-select enabled)
- **"Clear All" button** removes all selected folders
- **Icon:** Folder icon (📁) for visual clarity

**Settings Section:**
- **Two-column layout** for efficient space usage
- **Thumbnail Width:** Numeric input field with "px" label
- **Clips Per Row:** Numeric input field
- **Thumbnail Positions:** Text input for comma-separated values (with tooltip showing examples)
- **Output Format:** Dropdown menu (JPEG, PNG options)

**Output Section:**
- **Output Path:** Text field showing current output file path
- **"Browse..." button** opens "Save As" dialog for path selection

**Action Section:**
- **"Generate Overview" button:** Primary action button, prominently styled
- **Progress Bar:** Shows completion percentage and current status text
- **States:** 
  - Disabled when no folders selected
  - "Processing..." state during operation
  - "Complete!" state when finished

**Log Section:**
- **Scrollable text area** showing real-time processing updates
- **Auto-scroll** to latest entries
- **Clear button** to empty log (small, unobtrusive)

**Additional UI Elements:**
- **Tooltips** on hover for all input fields explaining their purpose
- **Validation indicators** showing invalid inputs (red border/text)
- **Status bar** at bottom showing total files found and processing time

#### 1.5.3. GUI Behavior Specifications

**Startup Behavior:**
- Load settings from `config.json`
- Populate all fields with saved values
- Show last-used source folders
- Focus on folder selection if no folders are configured

**Input Validation:**
- Thumbnail width: 100-1000 pixels
- Clips per row: 1-10
- Thumbnail positions: Valid percentage/time format
- Real-time validation with visual feedback

**Processing Flow:**
1. User clicks "Generate Overview"
2. Save current GUI settings to `config.json`
3. Disable controls and show progress
4. Run processing in background thread
5. Update progress bar and log in real-time
6. On completion, enable "Open Output" and "Open Folder" buttons
7. Re-enable all controls

## 2. Target Audience

**Primary:** Travel Vloggers & YouTubers: Often deal with large quantities of unorganized clips from various sources.

**Secondary:** Professional Videographers & Editors: Need to quickly catalogue footage from shoots for archival or editing purposes. (This group is the primary target for the Phase 1 MVP).

**Tertiary:** Hobbyists & Casual Video Shooters: Want a simple way to organize and preview their video libraries. (This group is the primary target for the Phase 2 GUI).

## 3. Phased Features & User Stories

### 3.1. Phase 1: MVP (Command-Line Tool)

**CLI-101 (Folder Input):** As a user, I want to define my default source folders in the config file, and optionally specify different folders on the command line to override the default for a specific run.

**CLI-102 (Automatic Scanning):** As a user, I expect the application to automatically find all valid video files (e.g., .MP4, .MOV, .AVI) within the specified folders and subfolders.

**CLI-103 (Centralized Configuration):** As a user, I want to define all my preferences (thumbnail size, positions, clips per row) in a single config.json file so I don't have to type them every time I run the tool.

**CLI-104 (Information Overlay):** As a user, I want the filename, length (in MM:SS format), and the shooting date/time of each video clip to be displayed on its set of thumbnails for easy identification.

**CLI-105 (Configuration Override):** As a user, I want the ability to temporarily override any setting from my config file using a command-line flag for a specific task.

**CLI-106 (Default Config Generation):** As a user, I want the application to generate a default config.json file on first run so I can easily see and edit all available options.

### 3.2. Phase 2: GUI Application

**GUI-101 (Folder Selection):** As a user, I want to select one or more folders containing my video files using a graphical file dialog so the application can scan them all at once.

**GUI-102 (Intuitive Controls):** As a user, I want a simple graphical interface where I can view and change my preferences, which are loaded from and saved to the central config.json file.

**GUI-103 (Visual Feedback):** As a user, I want to see a progress bar that shows the real-time status of the operation so I know the application is working.

**GUI-104 (Simple Save):** As a user, I want to use a "Save As..." dialog upon completion to choose the location and name for the output image file.

## 4. Phased Functional Requirements

### 4.1. Phase 1: MVP (Command-Line Tool)

#### 4.1.1. CLI Specifications
- The application shall be executable from the command line.
- The primary method for configuration shall be a JSON file located at `src/config.json`.
- If `src/config.json` does not exist, the application shall create it with default values upon the first run.
- If no source folders are provided as command-line arguments, the application will use the paths defined in the `source_folders` list within config.json.
- The CLI will accept optional arguments (e.g., source folder paths, --output, --width) to override the values present in `src/config.json` for a single run.
- The tool shall print progress updates to the console (e.g., "Processing video 5 of 50...").

#### 4.1.2. Configuration File (src/config.json)
The application will read its default parameters from this file. The file structure will be as follows:

```json
{
  "source_folders": [
    "C:/Users/YourUser/Videos/Trip1",
    "D:/Footage/Project_Alpha"
  ],
  "output_path": "output/overview.jpg",
  "thumbnail_width": 320,
  "clips_per_row": 5,
  "positions": "0%,50%,99%",
  "padding": 5,
  "supported_extensions": [
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".mts"
  ]
}
```

#### 4.1.3. Video Processing Logic
- The system shall recursively scan directories for files with extensions defined in the `supported_extensions` list in config.json.
- For each video, use the FFmpeg library to reliably extract metadata (duration, creation date/time) and frames based on the positions timestamps from the config.
- The system must gracefully handle video files that are missing creation date metadata, leaving that part of the overlay blank for that specific clip.
- The application will parse the positions string, handling both absolute seconds and percentages.
- The following information shall be stamped onto the thumbnails for each clip, using a semi-transparent background for readability: the filename (top-left of the first thumbnail), the creation date and time (top-right of the first thumbnail), and the duration in MM:SS format (bottom-right of the last thumbnail).

#### 4.1.4. Image Composition Logic
- The logic will use parameters from config.json (or their command-line overrides) to calculate final image dimensions and arrange thumbnails in a grid.
- A small amount of padding should be added between all thumbnails.

### 4.2. Phase 2: GUI Application

#### 4.2.1. GUI Specifications
- The GUI will be built on top of the core logic from Phase 1.
- On startup, the GUI shall load all settings, including the last-used source folders, from `src/config.json` and populate the input fields.
- A "Select Folder(s)" button opening a native file system dialog.
- A text area to display selected folder paths.
- Input fields for "Thumbnail Width," "Clips Per Row," and "Thumbnail Positions".
- A "Generate Overview" button to start the process. When clicked, any changes made in the GUI fields (including the selected source folders) will be saved back to `src/config.json`, making them persistent.
- A progress bar for real-time status updates.
- A "Save As..." button that appears upon completion for outputting PNG or JPG files.

## 5. Non-Functional Requirements

**Performance:**
- Phase 1: The CLI tool should process videos efficiently and provide regular console feedback to avoid appearing frozen.
- Phase 2: All video processing must happen in a background thread to prevent the GUI from freezing.

**Compatibility:** The application must be compatible with Windows 10 and Windows 11 in both phases.

**Error Handling:** The system must gracefully handle errors (e.g., corrupted files, invalid config.json syntax, missing metadata) and report the issue to the user without crashing in both phases.

**Usability:**
- Phase 1: The CLI must have clear instructions and error messages. A --help flag should be available.
- Phase 2: The GUI should be self-explanatory, requiring no user manual.

## 6. Technical Stack Recommendations

### 6.1. Phase 1: MVP (CLI)
- **Language:** Python 3.9+
- **Core Libraries:**
  - `json`: (Standard library) For parsing the config.json file.
  - `opencv-python`: For efficient video frame extraction.
  - `ffmpeg-python`: For robust video file metadata reading.
  - `Pillow`: For final image composition and text overlays.
- **Packaging:** PyInstaller or cx_Freeze to create a distributable executable file.

### 6.2. Phase 2: GUI
- **GUI Framework:** CustomTkinter or PyQt6 for a modern, professional look and feel.
- All other libraries from Phase 1 will be reused.