import streamlit as st
from supabase import create_client, Client
import os
from typing import Optional
import services

# Initialize Supabase client
# Uses st.secrets in production, or environment variables locally
@st.cache_resource
def init_supabase() -> Optional[Client]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # Try loading from streamlit secrets if env vars are missing
    if not url or not key:
        try:
            if not url:
                url = st.secrets["SUPABASE_URL"]
            if not key:
                key = st.secrets["SUPABASE_KEY"]
        except Exception:
            # Secrets not found or keys missing
            pass
    
    if not url or not key:
        return None
        
    return create_client(url, key)

def show_login_page():
    # CSS for centering and styling
    st.markdown("""
    <style>
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 45px;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Vertical spacer to push content to middle
    st.markdown("<div style='height: 10vh'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 AI Excel 清洗助手</h2>", unsafe_allow_html=True)
        
        # Container for the card effect
        with st.container(border=True):
            tab1, tab2 = st.tabs(["用户登录", "新用户注册"])
            
            supabase = init_supabase()
            
            if not supabase:
                st.error("系统配置错误：缺少 Supabase URL 或 Key。")
                return

            with tab1:
                with st.form("login_form"):
                    email = st.text_input("电子邮箱", key="login_email", placeholder="name@example.com")
                    password = st.text_input("登录密码", type="password", key="login_pass", placeholder="请输入密码")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    submit_button = st.form_submit_button("立即登录", type="primary", use_container_width=True)
                    
                    if submit_button:
                        with st.spinner("正在验证身份..."):
                            try:
                                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                                
                                # Check profile status
                                user_service = services.UserService(supabase)
                                profile = user_service.get_profile(response.user.id)
                                
                                if profile and profile.get('status') == 'banned':
                                     st.error("您的账号已被封禁，请联系管理员。")
                                     supabase.auth.sign_out()
                                else:
                                    # Update last login in background thread to avoid blocking
                                    import threading
                                    threading.Thread(
                                        target=user_service.update_last_login, 
                                        args=(response.user.id,),
                                        daemon=True
                                    ).start()
                                    
                                    st.session_state.user = response.user
                                    st.session_state.user_profile = profile
                                    
                                    st.success("登录成功！正在跳转...")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"登录失败: 账号或密码错误")

            with tab2:
                with st.form("register_form"):
                    new_email = st.text_input("电子邮箱", key="reg_email", placeholder="name@example.com")
                    new_password = st.text_input("设置密码", type="password", key="reg_pass", placeholder="请设置您的登录密码")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    register_button = st.form_submit_button("创建账号", use_container_width=True)
                    
                    if register_button:
                        try:
                            response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                            st.success("注册成功！请检查您的邮箱进行验证。")
                        except Exception as e:
                            st.error(f"注册失败: {str(e)}")

def check_auth():
    if "user" not in st.session_state:
        st.session_state.user = None
    
    # If user is logged in, ensure we have the profile (e.g. after refresh)
    if st.session_state.user and "user_profile" not in st.session_state:
        supabase = init_supabase()
        if supabase:
             user_service = services.UserService(supabase)
             profile = user_service.get_profile(st.session_state.user.id)
             st.session_state.user_profile = profile

    return st.session_state.user is not None

def logout():
    supabase = init_supabase()
    if supabase:
        supabase.auth.sign_out()
    st.session_state.user = None
    if "user_profile" in st.session_state:
        del st.session_state.user_profile
    st.rerun()
