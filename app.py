import streamlit as st
import pandas as pd
from cleaner import ExcelCleaner
from i18n import t
import ui
import auth
import services
import time
from admin import show_admin_panel, check_admin_access

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
# Track admin panel visibility
if 'show_admin_panel' not in st.session_state:
    st.session_state.show_admin_panel = False

# Load CSS
ui.load_css()

# Callback to handle file upload
def handle_file_upload():
    """Callback to handle file upload"""
    # Reset states when new file is uploaded
    st.session_state.cleaned_data = None
    st.session_state.raw_preview = None
    # Clean up all manual structure states
    keys_to_remove = [k for k in st.session_state.keys() if 'header_rows' in k or 'data_start_row' in k or 'key_columns' in k or 'selected_sheets' in k or 'preview_df_' in k]
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

# Initialize Services and Config
supabase = auth.init_supabase()
config_service = services.ConfigService(supabase) if supabase else None
log_service = services.LogService(supabase) if supabase else None

# Load System Config with caching to improve performance
@st.cache_data(ttl=60)  # Cache for 1 minute (reduced for faster sync)
def get_cached_config(_service):
    if _service:
        return _service.get_system_config()
    return {}

# Initialize system config in session state
if 'system_config' not in st.session_state:
    st.session_state.system_config = get_cached_config(config_service)

# Track config version for detecting updates from other sessions
if 'config_version' not in st.session_state:
    st.session_state.config_version = 0

# Check if config was updated from admin panel (via config_last_updated timestamp)
config_updated = False
if 'config_last_updated' in st.session_state:
    last_update = st.session_state.config_last_updated
    if 'last_seen_config_update' not in st.session_state:
        st.session_state.last_seen_config_update = last_update
        config_updated = True
    elif st.session_state.last_seen_config_update != last_update:
        st.session_state.last_seen_config_update = last_update
        config_updated = True

# Refresh config if needed (either not loaded or was updated)
if config_updated or not st.session_state.system_config:
    with st.spinner("🔄 正在同步最新配置..."):
        fresh_config = get_cached_config(config_service)
        if fresh_config:
            st.session_state.system_config = fresh_config
            st.session_state.config_version += 1
        else:
            st.error("❌ 配置同步失败，请刷新页面重试")

system_config = st.session_state.system_config

# --- Cached Helper Functions ---
@st.cache_data(show_spinner=False)
def cached_get_sheet_names(file_bytes, file_name):
    """Cache sheet names based on file content and name."""
    import io
    cleaner = ExcelCleaner()
    # Use a dummy file-like object since we pass bytes
    file_io = io.BytesIO(file_bytes)
    file_io.name = file_name
    return cleaner.get_sheet_names(file_io)

@st.cache_data(show_spinner=False)
def cached_load_preview(file_bytes, file_name, sheet_name):
    """Cache the first 100 rows of a sheet."""
    import io
    cleaner = ExcelCleaner()
    file_io = io.BytesIO(file_bytes)
    file_io.name = file_name
    full_df = cleaner.load_and_fill_merged_cells(file_io, sheet_name=sheet_name)
    preview_df = full_df.head(100).fillna("").astype(str)
    
    # Explicitly clear memory
    del full_df
    import gc
    gc.collect()
    
    return preview_df

# Check Maintenance Mode
if system_config.get("MAINTENANCE_MODE") == "true":
    user_profile = st.session_state.get('user_profile') or {}
    if user_profile.get('role') not in ('admin', 'super_admin'):
        st.error("⚠️ 系统正在维护中，请稍后再试。")
        st.stop()

# Get User Profile
user_profile = st.session_state.get('user_profile') or {}

# If user is logged in but profile is empty or has no role, reload it from database
if st.session_state.get('user') and (not user_profile or not user_profile.get('role')):
    supabase = auth.init_supabase()
    if supabase:
        user_service = services.UserService(supabase)
        profile = user_service.get_profile(st.session_state.user.id)
        if profile:
            st.session_state.user_profile = profile
            user_profile = profile

