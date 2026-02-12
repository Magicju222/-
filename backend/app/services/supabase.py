from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()

# Singleton pattern for Supabase client
_supabase_client = None

def get_supabase() -> Client:
    """Get Supabase client with service role key (singleton pattern)."""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_SERVICE_KEY
            )
        except Exception as e:
            print(f"Error connecting to Supabase: {e}")
            raise e
    
    return _supabase_client
