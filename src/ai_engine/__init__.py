from config.settings import settings
from src.scrapers.aliexpress import AliExpressScraper
from src.scrapers.shopee import ShopeeScraper
from src.scrapers.lazada import LazadaScraper
from typing import List, Dict, Any

class MasterPriceAggregator:
    """Aggregates prices across enabled regional e-commerce platforms."""

    @staticmethod
    def fetch_all_matches(part_name: str, specs: str = "") -> List[Dict[str, Any]]:
        search_query = f"{part_name} {specs}".strip()
        aggregated_results = []

        if settings.ENABLE_ALIEXPRESS:
            aggregated_results.extend(AliExpressScraper.search_part(search_query))

        if settings.ENABLE_SHOPEE:
            aggregated_results.extend(ShopeeScraper.search_part(search_query))

        if settings.ENABLE_LAZADA:
            aggregated_results.extend(LazadaScraper.search_part(search_query))

        return aggregated_results