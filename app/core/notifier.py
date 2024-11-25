from abc import ABC, abstractmethod
from app.models.schemas import ScrapingResult

class NotificationStrategy(ABC):
  @abstractmethod
  def notify(self, result: ScrapingResult) -> None:
      pass

class ConsoleNotifier(NotificationStrategy):
  def notify(self, result: ScrapingResult) -> None:
      print(f"Scraping completed: {result.total_products} products found, "
            f"{result.updated_products} products updated")