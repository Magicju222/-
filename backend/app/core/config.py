from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import Field, field_validator
import os

# Load environment variables from .env file
# Try to find .env in parent directory (project root)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Try default locations

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Excel Cleaner Admin API"
    
    # Supabase - Backend uses service role key for admin operations
    SUPABASE_URL: str = Field(..., min_length=10)
    SUPABASE_SERVICE_KEY: str = Field(..., min_length=20)
    
    # CORS配置 - 允许的源（生产环境必须限制）
    ALLOWED_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"
    
    # 环境模式
    ENVIRONMENT: str = "development"  # development, production
    
    # 安全配置
    MAX_FILE_SIZE_MB: int = Field(default=50, ge=1, le=500)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10)
    
    @field_validator('SUPABASE_URL')
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """验证Supabase URL格式"""
        if not v.startswith('https://'):
            raise ValueError('SUPABASE_URL must start with https://')
        if '.supabase.co' not in v:
            raise ValueError('SUPABASE_URL must be a valid Supabase URL')
        return v
    
    @field_validator('SUPABASE_SERVICE_KEY')
    @classmethod
    def validate_service_key(cls, v: str, info) -> str:
        """验证Service Key格式（JWT格式检查）"""
        if len(v) < 20:
            raise ValueError('SUPABASE_SERVICE_KEY is too short')
        # JWT格式基本检查（仅在非开发环境严格检查）
        values = info.data if hasattr(info, 'data') else {}
        env = values.get('ENVIRONMENT', 'development')
        if env != 'development':
            parts = v.split('.')
            if len(parts) != 3:
                raise ValueError('SUPABASE_SERVICE_KEY does not appear to be a valid JWT')
        return v
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证环境模式"""
        allowed = ['development', 'staging', 'production']
        if v.lower() not in allowed:
            raise ValueError(f'ENVIRONMENT must be one of: {allowed}')
        return v.lower()
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
