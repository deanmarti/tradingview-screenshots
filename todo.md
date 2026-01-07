# TradingView Screenshot Tool - Todo List

## Milestone 1: Configurable Time Interval ✅
- [x] Create a new tradingview_screenshot.py file
- [x] Add `INTERVAL_CONFIG` dictionary with interval codes and lookback days
- [x] Add `-i` / `--interval` CLI argument (default: `1D`)
- [x] Update function signature to accept `interval` parameter
- [x] Update lookback calculation to use config values
- [x] Update TradingView widget `"interval"` value dynamically
- [x] Update h2 title to reflect selected interval and date range
- [x] Update output filenames to include interval
- [x] Review and check the file

## Milestone 2: Optional Technical Indicators ✅
- [x] Add `INDICATOR_MAP` dictionary (MACD, RSI, DMI)
- [x] Add `-s` / `--studies` CLI argument (default: `MACD,RSI`)
- [x] Update function to accept `studies` parameter
- [x] Build studies array from comma-separated input
- [x] Update TradingView widget `"studies"` array
- [x] Update h2 title to show which indicators are displayed
- [x] Update output filenames to indicate when indicators are used
- [x] Review and check the file

## Milestone 3: Chart Validation ✅
- [x] Add `check_dom_errors()` function to detect TradingView error elements
- [x] Add `validate_chart()` function combining DOM check + file size validation
- [x] Define `MIN_FILE_SIZE` constant (50KB threshold)
- [x] Wrap main logic in try/except for network errors
- [x] Implement exit codes (0=success, 1=chart error)
- [x] Print validation status to stdout
- [x] Add `import sys` for exit codes
- [x] Review and check the file

## Milestone 4: Create docker compose to run on raspi / trixie ✅
- [x] Create docker compose - the docker compose has to define the standard password (Home4Charts8115$) and expose the SSH port
- [x] Create a short manual (ie where to copy the file, etc)
- [x] Create a json for a n8n node to run this via ssh and fetch the output file. Create one for the normal one and one with indicators