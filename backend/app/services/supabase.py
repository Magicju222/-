from supabase import create_client, Client
from backend.app.core.config import get_settings

settings = get_settings()

def get_supabase() -> Client:
    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        raise e
