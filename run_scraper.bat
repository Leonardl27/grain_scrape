@echo off
REM Grain Price Scraper - Windows Task Scheduler Script
REM Schedule this to run twice daily (e.g., 6 AM and 6 PM)

cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the scraper using Anaconda Python
"C:\Users\leona\Anaconda3\python.exe" scraper.py

REM Log completion
echo Scrape completed at %date% %time% >> scraper_log.txt
