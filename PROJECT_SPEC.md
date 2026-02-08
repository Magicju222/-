# Project Specification: Apple-Style AI Excel Cleaner

This document defines the development standards, agent roles, and invocation protocols for the AI Excel Cleaner project.

## 1. Project Overview
A Streamlit-based application designed to clean and standardizing messy Excel files using **local algorithms** (no longer dependent on Gemini AI). The project features a strict **Apple Human Interface Guideline (HIG)** aesthetic, utilizing glassmorphism, fluid animations, and a bilingual (Simplified Chinese/English) interface.

## 2. Agent Definitions & Roles
In this project, we utilize specialized AI agents to handle different aspects of the codebase. You can freely invoke these agents based on the task type.

### 🤖 Frontend Architect (`frontend-architect`)
**Responsibility**: Application Logic & Component Orchestration.
- **Scope**: `app.py`, `ui.py`, `i18n.py`.
- **Tasks**:
    - Managing Streamlit session state and interactivity.
    - Implementing logic flow (e.g., file upload -> processing -> download).
    - Handling internationalization (i18n) logic.
    - Component structure and layout (Grid, Containers).

### 🎨 UI Designer (`ui-designer`)
**Responsibility**: Visual Aesthetics & CSS styling.
- **Scope**: `style.css`, UI Component rendering strings in `ui.py`.
- **Tasks**:
    - Implementing Glassmorphism effects (backdrop-filter, rgba backgrounds).
    - Designing animations (keyframes, transitions, hover effects).
    - Ensuring "Apple-like" consistency (Shadows, Typography, Rounding).
    - Creating responsive layouts and hiding native Streamlit elements.

### ⚙️ Backend Architect (`backend-architect`)
**Responsibility**: Data Processing & Core Logic.
- **Scope**: `cleaner.py`, `requirements.txt`.
- **Tasks**:
    - Excel file parsing (OpenPyXL, Pandas, xlrd).
    - Local Algorithms (Rule-based cleaning, Smart Fill).
    - Data cleaning algorithms (Merge handling, Header detection).
    - Performance optimization and error handling.

### 🧪 QA Specialist (`api-test-pro`)
**Responsibility**: Testing & Validation.
- **Scope**: `demo.xlsx`, Manual Testing Scripts.
- **Tasks**:
    - Validating file upload/download flows.
    - Verifying Excel cleaning integrity.
    - Stress testing large file uploads.

## 3. Agent Invocation Timing
Call the respective agent when your task falls into their domain:

| Scenario | Agent to Call | Example Request |
| :--- | :--- | :--- |
| **New Visual Feature** | `ui-designer` | "Add a frosted glass effect to the sidebar." |
| **Logic/State Change** | `frontend-architect` | "Add a toggle to switch between cleaning modes." |
| **Data Algo Update** | `backend-architect` | "Improve the algorithm for detecting multi-level headers." |
| **Bug in Display** | `ui-designer` | "The upload button is misaligned on mobile." |
| **Bug in Processing** | `backend-architect` | "The cleaner crashes on empty columns." |

## 4. Development Workflow
1.  **Requirement Analysis**: Use the `search` tool to understand existing code context.
2.  **Agent Selection**: Assign the task to the specific agent defined above.
3.  **Implementation**:
    - **Visuals**: Edit `style.css` first, then apply classes in Python.
    - **Logic**: Edit `cleaner.py` for core logic, then expose in `app.py`.
4.  **Verification**: Always run the app to verify changes before marking complete.

## 5. Current Design Standards (v1.3.0)
- **Visual Style**: Apple Glassmorphism (Mesh Gradients, Blur 30px).
- **Language**: Default Simplified Chinese (zh), toggleable to English (en).
- **Primary Color**: `#007AFF` (Apple Blue).
- **Font**: System UI (San Francisco/Segoe UI).
- **Processing Mode**: Local Only (Rule-based).
- **Documentation**: In-app User Guide integrated via `USER_GUIDE.md`.
- **Architecture**: Multi-sheet capable with isolated state management per sheet.

## 6. Maintenance Guide
### Adding New File Formats
1.  Update `app.py`: Add extension to `st.file_uploader`.
2.  Update `cleaner.py`: Add loading logic in `load_and_fill_merged_cells` (use appropriate engine).
3.  Update `i18n.py`: Update `uploader_instruction` text.

### Updating UI Text
- Always edit `i18n.py`. Do not hardcode strings in `ui.py` or `app.py`.
- Ensure both `zh` and `en` keys are updated.

### Modifying Cleaning Logic
- Core logic resides in `cleaner.py`.
- `process_headers`: Handles header flattening.
- `process_key_columns`: Handles vertical fill (ffill).
- `clean_data`: Orchestrates the pipeline.
