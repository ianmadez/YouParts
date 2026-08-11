import time
import random
from typing import List, Dict, Any
from src.scrapers.base_scraper import BaseScraper

try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class StealthPlaywrightTemplateScraper(BaseScraper):
    """
    Modular Playwright Stealth Scraper Template.
    Includes human-like micro-delays, randomized viewports, webdriver masking,
    and scroll simulation to bypass basic automated anti-bot checks.
    """

    PLATFORM_NAME = "Custom Store"
    SEARCH_URL_TEMPLATE = "https://example.com/search?q={query}"

    def __init__(self, headless: bool = True):
        self.headless = headless

    def _human_delay(self, min_sec: float = 1.2, max_sec: float = 3.5):
        """Staggered random delay to mimic human reading and interaction pacing."""
        time.sleep(random.uniform(min_sec, max_sec))

    def _simulate_human_scrolling(self, page: "Page"):
        """Simulates non-linear human page scrolling."""
        scroll_steps = random.randint(2, 4)
        for _ in range(scroll_steps):
            scroll_amount = random.randint(150, 400)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.3, 0.7))

    def search_part(self, part_name: str, specs: str = "") -> List[Dict[str, Any]]:
        query = f"{part_name} {specs}".strip()
        search_url = self.SEARCH_URL_TEMPLATE.format(query=query.replace(" ", "+"))

        if not PLAYWRIGHT_AVAILABLE:
            print(f"[{self.PLATFORM_NAME}] Playwright library not installed. Returning fallback search link.")
            return self._fallback_response(query, search_url)

        results = []
        try:
            with sync_playwright() as p:
                # 1. Launch browser with stealth flags
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-infobars"
                    ]
                )

                # 2. Context setup with dynamic realistic desktop viewports & User-Agent
                context = browser.new_context(
                    viewport={"width": random.randint(1366, 1920), "height": random.randint(768, 1080)},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-US"
                )

                # 3. Override navigator.webdriver flag
                page = context.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                # 4. Human-paced navigation
                page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                self._human_delay(1.5, 3.0)

                # 5. Simulate human mouse & scroll micro-behavior
                self._simulate_human_scrolling(page)

                # --- DOM Extraction (Customize for your target platform) ---
                # Example:
                # items = page.query_selector_all(".product-item")
                # for item in items[:3]:
                #     title = item.query_selector(".title").inner_text()
                #     price = item.query_selector(".price").inner_text()
                #     link = item.query_selector("a").get_attribute("href")
                #     results.append({"platform": self.PLATFORM_NAME, "title": title, "price": price, ...})

                browser.close()

        except Exception as e:
            print(f"[{self.PLATFORM_NAME}] Stealth scraper notice: {e}. Falling back to direct search link.")
            return self._fallback_response(query, search_url)

        return results if results else self._fallback_response(query, search_url)

    def _fallback_response(self, query: str, search_url: str) -> List[Dict[str, Any]]:
        """Safe fallback route when CAPTCHA or blocking triggers."""
        return [{
            "platform": self.PLATFORM_NAME,
            "title": f"{self.PLATFORM_NAME} Search: '{query}'",
            "price": "Check Store",
            "currency": "LOCAL",
            "product_url": search_url,
            "is_direct_search": True
        }]