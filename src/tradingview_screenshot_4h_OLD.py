import os
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta

def create_tradingview_weekly_chart(ticker_symbol):
    today = datetime.today()
    # Approximate 6 months as 183 days
    six_months_ago = today - timedelta(days=183)
    date_range = f"from: {six_months_ago.strftime('%B %Y')} to: {today.strftime('%B %Y')}"

# Generate HTML content with TradingView widget - https://www.tradingview.com/widget-docs/widgets/charts/symbol-overview/
    html_content = f"""
    <h2>"{ticker_symbol}|4h chart, last 6 months|{date_range}"</h2>
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
  "hide_legend": true,
  "hide_volume": true,
  "hotlist": false,
  "interval": "240",
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
  "studies": [],
  "autosize": true
}}
  </script>
</div>
<!-- TradingView Widget END -->
    """

    # Save the HTML content to a file
    html_file_name = f"/home/pi/code/n8n/beeforceai/tradingview_charts/tradingview_daily_chart_{ticker_symbol.replace(':', '_')}.html"
    html_file_path = os.path.abspath(html_file_name)
    with open(html_file_path, "w") as file:
        file.write(html_content)

    # Set up Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize the Chrome WebDriver
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the generated HTML file
    driver.get(f"file://{html_file_path}")
    
    # Wait for the widget to load
    time.sleep(8)

    # Take a screenshot of the full page
    screenshot_path = f"/home/pi/code/n8n/beeforceai/tradingview_charts/tradingview_daily_chart_{ticker_symbol.replace(':', '_')}.png"
    driver.save_screenshot(screenshot_path)
    print(f"{screenshot_path}")

    driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate TradingView daily chart for a given stock ticker')
    parser.add_argument('ticker_symbol', type=str, help='Stock ticker symbol (e.g., AAPL or NASDAQ:AAPL)')
    args = parser.parse_args()
    
    # Convert ticker to uppercase
    ticker_symbol = args.ticker_symbol.strip().upper()
    create_tradingview_weekly_chart(ticker_symbol)
