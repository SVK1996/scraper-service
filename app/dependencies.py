from fastapi import Depends
from typing import Generator, Annotated
from app.services.cache_service import CacheService
from app.core.storage import StorageStrategy, JsonFileStorage
from app.core.notifier import NotificationStrategy, ConsoleNotifier
from app.config import settings

def get_cache_service() -> Generator[CacheService, None, None]:
  cache = CacheService(
      host=settings.REDIS_HOST,
      port=settings.REDIS_PORT,
      db=settings.REDIS_DB
  )
  try:
      yield cache
  finally:
      cache.close()

def get_storage_strategy() -> StorageStrategy:
  return JsonFileStorage(file_path=settings.STORAGE_PATH)

def get_notification_strategy() -> NotificationStrategy:
  return ConsoleNotifier()

# Type annotations for dependency injection
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
StorageStrategyDep = Annotated[StorageStrategy, Depends(get_storage_strategy)]
NotificationStrategyDep = Annotated[NotificationStrategy, Depends(get_notification_strategy)]