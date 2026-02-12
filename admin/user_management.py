"""
User Management Module
Handles user listing, search, ban/unban operations
"""

import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from .admin_api import get_admin_api

USERS_CACHE_TTL = 30  # seconds


@st.cache_data(ttl=USERS_CACHE_TTL, show_spinner=False)
def get_cached_users(api_url: str, limit: int = 1000) -> List[Dict]:
    """Cached users fetch to avoid repeated API calls"""
    from .admin_api import AdminAPI
    api = AdminAPI(api_url)
    return api.get_users(limit=limit)


def convert_to_json_serializable(obj):
    """Convert object to JSON serializable format"""
    if obj is None:
        return {}
    if hasattr(obj, 'to_dict'):
        obj = obj.to_dict()
    
    def default_handler(o):
        if isinstance(o, (datetime, pd.Timestamp)):
            return o.isoformat()
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if pd.isna(o):
            return None
        return str(o)
    
    return json.loads(json.dumps(obj, default=default_handler))

def show_user_management():
    """Display user management interface"""
    st.header("👥 用户管理")
    
    # Get admin API client
    api = get_admin_api()
    
    # Load users with caching
    users = get_cached_users(api.base_url, limit=1000)
    
    if not users:
        st.info("暂无用户数据")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(users)
    
    # User registration trend chart
    show_registration_trend(df)
    
    st.markdown("---")
    
    # Search and filter section
    st.subheader("筛选条件")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 搜索用户", placeholder="输入邮箱或用户ID")
    
    with col2:
        role_filter = st.selectbox(
            "角色筛选",
            ["全部", "user", "admin", "super_admin"]
        )
    
    with col3:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "active", "banned"]
        )
    
    # Apply filters
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False))
        df = df[mask.any(axis=1)]
    
    if role_filter != "全部" and 'role' in df.columns:
        df = df[df['role'] == role_filter]
    
    if status_filter != "全部" and 'status' in df.columns:
        df = df[df['status'] == status_filter]
    
    # Display summary
    st.markdown(f"**共找到 {len(df)} 位用户**")
    
    # Display users table with selection
    if len(df) > 0:
        # Prepare display DataFrame
        display_columns = ['id', 'email', 'role', 'status', 'created_at', 'last_login']
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            
            # Format dates
            if 'created_at' in display_df.columns:
                display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            if 'last_login' in display_df.columns:
                display_df['last_login'] = pd.to_datetime(display_df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Rename columns
            column_names = {
                'id': '用户ID',
                'email': '邮箱',
                'role': '角色',
                'status': '状态',
                'created_at': '注册时间',
                'last_login': '最后登录'
            }
            display_df.columns = [column_names.get(col, col) for col in display_df.columns]
            
            # Show table
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        
        # User actions section
        st.markdown("---")
        st.subheader("用户操作")
        
        # Single user operations
        col1, col2 = st.columns(2)
        
        with col1:
            selected_user = st.selectbox(
                "选择用户",
                options=df['id'].tolist(),
                format_func=lambda x: f"{x} ({df[df['id']==x]['email'].iloc[0] if 'email' in df.columns else 'Unknown'})"
            )
        
        with col2:
            action = st.selectbox(
                "操作",
                ["查看详情", "封禁用户", "解封用户", "修改角色"]
            )
        
        if st.button("执行操作", type="primary", key="single_action"):
            handle_user_action(api, selected_user, action, df)
        
        # Batch operations
        st.markdown("---")
        st.subheader("批量操作")
        
        # Multi-select for batch operations
        batch_user_ids = st.multiselect(
            "选择多个用户（通过用户ID）",
            options=df['id'].tolist(),
            format_func=lambda x: f"{x} ({df[df['id']==x]['email'].iloc[0] if 'email' in df.columns else 'Unknown'})"
        )
        
        if batch_user_ids:
            st.write(f"已选择 {len(batch_user_ids)} 位用户")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📛 批量封禁", type="secondary"):
                    batch_ban_users(api, batch_user_ids, df)
            
            with col2:
                if st.button("✅ 批量解封", type="secondary"):
                    batch_unban_users(api, batch_user_ids, df)
            
            with col3:
                batch_role = st.selectbox(
                    "批量修改角色为",
                    ["user", "admin", "super_admin"],
                    key="batch_role"
                )
                if st.button("📝 批量修改角色", type="secondary"):
                    batch_update_roles(api, batch_user_ids, batch_role, df)
    else:
        st.info("没有符合筛选条件的用户")

def show_registration_trend(df: pd.DataFrame):
    """Show user registration trend chart"""
    if 'created_at' not in df.columns or len(df) == 0:
        return
    
    st.subheader("📈 用户注册趋势")
    
    # Convert to datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Get registration counts by date (last 30 days)
    df['date'] = df['created_at'].dt.date
    last_30_days = datetime.now().date() - timedelta(days=30)
    
    daily_registrations = df[df['date'] >= last_30_days].groupby('date').size().reset_index(name='count')
    
    if len(daily_registrations) > 0:
        # Fill missing dates
        date_range = pd.date_range(start=last_30_days, end=datetime.now().date(), freq='D')
        daily_registrations = daily_registrations.set_index('date').reindex(date_range.date, fill_value=0).reset_index()
        daily_registrations.columns = ['date', 'count']
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_users = len(df)
            st.metric("总用户数", total_users)
        
        with col2:
            today = datetime.now().date()
            today_count = len(df[df['date'] == today])
            st.metric("今日注册", today_count)
        
        with col3:
            last_7_days = datetime.now().date() - timedelta(days=7)
            week_count = len(df[df['date'] >= last_7_days])
            st.metric("近7天注册", week_count)
        
        # Show chart
        st.line_chart(daily_registrations.set_index('date'))
    else:
        st.info("暂无注册数据")

def handle_user_action(api, user_id: str, action: str, df: pd.DataFrame):
    """Handle user actions"""
    user_info = df[df['id'] == user_id].iloc[0] if len(df[df['id'] == user_id]) > 0 else None
    
    if action == "查看详情":
        show_user_details(api, user_id)
    
    elif action == "封禁用户":
        if user_info is not None and user_info.get('status') == 'banned':
            st.warning("该用户已被封禁")
        else:
            show_ban_confirmation(api, user_id)
    
    elif action == "解封用户":
        if user_info is not None and user_info.get('status') != 'banned':
            st.warning("该用户未被封禁")
        else:
            show_unban_confirmation(api, user_id)
    
    elif action == "修改角色":
        show_role_editor(api, user_id, user_info)

def show_ban_confirmation(api, user_id: str):
    """Show ban confirmation dialog"""
    with st.expander("确认封禁用户", expanded=True):
        st.warning("确定要封禁该用户吗？封禁后用户将无法登录系统。")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认封禁", type="primary"):
                if api.ban_user(user_id):
                    st.success("✅ 用户已封禁")
                    st.rerun()
        with col2:
            if st.button("取消"):
                st.rerun()

def show_unban_confirmation(api, user_id: str):
    """Show unban confirmation dialog"""
    with st.expander("确认解封用户", expanded=True):
        st.info("确定要解封该用户吗？解封后用户将恢复正常访问。")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认解封", type="primary"):
                if api.unban_user(user_id):
                    st.success("✅ 用户已解封")
                    st.rerun()
        with col2:
            if st.button("取消"):
                st.rerun()

def show_user_details(api, user_id: str):
    """Show detailed user information"""
    user = api.get_user(user_id)
    
    if user:
        with st.expander("用户详情", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**基本信息**")
                st.write(f"用户ID: `{user.get('id', 'N/A')}`")
                st.write(f"邮箱: {user.get('email', 'N/A')}")
                st.write(f"角色: {user.get('role', 'N/A')}")
                status = user.get('status', 'N/A')
                status_color = "🟢" if status == 'active' else "🔴"
                st.write(f"状态: {status_color} {status}")
            
            with col2:
                st.markdown("**时间信息**")
                created_at = user.get('created_at', 'N/A')
                last_login = user.get('last_login', 'N/A')
                st.write(f"注册时间: {created_at}")
                st.write(f"最后登录: {last_login}")
            
            if 'metadata' in user and user['metadata']:
                st.markdown("**元数据**")
                try:
                    st.json(convert_to_json_serializable(user['metadata']))
                except Exception:
                    st.write(user['metadata'])
    else:
        st.error("无法获取用户详情")

def show_role_editor(api, user_id: str, user_info):
    """Show role editor dialog"""
    with st.expander("修改用户角色", expanded=True):
        current_role = user_info.get('role', 'user') if user_info is not None else 'user'
        
        st.write(f"当前角色: **{current_role}**")
        
        new_role = st.selectbox(
            "选择新角色",
            ["user", "admin", "super_admin"],
            index=["user", "admin", "super_admin"].index(current_role) if current_role in ["user", "admin", "super_admin"] else 0
        )
        
        if new_role != current_role:
            st.info(f"将把用户角色从 **{current_role}** 修改为 **{new_role}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认修改", type="primary"):
                    # Call API to update role
                    if update_user_role(api, user_id, new_role):
                        st.success(f"✅ 角色已修改为 {new_role}")
                        st.rerun()
            with col2:
                if st.button("取消"):
                    st.rerun()
        else:
            st.info("请选择不同的角色")

def update_user_role(api, user_id: str, new_role: str) -> bool:
    """Update user role via API"""
    try:
        # This would call the backend API to update role
        # For now, we'll use a direct Supabase update
        import os
        from supabase import create_client
        
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            st.error("缺少 Supabase 配置")
            return False
        
        supabase = create_client(url, key)
        
        # Update user profile role
        response = supabase.table("user_profiles").update({
            "role": new_role,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if response.data:
            return True
        else:
            st.error("更新角色失败")
            return False
            
    except Exception as e:
        st.error(f"更新角色时出错: {str(e)}")
        return False

def batch_ban_users(api, user_ids: List[str], df: pd.DataFrame):
    """Ban multiple users"""
    success_count = 0
    fail_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, user_id in enumerate(user_ids):
        status_text.text(f"正在封禁用户 {i+1}/{len(user_ids)}...")
        
        user_info = df[df['id'] == user_id].iloc[0] if len(df[df['id'] == user_id]) > 0 else None
        if user_info is not None and user_info.get('status') == 'banned':
            continue  # Skip already banned users
        
        if api.ban_user(user_id):
            success_count += 1
        else:
            fail_count += 1
        
        progress_bar.progress((i + 1) / len(user_ids))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        st.success(f"✅ 成功封禁 {success_count} 位用户")
    if fail_count > 0:
        st.error(f"❌ 封禁失败 {fail_count} 位用户")
    
    if success_count > 0:
        st.rerun()

def batch_unban_users(api, user_ids: List[str], df: pd.DataFrame):
    """Unban multiple users"""
    success_count = 0
    fail_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, user_id in enumerate(user_ids):
        status_text.text(f"正在解封用户 {i+1}/{len(user_ids)}...")
        
        user_info = df[df['id'] == user_id].iloc[0] if len(df[df['id'] == user_id]) > 0 else None
        if user_info is not None and user_info.get('status') != 'banned':
            continue  # Skip non-banned users
        
        if api.unban_user(user_id):
            success_count += 1
        else:
            fail_count += 1
        
        progress_bar.progress((i + 1) / len(user_ids))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        st.success(f"✅ 成功解封 {success_count} 位用户")
    if fail_count > 0:
        st.error(f"❌ 解封失败 {fail_count} 位用户")
    
    if success_count > 0:
        st.rerun()

def batch_update_roles(api, user_ids: List[str], new_role: str, df: pd.DataFrame):
    """Update roles for multiple users"""
    success_count = 0
    fail_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, user_id in enumerate(user_ids):
        status_text.text(f"正在修改用户 {i+1}/{len(user_ids)} 的角色...")
        
        if update_user_role(api, user_id, new_role):
            success_count += 1
        else:
            fail_count += 1
        
        progress_bar.progress((i + 1) / len(user_ids))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        st.success(f"✅ 成功修改 {success_count} 位用户的角色为 {new_role}")
    if fail_count > 0:
        st.error(f"❌ 修改失败 {fail_count} 位用户")
    
    if success_count > 0:
        st.rerun()
