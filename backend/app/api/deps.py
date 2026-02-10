from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
from backend.app.services.supabase import get_supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db() -> Client:
    return get_supabase()

def get_current_user(token: str = Depends(oauth2_scheme), db: Client = Depends(get_db)):
    try:
        # Verify token with Supabase Auth
        user_response = db.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_admin(current_user = Depends(get_current_user), db: Client = Depends(get_db)):
    # Check if user is admin in user_profiles
    response = db.table("user_profiles").select("role").eq("id", current_user.id).single().execute()
    
    if not response.data:
        raise HTTPException(status_code=403, detail="User profile not found")
        
    role = response.data.get("role")
    if role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
