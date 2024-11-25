from abc import ABC, abstractmethod
import json
from typing import List
from app.models.schemas import Product

class StorageStrategy(ABC):
  @abstractmethod
  def save(self, products: List[Product]) -> None:
      pass

  @abstractmethod
  def load(self) -> List[Product]:
      pass

class JsonFileStorage(StorageStrategy):
  def __init__(self, file_path: str = "products.json"):
      self.file_path = file_path

  def save(self, products: List[Product]) -> None:
      with open(self.file_path, 'w') as f:
          json.dump([product.dict() for product in products], f, indent=2)

  def load(self) -> List[Product]:
      try:
          with open(self.file_path, 'r') as f:
              data = json.load(f)
              return [Product(**item) for item in data]
      except FileNotFoundError:
          return []