"""
Supabase Client

Provides cached Supabase client instance for database operations.
"""

from functools import lru_cache

from supabase import create_client, Client

from api.app.config import get_settings

settings = get_settings()


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get cached Supabase client instance.

    Uses service role key for full database access.
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
    )


class SupabaseClient:
    """
    Supabase client wrapper with helper methods.

    Provides convenience methods for common database operations
    while allowing direct access to the underlying client.
    """

    def __init__(self, client: Client | None = None):
        self._client = client or get_supabase_client()

    @property
    def client(self) -> Client:
        """Get the underlying Supabase client."""
        return self._client

    def table(self, name: str):
        """Get a table reference."""
        return self._client.table(name)

    async def rpc(self, function_name: str, params: dict | None = None):
        """Call a Supabase RPC function."""
        return self._client.rpc(function_name, params or {}).execute()

    async def health_check(self) -> bool:
        """Check if Supabase is reachable."""
        try:
            self._client.table("admin_prompts").select("id").limit(1).execute()
            return True
        except Exception:
            return False
