from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
  # API Settings
  API_KEY: str = "your-static-token"
  API_PREFIX: str = "/api/v1"

  # Redis Settings
  REDIS_HOST: str = "redis-cache"
  REDIS_PORT: int = 6379
  REDIS_DB: int = 0

  # Scraper Settings
  BASE_URL: str = "http://localhost:5000/test"
  MAX_RETRIES: int = 3
  RETRY_DELAY: int = 5

  # Storage Settings
  STORAGE_PATH: str = "test.json"
  IMAGES_DIR: str = "images"

  # Proxy Settings
  DEFAULT_PROXY: Optional[str] = None

  class Config:
      env_file = ".env"
      case_sensitive = True

settings = Settings()