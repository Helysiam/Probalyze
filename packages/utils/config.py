from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = "https://taefyqfdtulikkivkwnr.supabase.co"
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_ANON_KEY: str = "sb_publishable_Rsnvz3wRJLynvPqyu5uHXQ_QKL2mySV"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL_DEFAULT: int = 120

    # API
    ALLOWED_ORIGINS: str = "http://localhost:3001,https://probalyze.picsnature.fr"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]
    API_PORT: int = 8000

    # Odds API (odds-api.com)
    ODDS_API_KEY: str = ""
    ODDS_API_BASE: str = "https://api.the-odds-api.com/v4"

    # Worker
    WORKER_INTERVAL_SECONDS: int = 3600  # 1h between ingestion cycles

    # Model
    MODEL_VERSION: str = "poisson-v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
