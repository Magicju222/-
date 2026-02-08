import streamlit as st
import pandas as pd
from cleaner import ExcelCleaner
from i18n import t
import ui
import auth

# Page Config (Must be first)
st.set_page_config(
    page_title="AI Excel Cleaner",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Session State Initialization
if 'lang' not in st.session_state:
    st.session_state.lang = 'zh'
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'raw_preview' not in st.session_state:
    st.session_state.raw_preview = None
# Track uploaded file to detect changes
if 'last_uploaded_file_id' not in st.session_state:
    st.session_state.last_uploaded_file_id = None
# Track if user guide has been clicked
if 'guide_clicked' not in st.session_state:
    st.session_state.guide_clicked = False

# Load CSS
ui.load_css()

# Callback to handle file upload
def handle_file_upload():
    """Callback to handle file upload"""
    # Reset states when new file is uploaded
    st.session_state.cleaned_data = None
    st.session_state.raw_preview = None
    # Clean up all manual structure states
    keys_to_remove = [k for k in st.session_state.keys() if 'header_rows' in k or 'data_start_row' in k or 'key_columns' in k or 'selected_sheets' in k]
    for k in keys_to_remove:
        del st.session_state[k]
    # Clear caches
    if 'cached_raw_df' in st.session_state:
        del st.session_state.cached_raw_df
    if 'cached_sheet_names' in st.session_state:
        del st.session_state.cached_sheet_names

# Authentication Check
if not auth.check_auth():
    auth.show_login_page()
    st.stop()

# Render Layout
# We render sidebar first
api_key, settings = ui.render_sidebar()

# Logout Button in Sidebar
with st.sidebar:
    st.divider()
    if st.button("🚪 Logout"):
        auth.logout()

ui.render_navbar()
ui.render_hero()

# Main Controller Logic
main_col1, main_col2, main_col3 = st.columns([1, 3, 1])

with main_col2:
    # File Uploader Card
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Excel/CSV file", 
            type=['xlsx', 'xls', 'csv'], 
            label_visibility="collapsed",
            key="uploaded_file",
            on_change=handle_file_upload
        )

    if uploaded_file:
        try:
            cleaner = ExcelCleaner()
            
            # 1. Get Sheet Names
            if 'cached_sheet_names' not in st.session_state or st.session_state.get('cached_file_id') != uploaded_file.file_id:
                sheet_names = cleaner.get_sheet_names(uploaded_file)
                st.session_state.cached_sheet_names = sheet_names
                st.session_state.cached_file_id = uploaded_file.file_id
            else:
                sheet_names = st.session_state.cached_sheet_names
            
            # 2. Sheet Selection
            st.markdown(f"### {t('select_sheets')}")
            selected_sheets = st.multiselect(
                t("select_sheets"),
                options=sheet_names,
                default=sheet_names, # Default select all
                label_visibility="collapsed",
                key="selected_sheets_input"
            )
            
            if not selected_sheets:
                st.warning("Please select at least one sheet.")
            else:
                # 3. Tabbed Configuration
                st.markdown(f"### {t('sheet_config')}")
                tabs = st.tabs(selected_sheets)
                
                # Dictionary to store configs for each sheet
                sheet_configs = {}
                
                for i, sheet in enumerate(selected_sheets):
                    with tabs[i]:
                        # Load specific sheet data
                        # We cache per sheet to avoid reload on interaction
                        sheet_cache_key = f"cached_df_{sheet}_{uploaded_file.file_id}"
                        if sheet_cache_key not in st.session_state:
                            raw_df = cleaner.load_and_fill_merged_cells(uploaded_file, sheet_name=sheet)
                            st.session_state[sheet_cache_key] = raw_df
                        else:
                            raw_df = st.session_state[sheet_cache_key]
                            
                        # Render Selector
                        # Use sheet name as key prefix for isolation
                        preview_df = raw_df.head(1000).fillna("").astype(str)
                        header_rows, data_start_row, key_columns = ui.render_interactive_structure_selector(
                            preview_df, 
                            key_prefix=f"sheet_{sheet}"
                        )
                        
                        sheet_configs[sheet] = {
                            "header_rows": header_rows,
                            "data_start_row": data_start_row,
                            "key_columns": key_columns
                        }
                
                # Action Button
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    start_btn = st.button(t("batch_clean_btn"), use_container_width=True)
                
                if start_btn:
                    # Progress Animation
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        status_text.text(t("processing"))
                        progress_bar.progress(10)
                        
                        sep = settings.get("sep_option", " / ")
                        
                        cleaned_results = {}
                        total_sheets = len(selected_sheets)
                        
                        for idx, sheet in enumerate(selected_sheets):
                            status_text.text(f"{t('cleaning')} - {sheet}")
                            
                            config = sheet_configs[sheet]
                            
                            # Clean Data
                            result = cleaner.clean_data(
                                uploaded_file,
                                header_rows=config["header_rows"],
                                data_start_row=config["data_start_row"],
                                key_columns=config["key_columns"],
                                separator=sep,
                                sheet_name=sheet
                            )
                            
                            cleaned_results[sheet] = result['cleaned_df']
                            
                            # Update progress
                            progress = int(10 + (idx + 1) / total_sheets * 80)
                            progress_bar.progress(progress)
                            
                        # Store results (Dictionary of DFs)
                        st.session_state.cleaned_data = cleaned_results
                        st.session_state.raw_preview = None # Not applicable for batch
                        
                        progress_bar.progress(100)
                        status_text.text(t("success"))
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        
        except Exception as e:
             st.error(f"Failed to load file: {e}")

# Render Results
if st.session_state.cleaned_data is not None:
    st.markdown("---")
    st.markdown(f"### {t('preview_clean')}")
    
    # Display results in tabs
    result_sheets = list(st.session_state.cleaned_data.keys())
    res_tabs = st.tabs(result_sheets)
    
    for i, sheet in enumerate(result_sheets):
        with res_tabs[i]:
            st.dataframe(st.session_state.cleaned_data[sheet], height=400, use_container_width=True)
            
    # Download All
    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
    with col_dl2:
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            for sheet, df in st.session_state.cleaned_data.items():
                # Sheet name length limit in Excel is 31 chars
                safe_sheet_name = sheet[:31]
                df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
        
        st.download_button(
            label=t("download_btn"),
            data=buffer,
            file_name="cleaned_batch_data.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
else:
    # Placeholder or Instructions when no data
    if not uploaded_file:
        ui.render_no_file_instruction()