# app/core/scraper.py
import aiohttp
import asyncio
from typing import List, Optional, Dict, Tuple
import os
import logging
from bs4 import BeautifulSoup
from app.models.schemas import Product, ScrapingSettings
import tenacity
from urllib.parse import urljoin, urlparse
import aiofiles
import re

logger = logging.getLogger(__name__)

class ScraperException(Exception):
  """Custom exception for scraper errors"""
  pass

class Scraper:
  def __init__(self, base_url: str, settings: ScrapingSettings):
      self.base_url = base_url
      self.settings = settings
      self.session = None
      self.headers = {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.5",
      }

  async def __aenter__(self):
      timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout
      self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
      return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
      if self.session:
          await self.session.close()

  def _sanitize_filename(self, filename: str) -> str:
      """Sanitize filename to be safe for all operating systems"""
      # Remove invalid characters and limit length
      safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
      return safe_filename[:255]  # Maximum filename length

  def _normalize_url(self, url: str) -> str:
      """Normalize URL by adding scheme if missing"""
      if not url.startswith(('http://', 'https://')):
          return urljoin(self.base_url, url)
      return url

  async def _safe_get_text(self, element, selector: str, default: str = "") -> str:
      """Safely extract text from a BS4 element"""
      try:
          found_elem = element.select_one(selector)
          return found_elem.get_text(strip=True) if found_elem else default
      except Exception as e:
          logger.warning(f"Error extracting text with selector {selector}: {str(e)}")
          return default

  async def _safe_get_price(self, element) -> float:
      """Safely extract and convert price to float"""
      try:
          price_text = element.text.strip()
          # Remove currency symbols and whitespace
          price_text = re.sub(r'[^\d.,]', '', price_text)
          # Split by any non-digit characters except decimal point
          price_parts = re.findall(r'\d+\.?\d*', price_text)
          if price_parts:
              return float(price_parts[0])
          return 0.0
      except Exception as e:
          logger.warning(f"Error converting price: {str(e)}")
          return 0.0

  def _is_valid_url(self, url: str) -> bool:
      """Check if the URL is valid"""
      if not url:
          return False
      try:
          result = urlparse(url)
          return all([result.scheme, result.netloc])
      except Exception:
          return False

  async def _get_image_url(self, product_elem) -> str:
      """Extract image URL from product element"""
      try:
          # Try different image selectors
          img_selectors = [
              'img.product-image',
              'img.attachment-woocommerce_thumbnail',
              'img[data-src]',
              'img[src]',
              'img'
          ]

          for selector in img_selectors:
              img_elem = product_elem.select_one(selector)
              if img_elem:
                  # Try different image attributes
                  for attr in ['data-src', 'src', 'data-lazy-src']:
                      image_url = img_elem.get(attr)
                      if image_url and not image_url.startswith('data:'):
                          # Convert relative URLs to absolute
                          if not image_url.startswith(('http://', 'https://')):
                              image_url = urljoin(self.base_url, image_url)
                          if self._is_valid_url(image_url):
                              return image_url

          logger.warning("No valid image URL found")
          return ""

      except Exception as e:
          logger.error(f"Error getting image URL: {str(e)}")
          return ""


  @tenacity.retry(
      stop=tenacity.stop_after_attempt(3),
      wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
      retry=tenacity.retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
      before_sleep=lambda retry_state: logger.info(f"Retrying request... (attempt {retry_state.attempt_number})")
  )

  async def scrape_page(self, page: int) -> List[Product]:
      """Scrape a single page for products"""
      try:
          url = f"{self.base_url}/page/{page}" if page > 1 else self.base_url
          logger.info(f"Scraping page {page}: {url}")

          async with self.session.get(
              url,
              proxy=self.settings.proxy,
              ssl=False if self.settings.proxy else None
          ) as response:
              response.raise_for_status()
              html = await response.text()

          soup = BeautifulSoup(html, 'html.parser')
          products = []

          # Try different product selectors
          product_selectors = [
              '.product',
              '.type-product',
              '.wc-product',
              '[data-product-id]'
          ]

          for selector in product_selectors:
              product_elements = soup.select(selector)
              if product_elements:
                  break

          for product_elem in product_elements:
              try:
                  # Get product title
                  title_elem = product_elem.select_one('.product-title, .woocommerce-loop-product__title, h2')
                  if not title_elem:
                      continue
                  title = title_elem.text.strip()

                  # Get image URL
                  image_url = await self._get_image_url(product_elem)
                  if not image_url:
                      logger.warning(f"No valid image URL found for product: {title}")
                      continue

                  # Get price
                  price_elem = product_elem.select_one('.price, .product-price, .woocommerce-Price-amount')
                  if not price_elem:
                      logger.warning(f"No price found for product: {title}")
                      continue

                  price = await self._safe_get_price(price_elem)
                  if price <= 0:
                      logger.warning(f"Invalid price for product: {title}")
                      continue

                  products.append(Product(
                      product_title=title,
                      product_price=price,
                      path_to_image=image_url  # Use the image URL directly
                  ))

              except Exception as e:
                  logger.error(f"Error processing product: {str(e)}")
                  continue

          return products

      except Exception as e:
          logger.error(f"Error scraping page {page}: {str(e)}")
          raise
  
  async def _download_image(self, image_url: str, title: str) -> str:
      """Download and save image with proper error handling"""
      try:
          # Create images directory if it doesn't exist
          os.makedirs('images', exist_ok=True)

          # Generate safe filename from title
          safe_filename = self._sanitize_filename(title) + '.jpg'
          image_path = os.path.join('images', safe_filename)

          # Check if file already exists
          if os.path.exists(image_path):
              logger.debug(f"Image already exists: {image_path}")
              return image_path

          async with self.session.get(image_url) as response:
              response.raise_for_status()

              # Verify content type
              content_type = response.headers.get('content-type', '')
              if not content_type.startswith('image/'):
                  raise ValueError(f"Invalid content type: {content_type}")

              # Save image using aiofiles for async I/O
              async with aiofiles.open(image_path, 'wb') as f:
                  await f.write(await response.read())

          logger.debug(f"Successfully downloaded image: {image_path}")
          return image_path

      except aiohttp.ClientError as e:
          logger.error(f"Error downloading image from {image_url}: {str(e)}")
          return ""
      except Exception as e:
          logger.error(f"Error saving image for {title}: {str(e)}")
          return ""

  async def scrape_all(self) -> List[Product]:
      """Scrape all pages up to the limit"""
      all_products = []
      page = 1
      page_limit = self.settings.page_limit or float('inf')

      async with self:
          while page <= page_limit:
              try:
                  products = await self.scrape_page(page)
                  if not products:
                      break

                  all_products.extend(products)
                  logger.info(f"Total products scraped: {len(all_products)}")

                  page += 1

              except ScraperException as e:
                  logger.error(f"Scraping stopped due to error: {str(e)}")
                  break
              except Exception as e:
                  logger.error(f"Unexpected error: {str(e)}")
                  break

      return all_products