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
        
        # Inject CSS with dynamic content
        import time
        version = int(time.time())
        st.markdown(f"""
        <style id="custom-css-{version}">
            {css}
            
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

@st.fragment
def render_interactive_structure_selector(df, key_prefix="default"):
    """
    Renders an interactive dataframe selector for defining structure.
    Returns: header_rows (list), data_start_row (int)
    """
    st.markdown(f"### {t('structure_definition')}")
    st.info(t("structure_instruction"))
    
    col_controls, col_preview = st.columns([1, 2])
    
    # Define state keys with prefix
    header_key = f"{key_prefix}_header_rows"
    data_row_key = f"{key_prefix}_data_start_row"
    key_cols_key = f"{key_prefix}_key_columns"
    
    # Ensure state exists
    if header_key not in st.session_state:
        st.session_state[header_key] = [1] # Default to row 1 as header
    if data_row_key not in st.session_state:
        st.session_state[data_row_key] = 2 # Default to row 2 as data start
    if key_cols_key not in st.session_state:
        st.session_state[key_cols_key] = []
        
    # --- PRE-PROCESS SELECTION ---
    # To avoid StreamlitAPIException, we process the widget's selection state 
    # BEFORE rendering the widgets that depend on it.
    widget_key = f"{key_prefix}_structure_selector_widget"
    if widget_key in st.session_state:
        selection = st.session_state[widget_key]
        if selection and "selection" in selection:
            # 1. Handle Row Selection -> Update Headers and Data Start
            if "rows" in selection.selection:
                selected_indices_0_based = selection.selection.rows
                selected_rows_1_based = [i + 1 for i in selected_indices_0_based]
                
                if selected_rows_1_based and set(selected_rows_1_based) != set(st.session_state[header_key]):
                    st.session_state[header_key] = selected_rows_1_based
                    # Auto-infer data start row
                    st.session_state[data_row_key] = max(selected_rows_1_based) + 1

            # 2. Handle Column Selection -> Update Key Columns
            if "columns" in selection.selection:
                 selected_cols = selection.selection.columns
                 key_columns_indices = []
                 for col in selected_cols:
                     if col in df.columns:
                         idx = df.columns.get_loc(col)
                         if isinstance(idx, int):
                             key_columns_indices.append(idx)
                         continue
                     if isinstance(col, str) and col.isdigit():
                         try:
                             col_int = int(col)
                             if col_int in df.columns:
                                 idx = df.columns.get_loc(col_int)
                                 if isinstance(idx, int):
                                     key_columns_indices.append(idx)
                         except: pass
                 
                 if set(key_columns_indices) != set(st.session_state[key_cols_key]):
                     st.session_state[key_cols_key] = key_columns_indices
    
    with col_controls:
        st.markdown(f"**{t('structure_settings')}**")
        
        # Display selected header rows (Read-only view of selection)
        st.write(f"{t('selected_headers')}: {sorted(st.session_state[header_key])}")
        
        # Manual override for data start row
        # Directly use the state key for automatic sync without st.rerun()
        st.number_input(
            t("data_row_input"),
            min_value=1,
            key=data_row_key
        )
            
    with col_preview:
        # Optimization: Limit preview rows for the interactive selector to 50
        # This drastically reduces the browser's rendering load for styled tables
        display_df = df.head(50).copy()
        display_df.index = display_df.index + 1
        
        # EXTREME OPTIMIZATION: Matrix-based styling (axis=None)
        def get_grid_styles(data):
            rows, cols = data.shape
            style_matrix = np.full((rows, cols), '', dtype=object)
            
            headers = set(st.session_state[header_key])
            data_row = st.session_state[data_row_key]
            
            for i in range(rows):
                idx = i + 1 
                if idx in headers:
                    style_matrix[i, :] = 'background-color: #fff3cd'
                elif idx == data_row:
                    style_matrix[i, :] = 'background-color: #d4edda'
                elif idx < data_row:
                    style_matrix[i, :] = 'background-color: #f8d7da; opacity: 0.5'
            
            return style_matrix

        styled_df = display_df.style.apply(get_grid_styles, axis=None)
        
        # Interactive Dataframe
        selection = st.dataframe(
            styled_df,
            on_select="rerun",
            selection_mode=["multi-row", "multi-column"],
            use_container_width=True,
            height=600,
            key=f"{key_prefix}_structure_selector_widget"
        )
    
    with col_controls:
        st.markdown("---")
        st.markdown(f"**{t('key_columns_settings')}**")
        st.info(t("key_columns_help"))
        st.write(f"{t('selected_key_columns')}: {st.session_state[key_cols_key]}")

    # Return values from state
    internal_header_rows = [r - 1 for r in st.session_state[header_key]]
    internal_data_start_row = st.session_state[data_row_key] - 1
    internal_key_columns = st.session_state[key_cols_key]
    
    return internal_header_rows, internal_data_start_row, internal_key_columns

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