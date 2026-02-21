import streamlit as st
import pandas as pd
from i18n import get_text
import io
import os
import numpy as np

def t(key):
    return get_text(st.session_state.get('lang', 'zh'), key)

# Dialog / Modal for User Guide
if hasattr(st, "dialog"):
    @st.dialog("📘 User Guide / 使用手册")
    def show_user_guide_modal():
        try:
            with open("USER_GUIDE.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except Exception as e:
            st.error(f"Could not load User Guide: {e}")
else:
    # Fallback for older Streamlit versions
    def show_user_guide_modal():
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 📘 User Guide")
            try:
                with open("USER_GUIDE.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except Exception as e:
                st.error(f"Could not load User Guide: {e}")

def load_css():
    try:
        with open("style.css", "r", encoding="utf-8") as f:
            css = f.read()
        
        # Get localized instructions
        title = t("uploader_title")
        subtitle = t("uploader_subtitle")
        details = t("uploader_details")
        
        # Check if in admin panel mode
        is_admin_panel = st.session_state.get('show_admin_panel', False)
        
        # Inject CSS with dynamic content
        import time
        version = int(time.time())
        
        # Admin panel specific CSS to hide file uploader
        admin_css = ""
        if is_admin_panel:
            admin_css = """
            /* Hide file uploader in admin panel */
            [data-testid='stFileUploader'] {
                display: none !important;
            }
            [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stFileUploader"]) {
                display: none !important;
            }
            """
        
        st.markdown(f"""
        <style id="custom-css-{version}">
            {css}
            {admin_css}
            
            /* Dynamic Content Injection for I18n */
            /* Title on the inner text wrapper's BEFORE */
            [data-testid="stFileUploaderDropzoneInstructions"] > div::before {{
                content: "{title}";
            }}
            
            /* Subtitle + Details on the inner text wrapper's AFTER */
            [data-testid="stFileUploaderDropzoneInstructions"] > div::after {{
                content: "{subtitle} \\A {details}";
            }}
        </style>
        """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("style.css not found!")

def render_navbar():
    # Navbar structure updated to use Streamlit columns for interactivity
    col_brand, col_spacer, col_btn = st.columns([2, 6, 2])
    
    with col_brand:
        # Use existing CSS classes but simplified container
        st.markdown(f"""
        <div class="nav-item" style="font-weight: 600; font-size: 1.1rem; padding-top: 5px;">
             AI Cleaner
        </div>
        """, unsafe_allow_html=True)
        
    with col_btn:
        # User Guide Button
        
        # Callback to update state BEFORE rerun/render
        def on_guide_click():
            st.session_state.guide_clicked = True
            
        if st.button(t("user_guide_btn"), icon="📖", use_container_width=True, on_click=on_guide_click):
            show_user_guide_modal()
            
    st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem; opacity: 0.2;'>", unsafe_allow_html=True)

def render_hero():
    st.markdown(f"""
    <div class="hero-container">
        <h1 class="hero-title">{t('hero_title')}</h1>
        <div class="hero-subtitle">{t('hero_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

def render_no_file_instruction():
    st.markdown(f"""
    <div class="instruction-container">
        <p class="instruction-step">1. {t('step_1')}</p>
        <p class="instruction-step">2. {t('step_2')}</p>
        <p class="instruction-step">3. {t('step_3')}</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(api_key_val=None, suggested_structure=None):
    with st.sidebar:
        st.header(t("settings"))
        
        # Language Switcher
        current_lang = st.session_state.get('lang', 'zh')
        lang_choice = st.radio(
            t("language"), 
            ["简体中文", "English"], 
            index=0 if current_lang == 'zh' else 1
        )
        
        # Update state and rerun immediately if changed
        if lang_choice == "简体中文" and current_lang != 'zh':
            st.session_state.lang = 'zh'
            st.rerun()
        elif lang_choice == "English" and current_lang != 'en':
            st.session_state.lang = 'en'
            st.rerun()
            
        # API Key
        # If passed from outside (e.g. env var), use it, otherwise normal input
        api_key_kwargs = {
            "label": t("api_key_label"),
            "type": "password",
            "key": "api_key_input",
            "help": t("api_key_help")
        }
        if "api_key_input" not in st.session_state:
            api_key_kwargs["value"] = api_key_val if api_key_val else ""
        api_key = st.text_input(**api_key_kwargs)
        
        # Advanced Settings
        with st.expander(t("advanced_settings")):
            sep_option = st.selectbox(
                t("sep_option"), 
                options=["_", " / ", "|"], 
                index=1, 
                key="sep_option",
                help=t("sep_help")
            )
            
            # Auto-populate if suggestion exists (handled via session state in app.py mostly, 
            # but we can set defaults here if key not present)
            
            # CHECK FOR PENDING SYNC FROM INTERACTIVE SELECTOR
            if 'pending_header_sync' in st.session_state:
                st.session_state['header_rows_input'] = st.session_state.pop('pending_header_sync')
            if 'pending_data_row_sync' in st.session_state:
                st.session_state['data_row_input'] = st.session_state.pop('pending_data_row_sync')
            
            header_rows_kwargs = {
                "label": t("header_rows_input"),
                "placeholder": "e.g., 0,1",
                "key": "header_rows_input",
                "help": t("header_help")
            }
            if "header_rows_input" not in st.session_state:
                header_rows_kwargs["value"] = ""
            header_rows_input = st.text_input(**header_rows_kwargs)

            data_row_kwargs = {
                "label": t("data_row_input"),
                "min_value": 0,
                "key": "data_row_input",
                "help": t("data_help")
            }
            if "data_row_input" not in st.session_state:
                data_row_kwargs["value"] = 1
            data_row_input = st.number_input(**data_row_kwargs)
            
        settings = {
            "sep_option": sep_option,
            "header_rows_input": header_rows_input,
            "data_row_input": data_row_input
        }
        
        st.markdown("---")
        st.markdown(f"**AI Excel Cleaner**\n\n{t('footer')}")
        
        return api_key, settings

def render_interactive_structure_selector(df, key_prefix="default"):
    """
    Renders an interactive dataframe selector for defining structure.
    New interaction mode: Four separate selection modes (Header Rows, Data Start, Data End, Column End)
    Returns: header_rows (list), data_start_row (int), key_columns (list), data_end_row (int or None), data_end_col (int or None)
    """
    st.markdown(f"### {t('structure_definition')}")
    
    col_controls, col_preview = st.columns([1, 2])
    
    # Define state keys with prefix
    header_key = f"{key_prefix}_header_rows"
    data_row_key = f"{key_prefix}_data_start_row"
    key_cols_key = f"{key_prefix}_key_columns"
    data_end_row_key = f"{key_prefix}_data_end_row"
    data_end_col_key = f"{key_prefix}_data_end_col"
    select_mode_key = f"{key_prefix}_select_mode"
    
    # Ensure state exists
    if header_key not in st.session_state:
        st.session_state[header_key] = [1] # Default to row 1 as header
    if data_row_key not in st.session_state:
        st.session_state[data_row_key] = 2 # Default to row 2 as data start
    if key_cols_key not in st.session_state:
        st.session_state[key_cols_key] = []
    if data_end_row_key not in st.session_state:
        st.session_state[data_end_row_key] = None # Default to None (no limit)
    if data_end_col_key not in st.session_state:
        st.session_state[data_end_col_key] = None # Default to None (no limit)
    if select_mode_key not in st.session_state:
        st.session_state[select_mode_key] = "header" # Default mode: select header rows
    
    # Get current selection mode
    current_mode = st.session_state[select_mode_key]
    
    # --- PRE-PROCESS SELECTION ---
    # Check all possible widget keys based on current mode
    widget_keys = {
        "header": f"{key_prefix}_selector_header",
        "data_start": f"{key_prefix}_selector_row",
        "data_end": f"{key_prefix}_selector_row",
        "col_end": f"{key_prefix}_selector_col_end",
        "key_cols": f"{key_prefix}_selector_key_cols",
    }
    
    widget_key = widget_keys.get(current_mode, f"{key_prefix}_selector_default")
    
    if widget_key in st.session_state:
        selection = st.session_state[widget_key]
        # Debug: show selection structure (using st.write instead of st.sidebar)
        if selection and "selection" in selection:
            
            # Handle based on current mode
            if current_mode == "header" and "rows" in selection.selection:
                # Header mode: multi-row selection
                selected_indices_0_based = selection.selection.rows
                selected_rows_1_based = [i + 1 for i in selected_indices_0_based]
                if selected_rows_1_based:
                    st.session_state[header_key] = sorted(selected_rows_1_based)
                    # Auto-update data start row
                    st.session_state[data_row_key] = max(selected_rows_1_based) + 1
                    
            elif current_mode == "data_start" and "rows" in selection.selection:
                # Data start mode: single row selection
                selected_indices = selection.selection.rows
                if selected_indices:
                    # Take the first selected row as data start
                    st.session_state[data_row_key] = selected_indices[0] + 1
                    
            elif current_mode == "data_end" and "rows" in selection.selection:
                # Data end mode: single row selection
                selected_indices = selection.selection.rows
                if selected_indices:
                    # Take the first selected row as data end
                    st.session_state[data_end_row_key] = selected_indices[0] + 1
                    
            elif current_mode == "col_end":
                # Column end mode: single column selection
                # Streamlit returns column names (which we set as '1', '2', '3', etc.)
                selected_col_names = selection.selection.get('columns', [])

                if selected_col_names:
                    # The column name is already the 1-based index (e.g., '3' means column 3)
                    try:
                        col_idx = int(selected_col_names[0])  # Already 1-based
                        st.session_state[data_end_col_key] = col_idx
                    except:
                        pass
                    
            elif current_mode == "key_cols":
                # Key columns mode: multi-column selection
                # Streamlit returns column names (which we set as '1', '2', '3', etc.)
                selected_col_names = selection.selection.get('columns', [])

                if selected_col_names:
                    key_columns_indices = []
                    for col_name in selected_col_names:
                        try:
                            # Convert 1-based display name to 0-based index
                            idx = int(col_name) - 1
                            key_columns_indices.append(idx)
                        except:
                            pass
                    if key_columns_indices:
                        st.session_state[key_cols_key] = key_columns_indices
    
    with col_controls:
        st.markdown(f"**{t('select_mode_title')}**")
        
        # Simple box-style buttons - vertically stacked, same size
        buttons_config = [
            ("header", t("btn_header_rows"), t("btn_header_rows_desc")),
            ("data_start", t("btn_data_start"), t("btn_data_start_desc")),
            ("data_end", t("btn_data_end"), t("btn_data_end_desc")),
            ("col_end", t("btn_col_end"), t("btn_col_end_desc")),
            ("key_cols", t("btn_key_cols"), t("btn_key_cols_desc")),
        ]
        
        for mode, label, desc in buttons_config:
            is_active = current_mode == mode
            
            # Create a container for each button row
            btn_container = st.container()
            with btn_container:
                # Use columns to create a box-like layout
                c1, c2 = st.columns([1, 3])
                
                with c1:
                    # Simple checkbox-style indicator
                    if is_active:
                        st.markdown("☑️")
                    else:
                        st.markdown("⬜")
                
                with c2:
                    # Simple button
                    btn_label = f"**{label}**" if is_active else label
                    if st.button(
                        btn_label,
                        use_container_width=True,
                        key=f"{key_prefix}_btn_{mode}"
                    ):
                        st.session_state[select_mode_key] = mode
                        st.rerun()
            
            # Description below
            st.caption(f"  {desc}")
            st.markdown("")  # Small spacing
        
        # Show current mode info
        st.markdown("---")
        mode_texts = {
            "header": t("mode_header"),
            "data_start": t("mode_data_start"),
            "data_end": t("mode_data_end"),
            "col_end": t("mode_col_end"),
            "key_cols": t("mode_key_cols")
        }
        st.info(f"**{t('current_mode')}:** {mode_texts.get(current_mode, '')}")
        
        # Display current selections
        st.markdown("---")
        st.markdown(f"**{t('structure_settings')}**")
        st.write(f"📌 {t('selected_headers')}: {sorted(st.session_state[header_key])}")
        st.write(f"📌 {t('data_row_input')}: {st.session_state[data_row_key]}")
        
        data_end_display = st.session_state[data_end_row_key] if st.session_state[data_end_row_key] else "未设置"
        col_end_display = st.session_state[data_end_col_key] if st.session_state[data_end_col_key] else "未设置"
        # Convert 0-based key column indices to 1-based for display
        if st.session_state[key_cols_key]:
            key_cols_display = [i + 1 for i in st.session_state[key_cols_key]]
        else:
            key_cols_display = "未设置"
        st.write(f"📌 {t('data_end_row_input')}: {data_end_display}")
        st.write(f"📌 {t('data_end_col_input')}: {col_end_display}")
        st.write(f"📌 {t('selected_key_columns')}: {key_cols_display}")
        
        # Manual input for data end row (when table is too large)
        if current_mode == "data_end":
            st.markdown("---")
            st.caption(t("manual_input"))
            manual_end_row = st.number_input(
                t("manual_end_row"),
                min_value=0,
                value=st.session_state[data_end_row_key] if st.session_state[data_end_row_key] else 0,
                key=f"{key_prefix}_manual_end_row"
            )
            if manual_end_row > 0:
                st.session_state[data_end_row_key] = manual_end_row
        
        # Manual input for data end column
        if current_mode == "col_end":
            st.markdown("---")
            st.caption(t("manual_input"))
            manual_end_col = st.number_input(
                t("manual_end_col"),
                min_value=0,
                value=st.session_state[data_end_col_key] if st.session_state[data_end_col_key] else 0,
                key=f"{key_prefix}_manual_end_col"
            )
            if manual_end_col > 0:
                st.session_state[data_end_col_key] = manual_end_col
        
        # Clear buttons
        st.markdown("---")
        if st.button(t("clear_selection"), use_container_width=True, key=f"{key_prefix}_clear_btn"):
            st.session_state[header_key] = [1]
            st.session_state[data_row_key] = 2
            st.session_state[data_end_row_key] = None
            st.session_state[data_end_col_key] = None
            st.session_state[key_cols_key] = []
            st.rerun()
            
    with col_preview:
        # Show full dataframe without row limit for scrolling
        display_df = df.copy()
        display_df.index = display_df.index + 1  # Row index 1-based
        # Rename columns to 1-based indices for display
        display_df.columns = [str(i + 1) for i in range(len(df.columns))]
        
        # Dynamic styling based on current mode and selections
        def get_grid_styles(data):
            rows, cols = data.shape
            style_matrix = np.full((rows, cols), '', dtype=object)
            
            headers = set(st.session_state[header_key])
            data_start = st.session_state[data_row_key]
            data_end = st.session_state[data_end_row_key]
            col_end = st.session_state[data_end_col_key]
            
            for i in range(rows):
                idx = i + 1  # 1-based row index
                
                # Header rows - always yellow
                if idx in headers:
                    style_matrix[i, :] = 'background-color: #fff3cd; color: #856404; font-weight: bold'
                # Data start row - green
                elif idx == data_start:
                    style_matrix[i, :] = 'background-color: #d4edda; color: #155724; font-weight: bold'
                # Data end row - blue
                elif data_end and idx == data_end:
                    style_matrix[i, :] = 'background-color: #cce5ff; color: #004085; font-weight: bold'
                # Rows between data start and end - light green
                elif data_end and data_start < idx < data_end:
                    style_matrix[i, :] = 'background-color: #f0f9f4'
                # Rows before data start (noise) - light red
                elif idx < data_start:
                    style_matrix[i, :] = 'background-color: #f8d7da; opacity: 0.6'
            
            # Column end highlighting
            if col_end:
                for j in range(cols):
                    col_idx = j + 1  # 1-based column index
                    if col_idx == col_end:
                        style_matrix[:, j] += '; border-right: 3px solid #004085'
                    elif col_idx > col_end:
                        style_matrix[:, j] += '; opacity: 0.3'
            
            return style_matrix

        styled_df = display_df.style.apply(get_grid_styles, axis=None)
        
        # Interactive Dataframe with dynamic selection mode
        # Use different widget keys for different modes to avoid selection conflicts
        if current_mode in ["header"]:
            selection_mode = ["multi-row"]
            widget_key = f"{key_prefix}_selector_header"
        elif current_mode in ["data_start", "data_end"]:
            selection_mode = ["single-row"]
            widget_key = f"{key_prefix}_selector_row"
        elif current_mode == "col_end":
            selection_mode = ["single-column"]
            widget_key = f"{key_prefix}_selector_col_end"
        elif current_mode == "key_cols":
            selection_mode = ["multi-column"]
            widget_key = f"{key_prefix}_selector_key_cols"
        else:
            selection_mode = ["multi-row"]
            widget_key = f"{key_prefix}_selector_default"
        
        selection = st.dataframe(
            styled_df,
            on_select="rerun",
            selection_mode=selection_mode,
            use_container_width=True,
            height=600,
            key=widget_key
        )

    # Return values from state (convert 1-based to 0-based for internal processing)
    internal_header_rows = [r - 1 for r in st.session_state[header_key]]
    internal_data_start_row = st.session_state[data_row_key] - 1
    internal_key_columns = st.session_state[key_cols_key]
    internal_data_end_row = st.session_state[data_end_row_key] - 1 if st.session_state[data_end_row_key] is not None else None
    internal_data_end_col = st.session_state[data_end_col_key] - 1 if st.session_state[data_end_col_key] is not None else None
    
    return internal_header_rows, internal_data_start_row, internal_key_columns, internal_data_end_row, internal_data_end_col

def highlight_header_rows(df, header_rows):
    """Highlights the detected header rows in yellow."""
    if not header_rows:
        return df.style
    
    def highlight_rows(row):
        # Check if the row index is in the header_rows list
        if row.name in header_rows:
            return ['background-color: #ffffcc'] * len(row)
        return [''] * len(row)
    
    return df.style.apply(highlight_rows, axis=1)

def render_analysis_status(header_rows, data_start_row):
    """Renders a success message with the detected structure info."""
    st.markdown(f"""
    <div class="status-card status-card-success">
        <div class="status-header">
            <div class="status-icon">✓</div>
            <span class="status-title">{t('analysis_success')}</span>
        </div>
        <div class="status-content">
            • <strong>{t('detected_headers')}</strong> {header_rows}<br>
            • <strong>{t('detected_data_start')}</strong> {data_start_row}
        </div>
        <div class="status-footer">
            {t('analysis_tip')}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_results(cleaned_data, raw_data, structure_info=None):
    st.markdown("---")
    
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        with st.container(border=True):
            st.markdown(f"### {t('preview_raw')}")
            if structure_info and 'header_rows' in structure_info:
                st.dataframe(highlight_header_rows(raw_data, structure_info['header_rows']), height=400, use_container_width=True)
            else:
                st.dataframe(raw_data, height=400, use_container_width=True)
        
    with col_res2:
        with st.container(border=True):
            st.markdown(f"### {t('preview_clean')}")
            st.dataframe(cleaned_data, height=400, use_container_width=True)

    # Download Section - Replaced <br> with CSS class
    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    
    col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
    with col_dl2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            cleaned_data.to_excel(writer, index=False)
        
        st.download_button(
            label=t("download_btn"),
            data=buffer,
            file_name="cleaned_data.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )