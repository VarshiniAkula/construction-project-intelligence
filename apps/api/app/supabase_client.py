"""Async Supabase client singleton."""
from supabase._async.client import AsyncClient, create_client as _create_client
from app.config import settings

_client: AsyncClient | None = None

async def get_supabase() -> AsyncClient:
    global _client
    if _client is None:
        _client = await _create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _client
