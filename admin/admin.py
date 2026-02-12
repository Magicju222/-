"""
Admin Panel Main Module
Provides the main admin interface with tab navigation
"""

import streamlit as st
from .user_management import show_user_management
from .log_viewer import show_log_viewer
from .analytics import show_analytics
from .system_config import show_system_config

def show_admin_panel():
    """Display the main admin panel with tabs"""
    
    # Admin panel header
    st.markdown("""
        <style>
        .admin-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        </style>
        <div class="admin-header">
            <h1 style="margin:0;">🔧 管理面板</h1>
            <p style="margin:0; opacity:0.9;">系统管理和数据分析中心</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different sections
    tabs = st.tabs([
        "👥 用户管理",
        "📋 清洗日志", 
        "📊 数据分析",
        "⚙️ 系统配置"
    ])
    
    with tabs[0]:
        show_user_management()
    
    with tabs[1]:
        show_log_viewer()
    
    with tabs[2]:
        show_analytics()
    
    with tabs[3]:
        show_system_config()
    
    # Footer
    st.markdown("---")
    st.caption("AI Excel Cleaner Admin Panel v1.0")

def check_admin_access():
    """Check if current user has admin access"""
    if 'user_profile' not in st.session_state:
        return False
    
    user_profile = st.session_state.user_profile
    role = user_profile.get('role', 'user')
    
    return role in ['admin', 'super_admin']

def admin_access_required(func):
    """Decorator to require admin access"""
    def wrapper(*args, **kwargs):
        if not check_admin_access():
            st.error("⛔ 访问被拒绝：需要管理员权限")
            st.info("请联系系统管理员获取访问权限")
            return
        return func(*args, **kwargs)
    return wrapper
