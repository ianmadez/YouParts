import urllib.parse
from typing import List, Dict, Any

class LazadaScraper:
    """Lightweight regional search link builder for Lazada."""

    BASE_SEARCH_URL = "https://www.lazada.com/catalog/?q={query}"

    @classmethod
    def search_part(cls, part_query: str, limit: int = 3) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(part_query)
        search_url = cls.BASE_SEARCH_URL.format(query=encoded_query)

        return [{
            "platform": "Lazada",
            "title": f"Lazada Search: '{part_query}'",
            "price": "Check Listing",
            "currency": "MYR/LOCAL",
            "product_url": search_url,
            "is_direct_search": True
        }]