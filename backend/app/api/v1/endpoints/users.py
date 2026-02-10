from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from backend.app.api import deps
from supabase import Client

router = APIRouter()

@router.get("/", response_model=Any)
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Retrieve users (Admin only).
    """
    # Join with auth.users is hard via Supabase API directly if we want email.
    # Usually we query user_profiles and maybe auth.users if we have permissions.
    # For now, let's query user_profiles which has nickname, role, status.
    # Note: email is in auth.users, which is protected. 
    # The Service Role Key allows access to auth.admin methods.
    
    # Using Service Role for listing users is often easier if we have it, 
    # but here we are using the client initialized with what? 
    # If SUPABASE_KEY in config is the SERVICE_ROLE_KEY, we are god.
    # If it's ANON_KEY, we are limited by RLS.
    # Since this is an Admin API, we likely assume the backend runs with SERVICE_ROLE_KEY
    # OR the RLS policies allow admins to see everything.
    # Our RLS says: "Admins can view all profiles". So ANON_KEY + Admin User Token works.
    
    response = db.table("user_profiles").select("*").range(skip, skip + limit - 1).execute()
    return response.data

@router.get("/{user_id}", response_model=Any)
def read_user_by_id(
    user_id: str,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    response = db.table("user_profiles").select("*").eq("id", user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return response.data

@router.post("/{user_id}/ban", response_model=Any)
def ban_user(
    user_id: str,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    response = db.table("user_profiles").update({"status": "banned"}).eq("id", user_id).execute()
    return response.data

@router.post("/{user_id}/unban", response_model=Any)
def unban_user(
    user_id: str,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    response = db.table("user_profiles").update({"status": "active"}).eq("id", user_id).execute()
    return response.data
