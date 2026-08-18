from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import logger
from typing import Optional


class SupabaseService:
    """
    Service wrapper for the official Supabase Python SDK Client.
    Maintains client access separate from SQLAlchemy.
    """
    _anon_client: Optional[Client] = None
    _service_client: Optional[Client] = None

    @classmethod
    def get_anon_client(cls) -> Client:
        """
        Returns a Supabase client configured with the public Anon Key.
        Safe for operations respecting Row Level Security (RLS).
        """
        if cls._anon_client is None:
            cls._anon_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        return cls._anon_client

    @classmethod
    def get_service_role_client(cls) -> Client:
        """
        Returns a Supabase client configured with the Service Role Key.
        WARNING: Server-side only! Never expose to frontend.
        """
        if cls._service_client is None:
            cls._service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        return cls._service_client


def check_supabase_client_init() -> bool:
    """
    Verifies that the Supabase Python SDK client can be initialized with valid configuration.
    """
    try:
        client = SupabaseService.get_anon_client()
        return client is not None
    except Exception as e:
        logger.warning(f"Supabase client initialization check failed: {e}")
        return False
