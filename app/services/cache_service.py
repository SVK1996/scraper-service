# app/services/cache_service.py
import redis
import logging
from typing import Optional
import time

logger = logging.getLogger(__name__)

class CacheService:
  def __init__(self, host: str, port: int, db: int = 0):
      self.redis_client = None
      self.host = host
      self.port = port
      self.db = db
      self._connect_with_retry()

  def _connect_with_retry(self, max_retries=5, delay=2):
      """Attempt to connect to Redis with retries"""
      for attempt in range(max_retries):
          try:
              self.redis_client = redis.Redis(
                  host=self.host,
                  port=self.port,
                  db=self.db,
                  decode_responses=True,
                  socket_timeout=5,
                  socket_connect_timeout=5
              )
              # Test the connection
              self.redis_client.ping()
              logger.info("Successfully connected to Redis")
              return
          except redis.ConnectionError as e:
              if attempt == max_retries - 1:
                  logger.error(f"Failed to connect to Redis after {max_retries} attempts")
                  raise
              logger.warning(f"Redis connection attempt {attempt + 1} failed, retrying in {delay} seconds")
              time.sleep(delay)

  def get_product_price(self, product_title: str) -> Optional[float]:
      """Get cached product price"""
      try:
          if not self.redis_client:
              return None
          price = self.redis_client.get(product_title)
          return float(price) if price else None
      except (redis.RedisError, ValueError) as e:
          logger.error(f"Error getting price from cache: {str(e)}")
          return None

  def set_product_price(self, product_title: str, price: float, expire_time: int = 3600) -> bool:
      """Set product price in cache"""
      try:
          if not self.redis_client:
              return False
          return bool(self.redis_client.setex(product_title, expire_time, str(price)))
      except redis.RedisError as e:
          logger.error(f"Error setting price in cache: {str(e)}")
          return False

  def is_healthy(self) -> bool:
      """Check if Redis connection is healthy"""
      try:
          return bool(self.redis_client and self.redis_client.ping())
      except Exception:
          return False
        
  def close(self):
      self.redis_client.close()