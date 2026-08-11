from typing import List, Dict, Any
from config.settings import settings
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.aliexpress import AliExpressScraper
from src.scrapers.shopee import ShopeeScraper
from src.scrapers.lazada import LazadaScraper
from src.scrapers.playwright_stealth_template import StealthPlaywrightTemplateScraper

__all__ = [
    "BaseScraper",
    "AliExpressScraper",
    "ShopeeScraper",
    "LazadaScraper",
    "StealthPlaywrightTemplateScraper",
    "MasterPriceAggregator",
]


class MasterPriceAggregator:
    """
    Central dispatch for price query lookups across active scrapers and fallback link generators.
    """

    @staticmethod
    def fetch_all_matches(part_name: str, specs: str = "") -> List[Dict[str, Any]]:
        search_query = f"{part_name} {specs}".strip()
        results: List[Dict[str, Any]] = []

        # 1. Fallback Search Link Builders (Always Reliable)
        if settings.ENABLE_ALIEXPRESS:
            results.extend(AliExpressScraper.search_part(search_query))

        if settings.ENABLE_SHOPEE:
            results.extend(ShopeeScraper.search_part(search_query))

        if settings.ENABLE_LAZADA:
            results.extend(LazadaScraper.search_part(search_query))

        return results
