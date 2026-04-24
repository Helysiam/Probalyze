from supabase import create_client, Client
from functools import lru_cache

from packages.utils.config import settings
from packages.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    logger.info(f"Supabase client initialized: {settings.SUPABASE_URL}")
    return client


def get_supabase() -> Client:
    """FastAPI dependency."""
    return get_supabase_client()
