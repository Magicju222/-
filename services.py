import os
import streamlit as st
from supabase import Client
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# Re-use the init_supabase from auth.py or move it here.
# For now, let's assume auth.py has the client initialization logic, 
# but we need a client instance here. 
# Ideally, we pass the client or get it from session state.

class BaseService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

class UserService(BaseService):
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile by ID."""
        try:
            response = self.supabase.table("user_profiles").select("*").eq("id", user_id).single().execute()
            return response.data
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def update_last_login(self, user_id: str):
        """Update the last_login_at timestamp."""
        try:
            self.supabase.table("user_profiles").update({
                "last_login_at": datetime.now().isoformat()
            }).eq("id", user_id).execute()
        except Exception as e:
            print(f"Error updating last login: {e}")

    def is_banned(self, user_id: str) -> bool:
        """Check if user is banned."""
        profile = self.get_profile(user_id)
        if profile and profile.get("status") == "banned":
            return True
        return False

class LogService(BaseService):
    def log_cleaning_task(self, 
                          user_id: str, 
                          file_name: str, 
                          file_size: int, 
                          status: str, 
                          row_count: int = 0, 
                          processing_time_ms: int = 0, 
                          error_message: str = None):
        """Log a cleaning task result."""
        try:
            data = {
                "user_id": user_id,
                "file_name": file_name,
                "file_size_bytes": file_size,
                "row_count": row_count,
                "processing_time_ms": processing_time_ms,
                "status": status,
                "error_message": error_message
            }
            self.supabase.table("cleaning_logs").insert(data).execute()
        except Exception as e:
            print(f"Error logging cleaning task: {e}")

class ConfigService(BaseService):
    def get_system_config(self) -> Dict[str, str]:
        """Fetch all system configurations as a key-value dictionary."""
        try:
            response = self.supabase.table("system_config").select("key, value").execute()
            config = {}
            if response.data:
                for item in response.data:
                    config[item["key"]] = item["value"]
            return config
        except Exception as e:
            print(f"Error fetching system config: {e}")
            return {}
