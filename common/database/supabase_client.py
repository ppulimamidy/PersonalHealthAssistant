"""
Supabase Client
Provides a singleton Supabase client for database operations
"""

from typing import Optional
from supabase import create_client, Client  # pylint: disable=no-name-in-module
from supabase.lib.client_options import (  # pylint: disable=no-name-in-module,import-error
    ClientOptions,
)

from common.config.settings import get_settings
from common.utils.logging import get_logger

logger = get_logger(__name__)

# Global Supabase client instance
_supabase_client: Optional[Client] = None  # pylint: disable=invalid-name


def get_supabase_client() -> Client:
    """
    Get Supabase client singleton

    Returns:
        Client: Supabase client instance

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    global _supabase_client  # pylint: disable=global-statement,invalid-name

    if _supabase_client is None:
        settings = get_settings()

        supabase_url = settings.supabase.supabase_url
        supabase_key = settings.supabase.supabase_anon_key

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not configured")

        # Configure client options
        options = ClientOptions(
            schema="public",
            headers={"X-Client-Info": "personal-health-assistant/1.0.0"},
        )

        # Create client
        _supabase_client = create_client(
            supabase_url=supabase_url, supabase_key=supabase_key, options=options
        )

        logger.info("Supabase client initialized successfully")

    return _supabase_client


def reset_supabase_client() -> None:
    """Reset the Supabase client singleton (useful for testing)"""
    global _supabase_client  # pylint: disable=global-statement,invalid-name
    _supabase_client = None
    logger.info("Supabase client reset")
