import urllib.parse
from typing import List, Dict, Any

class ShopeeScraper:
    """Lightweight regional search link builder for Shopee."""

    BASE_SEARCH_URL = "https://shopee.com/search?keyword={query}"

    @classmethod
    def search_part(cls, part_query: str, limit: int = 3) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(part_query)
        search_url = cls.BASE_SEARCH_URL.format(query=encoded_query)

        return [{
            "platform": "Shopee",
            "title": f"Shopee Search: '{part_query}'",
            "price": "Check Listing",
            "currency": "MYR/LOCAL",
            "product_url": search_url,
            "is_direct_search": True
        }]