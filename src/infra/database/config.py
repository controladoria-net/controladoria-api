import os
from functools import lru_cache

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def get_database_url() -> str:
    """Retrieve the database URL from environment variables."""
    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return database_url
