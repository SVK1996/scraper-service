from fastapi import FastAPI, Depends
from app.models.schemas import ScrapingSettings, ScrapingResult
from app.core.scraper import Scraper
from app.dependencies import (
  CacheServiceDep,
  StorageStrategyDep,
  NotificationStrategyDep
)
from app.services.auth_service import verify_api_key
from app.config import settings
import asyncio

app = FastAPI(title="Scraper Service")

@app.get("/health")
async def health_check():
  """Health check endpoint"""
  return {
      "status": "OK",
      "service": "scraper-service",
      "version": "1.0.0"
  }


@app.post(f"{settings.API_PREFIX}/scrape/", response_model=ScrapingResult)
async def scrape_products(
  settings_input: ScrapingSettings,
  cache_service: CacheServiceDep,
  storage: StorageStrategyDep,
  notifier: NotificationStrategyDep,
  api_key: str = Depends(verify_api_key)
):
  async with Scraper(settings.BASE_URL, settings_input) as scraper:
      all_products = []
      updated_products = 0
      page = 1

      while True:
          if settings_input.page_limit and page > settings_input.page_limit:
              break

          products = await scraper.scrape_page(page)
          if not products:
              break

          for product in products:
              cached_price = cache_service.get_product_price(product.product_title)
              if cached_price != product.product_price:
                  updated_products += 1
                  cache_service.set_product_price(
                      product.product_title,
                      product.product_price
                  )

          all_products.extend(products)
          page += 1

      storage.save(all_products)
      result = ScrapingResult(
          total_products=len(all_products),
          updated_products=updated_products
      )
      notifier.notify(result)
      return result

@app.on_event("startup")
async def startup_event():
  pass

@app.on_event("shutdown")
async def shutdown_event():
  pass