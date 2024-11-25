from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional

class ScrapingSettings(BaseModel):
  page_limit: Optional[int] = None
  proxy: Optional[str] = None

class Product(BaseModel):
  product_title: str
  product_price: float
  path_to_image: str

  @validator('product_price')
  def validate_price(cls, v):
      if v <= 0:
          raise ValueError('Price must be greater than 0')
      return v

class ScrapingResult(BaseModel):
  total_products: int
  updated_products: int