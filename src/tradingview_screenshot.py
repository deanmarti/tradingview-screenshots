import os
import sys
import time
import json
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta

# Validation constants
MIN_FILE_SIZE = 35000  # 35KB minimum for valid chart

# Interval configuration: TradingView codes and lookback periods
INTERVAL_CONFIG = {
    "15m": {"code": "15", "label": "15min", "lookback_days": 7},
    "1h":  {"code": "60", "label": "1h", "lookback_days": 30},
    "4h":  {"code": "240", "label": "4h", "lookback_days": 183},
    "1D":  {"code": "D", "label": "Daily", "lookback_days": 365},
    "1W":  {"code": "W", "label": "Weekly", "lookback_days": 1825},
}

# Common indicator shortcuts (user-friendly names to TradingView study codes)
INDICATOR_SHORTCUTS = {
    "MACD": "STD;MACD",
    "RSI": "STD;RSI",
    "DMI": "STD;DMI",
    "EMA": "STD;EMA",
    "SMA": "STD;SMA",
    "BB": "STD;Bollinger Bands",
    "VWAP": "STD;VWAP",
    "ATR": "STD;ATR",
    "ADX": "STD;ADX",
    "STOCH": "STD;Stochastic",
    "CCI": "STD;CCI",
    "MFI": "STD;MFI",
    "OBV": "STD;OBV",
    "ICHIMOKU": "STD;Ichimoku Cloud",
}


def resolve_study(study_name):
    """Resolve study name to TradingView code. Supports shortcuts and direct codes."""
    study_upper = study_name.upper()

    # Check if it's a shortcut
    if study_upper in INDICATOR_SHORTCUTS:
        return INDICATOR_SHORTCUTS[study_upper]

    # If already has STD; prefix, use as-is
    if study_name.startswith("STD;"):
        return study_name

    # Otherwise, assume it's a standard indicator and add STD; prefix
    return f"STD;{study_name}"


def check_dom_errors(driver):
    """Check for TradingView error elements in the DOM."""
    error_selectors = [
        ".tv-widget-error",
        "[data-error]",
        ".error-message",
        ".tv-symbol-not-found"
    ]
    for selector in error_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            return False, f"Error element found: {selector}"
    return True, "No errors in DOM"


def validate_chart(driver, screenshot_path):
    """Validate chart by checking DOM errors and screenshot file size.

    Returns: (success: bool, message: str, exit_code: int)
    """
    # Check for DOM errors (while browser is open)
    dom_valid, dom_msg = check_dom_errors(driver)
    if not dom_valid:
        return False, dom_msg, 1

    # Take screenshot
    driver.save_screenshot(screenshot_path)

    # Validate file size
    file_size = os.path.getsize(screenshot_path)
    if file_size < MIN_FILE_SIZE:
        return False, "Invalid chart", 1

    return True, "Valid chart", 0


def create_tradingview_chart(ticker_symbol, interval="1D", studies=None, output_dir=None):
    """Generate a TradingView chart screenshot for the given ticker, interval, and studies."""

    # Determine output directory
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    # Get interval configuration
    config = INTERVAL_CONFIG[interval]
    interval_code = config["code"]
    interval_label = config["label"]
    lookback_days = config["lookback_days"]

    # Process studies/indicators
    if studies is None:
        studies = []
    studies_codes = [resolve_study(s) for s in studies]
    studies_json = json.dumps(studies_codes)  # Proper JSON formatting with double quotes
    studies_label = ", ".join(studies) if studies else ""
    hide_legend = "false" if studies_codes else "true"  # Show legend when indicators are present

    # Calculate date range
    today = datetime.today()
    start_date = today - timedelta(days=lookback_days)
    date_range = f"{start_date.strftime('%B %Y')} to {today.strftime('%B %Y')}"

    # Build title with optional indicators
    title_parts = [ticker_symbol, f"{interval_label} chart", date_range]
    if studies_label:
        title_parts.append(studies_label)
    title = " | ".join(title_parts)

    # Generate HTML content with TradingView widget
    html_content = f"""
    <h2>"{title}"</h2>
    <!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
  {{
  "allow_symbol_change": false,
  "calendar": false,
  "details": false,
  "hide_side_toolbar": true,
  "hide_top_toolbar": true,
  "hide_legend": {hide_legend},
  "hide_volume": true,
  "hotlist": false,
  "interval": "{interval_code}",
  "locale": "en",
  "save_image": false,
  "style": "1",
  "symbol": "{ticker_symbol}",
  "theme": "dark",
  "timezone": "Etc/UTC",
  "backgroundColor": "#0F0F0F",
  "gridColor": "rgba(242, 242, 242, 0.06)",
  "watchlist": [],
  "withdateranges": true,
  "compareSymbols": [],
  "studies": {studies_json},
  "autosize": true
}}
  </script>
</div>
<!-- TradingView Widget END -->
    """

    # Create output filenames with interval and optional indicators suffix
    safe_ticker = ticker_symbol.replace(':', '_')
    indicators_suffix = "_indicators" if studies else ""
    html_file_path = os.path.join(output_dir, f"tradingview_{interval}_chart_{safe_ticker}{indicators_suffix}.html")
    screenshot_path = os.path.join(output_dir, f"tradingview_{interval}_chart_{safe_ticker}{indicators_suffix}.png")

    # Save the HTML content to a file
    with open(html_file_path, "w") as file:
        file.write(html_content)

    # Set up Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")  # Suppress logs
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])

    # Use system Chromium binary on Linux (Debian/Raspbian)
    chromium_paths = ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]
    for path in chromium_paths:
        if os.path.exists(path):
            chrome_options.binary_location = path
            break

    # Initialize the Chrome WebDriver (suppress service logs)
    # Use system ChromeDriver path on Linux (Debian/Raspbian)
    chromedriver_paths = ["/usr/bin/chromedriver", "/usr/lib/chromium/chromedriver"]
    service = Service(log_output=os.devnull)
    for path in chromedriver_paths:
        if os.path.exists(path):
            service = Service(executable_path=path, log_output=os.devnull)
            break
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the generated HTML file
    driver.get(f"file:///{html_file_path}")

    # Wait for the widget to load
    time.sleep(8)

    # Validate chart and take screenshot
    success, message, exit_code = validate_chart(driver, screenshot_path)

    driver.quit()

    # Output results (only filename on success, error message on failure)
    if success:
        print(f"{screenshot_path}")
    else:
        print(f"Error: {message}", file=sys.stderr)

    return exit_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate TradingView chart screenshot for a given stock ticker')
    parser.add_argument('ticker_symbol', type=str, help='Stock ticker symbol (e.g., AAPL or NASDAQ:AAPL)')
    parser.add_argument('-i', '--interval', type=str, default='1D',
                        choices=['15m', '1h', '4h', '1D', '1W'],
                        help='Chart interval (default: 1D)')
    parser.add_argument('-s', '--studies', type=str, nargs='?', default=None, const='MACD,RSI',
                        help='Comma-separated indicators: MACD,RSI,DMI (default if -s provided: MACD,RSI)')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Output directory for chart files (default: script directory)')
    args = parser.parse_args()

    # Convert ticker to uppercase
    ticker_symbol = args.ticker_symbol.strip().upper()

    # Parse studies from comma-separated string (None if not provided)
    studies = []
    if args.studies:
        studies = [s.strip().upper() for s in args.studies.split(',') if s.strip()]

    # Determine output directory
    output_dir = args.output
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        exit_code = create_tradingview_chart(ticker_symbol, args.interval, studies, output_dir)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
