from pathlib import Path
import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8050"
OUTPUT_DIR = Path("docs/screenshots")
PAGES = [
    ("executive", "/executive"),
    ("housing", "/housing"),
    ("tourism", "/tourism"),
    ("macro", "/macro"),
    ("affordability", "/affordability"),
    ("forecast", "/forecast"),
]


def wait_for_dashboard(page) -> None:
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(4000)
    page.evaluate("window.scrollTo(0, 0)")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    only_page = sys.argv[1] if len(sys.argv) > 1 else None
    pages = [item for item in PAGES if only_page is None or item[0] == only_page]
    if not pages:
        raise SystemExit(f"Unknown page: {only_page}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 3200},
            device_scale_factor=1,
        )

        page = context.new_page()
        page.set_default_timeout(30000)

        for name, route in pages:
            url = f"{BASE_URL}{route}"
            print(f"Capturing {url}")
            page.goto(url, wait_until="domcontentloaded")
            wait_for_dashboard(page)
            output_file = OUTPUT_DIR / f"dashboard_{name}.png"
            page.screenshot(path=str(output_file), full_page=True)
            print(f"Saved {output_file}")

        browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
