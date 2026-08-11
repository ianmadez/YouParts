import urllib.parse
import requests
from typing import List, Dict, Any

class AliExpressScraper:
    """Lightweight search utility for AliExpress items."""

    BASE_SEARCH_URL = "https://www.aliexpress.com/w/wholesale-{query}.html"

    @classmethod
    def search_part(cls, part_query: str, limit: int = 3) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(part_query.replace(" ", "-"))
        search_url = cls.BASE_SEARCH_URL.format(query=encoded_query)

        # Fallback output structure for direct product lookup link
        results = [{
            "platform": "AliExpress",
            "title": f"Search results for '{part_query}'",
            "price": "Check Store",
            "currency": "USD",
            "product_url": search_url,
            "is_direct_search": True
        }]
        return results