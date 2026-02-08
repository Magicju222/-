# Changelog

## [v2.0-Visual-Overhaul] - 2026-02-08

### 🎨 Visual & UI Major Update (Apple Design)
- **True Frosted Glass (Glassmorphism)**: 
    - Refactored the entire UI (Upload Card, Buttons, Panels) to use a transparent base (`rgba(255, 255, 255, 0.01)`) with `backdrop-filter: blur(24px)`, creating a premium, deep glass effect.
- **Laser Flow Animation**:
    - Added a high-fidelity "Laser Flow" effect to the File Uploader and Secondary Buttons.
    - Implemented using a rotating conic gradient on a pseudo-element (`::before`) hidden behind the glass layer.
    - **Smart Interaction**: The User Guide button features a persistent laser pulse that stops upon first click (marking it as "read"), then reverts to a hover-only effect.
- **Advanced Typography**:
    - Redesigned the File Uploader text hierarchy.
    - Replaced default Streamlit text with custom-injected CSS content.
    - **Title**: 24px Bold with dark gradient.
    - **Subtitle**: 16px Regular with refined spacing.
    - **Details**: 13px Uppercase secondary info.
- **Component Styling**:
    - **Buttons**: Differentiated `Primary` (Solid Blue) and `Secondary` (Glass + Laser) button styles.
    - **Icons**: Added a custom 3D/Glassy folder icon to the uploader with dynamic hover shadows.

## [v1.3.0-Multi-Sheet-Support] - 2026-02-08

### 🚀 Major Feature: Multi-Sheet Batch Processing
- **Sheet Awareness**: The application now automatically detects all sheets in the uploaded file (`.xlsx` or `.xls`).
- **Batch Selection**: Users can select multiple sheets to clean simultaneously via a multi-select dropdown.
- **Independent Configuration**: Each selected sheet gets its own configuration tab, allowing for unique header/data row definitions per sheet.
- **Unified Export**: The "Start Batch Cleaning" process combines all cleaned sheets into a single download file, preserving the original sheet names.

## [v1.2.1-User-Guide-Integration] - 2026-02-08

### 📚 Documentation & Help
- **Integrated User Guide**: Added a dedicated "User Guide" button in the navigation bar.
- **In-App Reading**: Clicking the guide button opens the full `USER_GUIDE.md` content directly within the app (using Modal Dialog if supported, or Sidebar fallback).
- **Updated Instructions**: Refined the step-by-step instructions in the UI to match the current manual workflow (Upload -> Define -> Clean).

### 📂 File Support Update
- **CSV Support**: Explicitly added `.csv` to the supported file types list in the upload area instructions.
- **Text Fixes**: Corrected duplicate numbering in the UI step indicators.

## [v1.2-Local-Mode-Interactive] - 2026-02-07

### 🚀 Major Feature: Local & Manual Control
- **Removed AI Dependency**: Completely removed Google Gemini AI integration. The application now runs 100% locally with no API Key required.
- **Interactive Structure Selection**:
    - Users can now **click** on table rows to define Header Rows and Data Start Row directly.
    - Added real-time visual feedback (Yellow for Headers, Green for Data Start).
    - Bi-directional sync between the visual selector and the sidebar settings.
- **Key Columns (Vertical Fill)**:
    - Added support for selecting **Index Columns** (Key Columns) by clicking on column headers.
    - Selected columns automatically perform **Vertical Forward-Fill** (unmerge and fill down), solving the issue of merged cells in grouping columns (e.g., "Region" or "Category").

### 📂 Enhanced File Support
- **Format Expansion**: Added support for legacy `.xls` (Excel 97-2003) and `.csv` files.
- **Robust Loading**: Implemented fallback mechanisms to handle file type mismatches (e.g., CSV files with .xls extension).

### 🛠 UI/UX Improvements
- **1-Based Indexing**: All row numbers in the UI (both input boxes and table display) now start from 1, matching Excel's native display logic.
- **Status Indicators**: Updated Sidebar to reflect the "Local Mode" status (API Key disabled).
- **Expanded Preview**: Increased the data preview limit from 50 to 1000 rows to facilitate better structure selection for larger files.
- **Optimized Layout**: Increased the interactive table height to 600px for better visibility.

## [v1.1-Refactored-Architecture] - 2026-02-07

### 🏗 Architecture & Code Quality
- **MVC Pattern Implementation**: Decoupled the application into clear layers:
    - `app.py`: Lightweight Controller for state and flow.
    - `ui.py`: Dedicated View layer handling all Streamlit rendering and CSS injection.
    - `cleaner.py`: Model layer for business logic and data processing.
    - `i18n.py`: Centralized text resource management with helper functions.
- **Project Specifications**: Created `PROJECT_SPEC.md` to define Agent roles (Frontend, Backend, UI, QA) and development standards.

### 🎨 UI/UX Refinements
- **Enhanced Interactivity**: 
    - Fixed Navbar z-index issues allowing proper interaction with the Sidebar toggle.
    - Implemented "Click-through" header (`pointer-events`) to ensure Navbar items are clickable.
    - Added "Pill-shape" hover effects to Navbar items and Header buttons for better feedback.
- **Visual Polish**: 
    - Optimized Mesh Gradient for a smoother, "breathing" background.
    - Refined Glassmorphism parameters (`blur(30px)`) for better legibility.
    - Standardized rounded corners and shadows to strictly follow Apple HIG.

### 🛡️ Robustness & Stability
- **File Validation**: Restricted uploads to `.xlsx` only and added specific error handling for `zipfile.BadZipFile` to prevent crashes on invalid files.
- **Data Processing**: Fixed `Duplicate column names` error in `cleaner.py` by auto-renaming duplicate headers (e.g., `Total`, `Total_1`).
- **Error Handling**: Added try-catch blocks for file loading to provide user-friendly error messages.

### File Structure Update
- `ui.py`: [NEW] Handles all UI components (Navbar, Hero, Sidebar, Results).
- `PROJECT_SPEC.md`: [NEW] Development guidelines.

## [v1.0-Apple-Glass] - 2024-02-07

### Core Features
- **AI-Powered Cleaning**: Implemented `cleaner.py` using Google Gemini to identify header structures and clean noise data.
- **Excel Processing**: Integrated `openpyxl` for handling merged cells and preserving data integrity.
- **Semantic Flattening**: Added algorithm to merge multi-level headers into single semantic columns.

### UI/UX Improvements (Apple Style)
- **Glassmorphism Design**: Implemented full-page mesh gradient background and frosted glass cards with `backdrop-filter`.
- **Custom Dropzone**: Completely redesigned the Streamlit file uploader to mimic Apple's native dropzone, removing default text and buttons.
- **Micro-interactions**: Added fade-in animations (`fadeInUp`) for page elements and scale/glow effects for hover states.
- **Typography**: Switched to San Francisco-style font stack (`-apple-system`, `SF Pro Display`).
- **Clean Layout**: Hidden default Streamlit header (hamburger menu visible but transparent), footer, and deploy button.

### Internationalization
- **Bilingual Support**: Full support for Simplified Chinese (`zh`) and English (`en`).
- **Dynamic CSS**: Implemented CSS variable injection (`--current-lang`) to toggle pseudo-element text in the uploader component.
- **Immediate Switching**: Language switch triggers immediate app rerun for instant UI update.

### File Structure
- `app.py`: Main application entry point.
- `cleaner.py`: Core logic for Excel processing.
- `style.css`: Comprehensive styling overrides.
- `i18n.py`: Translation dictionary.
- `demo.xlsx`: Mock data for testing.
