import logging
import os
from supabase import create_client, Client
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Single supabase client instance for the backend
_supabase: Client = None

def get_supabase_client() -> Client:
    global _supabase
    if _supabase is not None:
        return _supabase
    
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    
    if not url or not key:
        return None
        
    try:
        _supabase = create_client(url, key)
        return _supabase
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None

async def verify_supabase_token(id_token: str):
    """
    Verifies a Supabase access token (JWT) by calling the Supabase Auth API.
    Returns the user data if valid, or raises an exception.
    """
    client = get_supabase_client()
    if client is None:
        raise ValueError("Supabase is not configured on the backend.")

    try:
        # get_user verifies the token with the Supabase Auth server
        res = client.auth.get_user(id_token)
        if not res or not res.user:
            raise ValueError("Invalid or expired Supabase token.")
            
        user = res.user
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.user_metadata.get("full_name") or user.email,
        }
    except Exception as e:
        logger.error(f"Error verifying Supabase token: {str(e)}")
        raise ValueError(f"Supabase token verification failed: {str(e)}")
