"""Scraper for Legacy Cooperative grain prices using Playwright."""

import re
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import database


URL = "https://www.legacy-cooperative.com/grain#cash-bids"
LOCATION = "Rolla"


def parse_price(text: str) -> float | None:
    """Parse price string to float."""
    if not text or text.strip() in ['-', 'N/A', '']:
        return None
    # Remove $ and other non-numeric chars except . and -
    cleaned = re.sub(r'[^\d.\-]', '', text.strip())
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_grain_prices() -> list[dict]:
    """Scrape grain prices from Legacy Cooperative website."""
    prices = []

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            print(f"Navigating to {URL}...")
            page.goto(URL, wait_until='networkidle', timeout=30000)

            # Wait for the cash bids widget to load
            print("Waiting for DTN widget to load...")
            page.wait_for_timeout(3000)  # Initial wait for JavaScript

            # Try to find and click on Rolla location if there's a dropdown
            try:
                # Look for location selector/dropdown
                location_selectors = [
                    f'text="{LOCATION}"',
                    f'option:has-text("{LOCATION}")',
                    f'[data-location="{LOCATION}"]',
                    f'button:has-text("{LOCATION}")',
                    f'.location-select >> text="{LOCATION}"'
                ]

                for selector in location_selectors:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=1000):
                            element.click()
                            print(f"Selected location: {LOCATION}")
                            page.wait_for_timeout(2000)
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Note: Could not find location selector: {e}")

            # Wait for price data to appear
            page.wait_for_timeout(2000)

            # Try multiple strategies to extract price data
            prices = extract_prices_from_table(page)

            if not prices:
                prices = extract_prices_from_dtn_widget(page)

            if not prices:
                # Fallback: save screenshot for debugging
                page.screenshot(path='debug_screenshot.png')
                print("Warning: No prices found. Screenshot saved to debug_screenshot.png")

        except PlaywrightTimeout as e:
            print(f"Timeout error: {e}")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()

    return prices


def extract_prices_from_table(page) -> list[dict]:
    """Extract prices from HTML table structure."""
    prices = []

    # Look for table rows with price data
    table_selectors = [
        'table.cash-bids tr',
        '.dtn-cash-bids-table tr',
        '[class*="cash"] table tr',
        '.widget-content table tr',
        'table tr'
    ]

    for selector in table_selectors:
        try:
            rows = page.locator(selector).all()
            if len(rows) > 1:  # Has header + data
                print(f"Found {len(rows)} rows with selector: {selector}")

                for row in rows[1:]:  # Skip header
                    cells = row.locator('td').all()
                    if len(cells) >= 3:
                        price_data = extract_row_data(cells)
                        if price_data and price_data.get('commodity'):
                            prices.append(price_data)

                if prices:
                    break
        except Exception as e:
            continue

    return prices


def extract_prices_from_dtn_widget(page) -> list[dict]:
    """Extract prices from DTN widget elements."""
    prices = []

    # DTN widgets often use specific class patterns
    widget_selectors = [
        '.dtn-cash-bids',
        '[class*="cashbid"]',
        '.commodity-row',
        '.bid-row',
        '[data-commodity]'
    ]

    for selector in widget_selectors:
        try:
            elements = page.locator(selector).all()
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")

                for elem in elements:
                    text = elem.inner_text()
                    price_data = parse_commodity_text(text)
                    if price_data:
                        prices.append(price_data)

                if prices:
                    break
        except Exception:
            continue

    return prices


def extract_row_data(cells) -> dict | None:
    """Extract data from table row cells."""
    try:
        if len(cells) < 3:
            return None

        texts = [cell.inner_text().strip() for cell in cells]

        # Common column orders:
        # Commodity, Delivery, Cash Price, Basis, Change
        # or: Commodity, Cash Price, Basis, Change, Delivery

        commodity = texts[0] if texts else None
        if not commodity or commodity.lower() in ['commodity', 'crop', '']:
            return None

        return {
            'commodity': commodity,
            'cash_price': parse_price(texts[2]) if len(texts) > 2 else None,
            'basis': parse_price(texts[3]) if len(texts) > 3 else None,
            'futures_change': parse_price(texts[4]) if len(texts) > 4 else None,
            'delivery_start': texts[1] if len(texts) > 1 else None,
            'delivery_end': texts[1] if len(texts) > 1 else None,
        }
    except Exception:
        return None


def parse_commodity_text(text: str) -> dict | None:
    """Parse commodity data from text block."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return None

    # First line is usually commodity name
    commodity = lines[0]
    if commodity.lower() in ['commodity', 'crop', 'cash bids', '']:
        return None

    # Try to find price values in remaining lines
    cash_price = None
    basis = None

    for line in lines[1:]:
        price = parse_price(line)
        if price is not None:
            if cash_price is None:
                cash_price = price
            elif basis is None:
                basis = price

    if cash_price is None:
        return None

    return {
        'commodity': commodity,
        'cash_price': cash_price,
        'basis': basis,
        'futures_change': None,
        'delivery_start': None,
        'delivery_end': None,
    }


def main():
    """Main entry point for scraper."""
    print(f"Starting grain price scrape at {datetime.now()}")
    print("=" * 50)

    prices = scrape_grain_prices()

    if prices:
        print(f"\nFound {len(prices)} price records:")
        for p in prices:
            print(f"  - {p['commodity']}: ${p['cash_price']}")

        # Save to database
        count = database.insert_prices(prices)
        print(f"\nSaved {count} records to database")
    else:
        print("\nNo prices found. The website structure may have changed.")
        print("Check debug_screenshot.png if available.")
        sys.exit(1)

    print("=" * 50)
    print("Scrape completed successfully")


if __name__ == "__main__":
    main()
