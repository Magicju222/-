from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
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
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
