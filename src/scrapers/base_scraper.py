from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    """
    Abstract Base Class for all YouParts scrapers.
    Whether generating direct search links or running a headless stealth browser,
    all regional scraper plugins must implement `search_part`.
    """

    @abstractmethod
    def search_part(self, part_name: str, specs: str = "") -> List[Dict[str, Any]]:
        """
        Executes a component search and returns standardized price/listing records.

        Expected Output Schema:
        [
            {
                "platform": str,          # e.g., "Amazon US", "McMaster-Carr", "Shopee MY"
                "title": str,             # Listing title or query description
                "price": str,             # Formatted price string or "Check Listing"
                "currency": str,          # Currency code e.g. "USD", "MYR", "EUR"
                "product_url": str,       # Direct product or target search link URL
                "is_direct_search": bool  # True if fallback search link, False if scraped product
            }
        ]
        """
        pass