is_admin = user_profile.get('role') in ('admin', 'super_admin')

# Show System Notice if configured
system_notice = system_config.get("SYSTEM_NOTICE", "").strip()
if system_notice:
    # Track dismissed notices
    if 'dismissed_notices' not in st.session_state:
        st.session_state.dismissed_notices = set()

    # Create a hash of the notice to track if it's been dismissed
    import hashlib
    notice_hash = hashlib.md5(system_notice.encode()).hexdigest()[:8]

    if notice_hash not in st.session_state.dismissed_notices:
        with st.container():
            col1, col2 = st.columns([10, 1])
            with col1:
                st.info(f"📢 系统公告: {system_notice}", icon="ℹ️")
            with col2:
                if st.button("✕", key=f"dismiss_notice_{notice_hash}"):
                    st.session_state.dismissed_notices.add(notice_hash)
                    st.rerun()

# Show Admin Panel if requested
if st.session_state.get('show_admin_panel', False):
    if check_admin_access():
        # Add back button
        if st.button("← 返回主页面"):
            st.session_state.show_admin_panel = False
            st.rerun()
        
        # Show admin panel
        show_admin_panel()
        
        # Stop here to not show main content
        st.stop()
    else:
        st.error("⛔ 访问被拒绝：需要管理员权限")
        st.session_state.show_admin_panel = False

# Render Layout - Only if not in admin panel
api_key, settings = ui.render_sidebar()

# Admin Panel Button (only for admins)
if is_admin:
    with st.sidebar:
        st.divider()
        if st.button("🔧 管理面板", use_container_width=True):
            st.session_state.show_admin_panel = True
            st.rerun()

# Logout Button in Sidebar
with st.sidebar:
    st.divider()
    if st.button("🚪 Logout"):
        auth.logout()

# Only show navbar and hero if not in admin panel
if not st.session_state.get('show_admin_panel', False):
    ui.render_navbar()
    ui.render_hero()

# Main Controller Logic - Only show if not in admin panel
if not st.session_state.get('show_admin_panel', False):
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
            # Check File Size Limit
            max_size_mb = int(system_config.get("MAX_FILE_SIZE_MB", 50))
            if uploaded_file.size > max_size_mb * 1024 * 1024:
                st.error(f"文件大小超过限制 ({max_size_mb}MB)。")
            else:
                try:
                    cleaner = ExcelCleaner()
                
                    # 1. Get Sheet Names
                    # Read file as bytes once for caching
                    file_bytes = uploaded_file.getvalue()
                    sheet_names = cached_get_sheet_names(file_bytes, uploaded_file.name)
                    
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
                                # Load specific sheet data preview using CACHE
                                preview_df = cached_load_preview(file_bytes, uploaded_file.name, sheet)
                                    
                                # Render Selector
                                # Use sheet name as key prefix for isolation
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
                                    start_time = time.time()
                                    try:
                                        result = cleaner.clean_data(
                                            uploaded_file,
                                            header_rows=config["header_rows"],
                                            data_start_row=config["data_start_row"],
                                            key_columns=config["key_columns"],
                                            separator=sep,
                                            sheet_name=sheet
                                        )
                                        processing_time_ms = int((time.time() - start_time) * 1000)
                                        
                                        cleaned_results[sheet] = result['cleaned_df']
                                        
                                        # Log Success
                                        if log_service and st.session_state.user:
                                            log_service.log_cleaning_task(
                                                user_id=st.session_state.user.id,
                                                file_name=uploaded_file.name,
                                                file_size=uploaded_file.size,
                                                row_count=len(result['cleaned_df']),
                                                processing_time_ms=processing_time_ms,
                                                status='success'
                                            )
                                            
                                    except Exception as e:
                                        # Log Failure
                                        if log_service and st.session_state.user:
                                            log_service.log_cleaning_task(
                                                user_id=st.session_state.user.id,
                                                file_name=uploaded_file.name,
                                                file_size=uploaded_file.size,
                                                status='failed',
                                                error_message=str(e)
                                            )
                                        raise e
                                    
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