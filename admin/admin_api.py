"""
Admin API Client
Handles all backend API calls for admin operations
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any, List
import os

# API Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1_STR = "/api/v1"

class AdminAPI:
    """Client for admin backend API"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or API_BASE_URL
        self.api_url = f"{self.base_url}{API_V1_STR}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token"""
        headers = {"Content-Type": "application/json"}
        
        # Get JWT token from session state
        if "user" in st.session_state and st.session_state.user:
            # Get the access token from Supabase session
            # Note: This assumes the token is stored in session
            token = getattr(st.session_state, 'access_token', None)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response"""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("认证失败：请重新登录")
            return None
        elif response.status_code == 403:
            st.error("权限不足：需要管理员权限")
            return None
        else:
            st.error(f"API 错误: {response.status_code} - {response.text}")
            return None
    
    # User Management APIs
    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get list of users"""
        try:
            response = requests.get(
                f"{self.api_url}/users/",
                headers=self._get_headers(),
                params={"skip": skip, "limit": limit}
            )
            result = self._handle_response(response)
            return result if result else []
        except Exception as e:
            st.error(f"获取用户列表失败: {str(e)}")
            return []
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get specific user details"""
        try:
            response = requests.get(
                f"{self.api_url}/users/{user_id}",
                headers=self._get_headers()
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"获取用户详情失败: {str(e)}")
            return None
    
    def ban_user(self, user_id: str) -> bool:
        """Ban a user"""
        try:
            response = requests.post(
                f"{self.api_url}/users/{user_id}/ban",
                headers=self._get_headers()
            )
            result = self._handle_response(response)
            return result is not None
        except Exception as e:
            st.error(f"封禁用户失败: {str(e)}")
            return False
    
    def unban_user(self, user_id: str) -> bool:
        """Unban a user"""
        try:
            response = requests.post(
                f"{self.api_url}/users/{user_id}/unban",
                headers=self._get_headers()
            )
            result = self._handle_response(response)
            return result is not None
        except Exception as e:
            st.error(f"解封用户失败: {str(e)}")
            return False
    
    # Logs APIs
    def get_logs(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get cleaning logs"""
        try:
            response = requests.get(
                f"{self.api_url}/logs/",
                headers=self._get_headers(),
                params={"skip": skip, "limit": limit}
            )
            result = self._handle_response(response)
            return result if result else []
        except Exception as e:
            st.error(f"获取日志失败: {str(e)}")
            return []
    
    def get_stats(self) -> Optional[Dict]:
        """Get system statistics"""
        try:
            response = requests.get(
                f"{self.api_url}/logs/stats",
                headers=self._get_headers()
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"获取统计数据失败: {str(e)}")
            return None
    
    # Config APIs
    def get_config(self) -> List[Dict]:
        """Get system configuration"""
        try:
            response = requests.get(
                f"{self.api_url}/config/",
                headers=self._get_headers()
            )
            result = self._handle_response(response)
            return result if result else []
        except Exception as e:
            st.error(f"获取配置失败: {str(e)}")
            return []
    
    def update_config(self, key: str, value: str) -> Optional[List[Dict]]:
        """Update system configuration and return updated config"""
        try:
            response = requests.put(
                f"{self.api_url}/config/",
                headers=self._get_headers(),
                json={"key": key, "value": value}
            )
            result = self._handle_response(response)
            return result if result else None
        except Exception as e:
            st.error(f"更新配置失败: {str(e)}")
            return None

# Singleton instance
@st.cache_resource
def get_admin_api() -> AdminAPI:
    """Get Admin API client instance"""
    return AdminAPI()
