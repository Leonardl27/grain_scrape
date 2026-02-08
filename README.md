# Grain Price Scraper

Automated grain price tracking for Legacy Cooperative's Rolla location with a Streamlit dashboard for visualization.

## Features

- **Automated Scraping**: Playwright-based scraper extracts cash bids from Legacy Cooperative
- **Price Tracking**: SQLite database stores historical prices for trend analysis
- **Interactive Dashboard**: Streamlit web app with charts, filtering, and CSV export
- **Scheduling**: Windows Task Scheduler support for twice-daily data collection

## Commodities Tracked

- Corn
- Soybeans
- Spring Wheat (14% Pro)
- Winter Wheat (12% Pro)
- Canola

## Installation

```bash
# Clone the repository
git clone https://github.com/Leonardl27/grain_scrape.git
cd grain_scrape

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## Usage

### Run the scraper manually

```bash
python scraper.py
```

### Launch the dashboard

```bash
streamlit run dashboard.py
```

Then open http://localhost:8501 in your browser.

### Schedule automated scraping (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Daily, repeat every 12 hours
4. Action: Start a program
5. Program: `C:\path\to\grain_scrape\run_scraper.bat`

## Project Structure

```
grain_scrape/
├── scraper.py          # Playwright scraper for grain prices
├── database.py         # SQLite database operations
├── dashboard.py        # Streamlit dashboard
├── requirements.txt    # Python dependencies
├── run_scraper.bat     # Windows scheduler script
└── grain_prices.db     # SQLite database (created at runtime)
```

## Live Demo

View the dashboard: [Streamlit Cloud](https://share.streamlit.io)

## Data Source

Prices are scraped from [Legacy Cooperative](https://www.legacy-cooperative.com/grain#cash-bids).

## License

MIT
