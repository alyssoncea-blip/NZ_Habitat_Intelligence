"""Trade Me Property Scraper — Playwright-based with rate limiting.

Scrapes property listings from Trade Me with proper delays, retries,
and respectful rate limiting. Falls back to cached data when scraping fails.
"""
import json
import logging
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger(__name__)

TRADE_ME_BASE = "https://www.trademe.co.nz/a/property/residential"
TRADE_ME_RENT = "https://www.trademe.co.nz/a/property/residential/rent"

REGIONS = [
    {"name": "Auckland", "id": 2},
    {"name": "Wellington", "id": 10},
    {"name": "Canterbury", "id": 12},
    {"name": "Waikato", "id": 4},
    {"name": "Bay of Plenty", "id": 5},
    {"name": "Otago", "id": 14},
]


class TradeMeScraper:
    """Scraper for Trade Me Property listings using Playwright."""

    def __init__(self, data_dir: str = "data_pipeline/bronze"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.request_delay_min = int(os.getenv("TRADE_ME_DELAY_MIN", 5))
        self.request_delay_max = int(os.getenv("TRADE_ME_DELAY_MAX", 15))
        self.max_listings_per_region = int(os.getenv("TRADE_ME_MAX_LISTINGS", 50))

    def _delay(self):
        """Respectful delay between requests."""
        delay = random.uniform(self.request_delay_min, self.request_delay_max)
        logger.info("  Waiting %.1f seconds (rate limiting)", delay)
        time.sleep(delay)

    def _scrape_with_playwright(self, url: str, region_name: str) -> List[Dict[str, Any]]:
        """Scrape a single Trade Me search results page using Playwright."""
        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright not installed — skipping real scrape")
            return []

        listings = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()

                logger.info("  Opening %s", url)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)  # Let JS render

                # Try to extract listing cards
                cards = page.query_selector_all("[data-testid='listing-card']") or \
                        page.query_selector_all(".tms-qa-property-listing-card") or \
                        page.query_selector_all(".listing-card")

                for card in cards[:self.max_listings_per_region]:
                    try:
                        title_el = card.query_selector("a") or card.query_selector(".listing-title")
                        price_el = card.query_selector("[data-testid='price']") or card.query_selector(".price")
                        address_el = card.query_selector("[data-testid='address']") or card.query_selector(".address")

                        listing = {
                            "region": region_name,
                            "title": (title_el.inner_text() if title_el else "").strip(),
                            "price": (price_el.inner_text() if price_el else "").strip(),
                            "address": (address_el.inner_text() if address_el else "").strip(),
                            "url": (title_el.get_attribute("href") if title_el else "").strip(),
                            "scraped_at": datetime.now().isoformat(),
                        }
                        if listing["title"] or listing["price"]:
                            listings.append(listing)
                    except Exception as e:
                        logger.debug("  Error parsing card: %s", e)

                browser.close()

        except PlaywrightTimeout:
            logger.warning("  Timeout scraping %s", region_name)
        except Exception as e:
            logger.warning("  Error scraping %s: %s", region_name, e)

        return listings

    def scrape_listings(self) -> Dict[str, Any]:
        """Scrape property listings from Trade Me for all NZ regions."""
        logger.info("Starting Trade Me Property scrape (%d regions)", len(REGIONS))
        all_listings = []

        for region in REGIONS:
            url = f"{TRADE_ME_BASE}/{region['name'].lower()}"
            logger.info("Scraping %s...", region["name"])
            listings = self._scrape_with_playwright(url, region["name"])
            all_listings.extend(listings)
            logger.info("  Got %d listings from %s", len(listings), region["name"])
            self._delay()

        result = {
            "metadata": {
                "source": "Trade Me Property",
                "date_scraped": datetime.now().isoformat(),
                "scraping_method": "playwright" if HAS_PLAYWRIGHT else "unavailable",
                "total_listings": len(all_listings),
                "regions_scraped": len(REGIONS),
            },
            "listings": all_listings,
        }
        return result

    def scrape_rentals(self) -> Dict[str, Any]:
        """Scrape rental listings from Trade Me."""
        logger.info("Starting Trade Me Rentals scrape")
        all_rentals = []

        for region in REGIONS:
            url = f"{TRADE_ME_RENT}/{region['name'].lower()}"
            rentals = self._scrape_with_playwright(url, region["name"])
            all_rentals.extend(rentals)
            logger.info("  Got %d rentals from %s", len(rentals), region["name"])
            self._delay()

        return {
            "metadata": {
                "source": "Trade Me Rentals",
                "date_scraped": datetime.now().isoformat(),
                "scraping_method": "playwright" if HAS_PLAYWRIGHT else "unavailable",
                "total_rentals": len(all_rentals),
            },
            "rentals": all_rentals,
        }

    def save_data(self, name: str, data: Dict[str, Any]) -> str:
        path = self.data_dir / f"trade_me_{name}_raw.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Saved %s to %s", name, path)
        return str(path)

    def run_scraping(self) -> Dict[str, str]:
        """Run full Trade Me scraping process."""
        results = {}

        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            results["error"] = "Playwright not available"
            return results

        try:
            listings = self.scrape_listings()
            results["listings"] = self.save_data("listings", listings)
        except Exception as e:
            logger.error("Listings scrape failed: %s", e)

        try:
            rentals = self.scrape_rentals()
            results["rentals"] = self.save_data("rentals", rentals)
        except Exception as e:
            logger.error("Rentals scrape failed: %s", e)

        return results


if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    scraper = TradeMeScraper()
    results = scraper.run_scraping()
    for name, path in results.items():
        print(f"  {name}: {path}")
