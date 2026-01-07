# TradingView Screenshot Tool - Specification

## Overview
Python script to generate TradingView chart screenshots with configurable time intervals, optional technical indicators, and chart validation.

## Current State ✅
- Script: `tradingview_screenshot.py`
- All milestones completed

---

## Milestone 1: Configurable Time Interval ✅

### Requirements
- CLI argument for time interval (`-i` / `--interval`)
- Supported intervals: `15m`, `1h`, `4h`, `1D`, `1W`
- Default: `1D`
- Auto-adjusted lookback periods:
  | Interval | Lookback Period |
  |----------|-----------------|
  | 15m      | 7 days          |
  | 1h       | 30 days         |
  | 4h       | 6 months        |
  | 1D       | 1 year          |
  | 1W       | 5 years         |
- Dynamic h2 title with interval and date range
- Output filenames include interval

### Usage
```bash
python tradingview_screenshot.py NASDAQ:AAPL -i 1D
python tradingview_screenshot.py NASDAQ:AAPL -i 4h
python tradingview_screenshot.py NASDAQ:AAPL -i 1W
```

---

## Milestone 2: Optional Technical Indicators ✅

### Requirements
- CLI argument for indicators (`-s` / `--studies`)
- Default: **no indicators** (chart only)
- `-s` without argument: defaults to `MACD,RSI`
- Supports **any TradingView study** (not just predefined)
- Multiple indicators via comma-separated list
- Shows legend when indicators are present (`hide_legend: false`)

### Shortcut Mappings
| Shortcut | TradingView Code |
|----------|------------------|
| MACD | STD;MACD |
| RSI | STD;RSI |
| DMI | STD;DMI |
| EMA | STD;EMA |
| SMA | STD;SMA |
| BB | STD;Bollinger Bands |
| VWAP | STD;VWAP |
| ATR | STD;ATR |
| ADX | STD;ADX |
| STOCH | STD;Stochastic |
| CCI | STD;CCI |
| MFI | STD;MFI |
| OBV | STD;OBV |
| ICHIMOKU | STD;Ichimoku Cloud |

### Custom Studies
Any TradingView study can be used:
- Direct code: `STD;My Custom Study`
- Name only: `Volume` → automatically becomes `STD;VOLUME`

### Usage
```bash
python tradingview_screenshot.py NASDAQ:AAPL -i 4h           # No indicators
python tradingview_screenshot.py NASDAQ:AAPL -i 4h -s        # Default: MACD,RSI
python tradingview_screenshot.py NASDAQ:AAPL -i 4h -s RSI    # RSI only
python tradingview_screenshot.py NASDAQ:AAPL -i 4h -s BB,VWAP,Volume  # Multiple
```

---

## Milestone 3: Chart Validation ✅

### Requirements
- Validate chart rendered correctly
- DOM error check for TradingView error elements
- File size validation (minimum 35KB)
- Exit codes:
  - `0` = Success
  - `1` = Invalid chart
- Clean output:
  - Success: prints only filename
  - Error: prints `Error: Invalid chart` to stderr

### Validation Approach
1. Check DOM for error elements (`.tv-widget-error`, etc.)
2. Verify screenshot file size ≥ 35KB

---

## Milestone 4: Docker & n8n Integration ✅

### Docker Deployment
- `docker-compose.yml` - Container configuration
- `Dockerfile` - Debian Trixie base with Python, Chromium, SSH
- SSH access on port `2222`
- Password: `Home4Charts8115$`

### n8n Integration
- `n8n_node_chart_normal.json` - Workflow for charts without indicators
- `n8n_node_chart_indicators.json` - Workflow for charts with indicators

### Deployment Files
- `DEPLOYMENT.md` - Full deployment manual
- `requirements.txt` - Python dependencies

---

## CLI Reference

```bash
python tradingview_screenshot.py TICKER [-i INTERVAL] [-s [STUDIES]] [-o OUTPUT_DIR]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `TICKER` | Stock symbol (e.g., `NASDAQ:AAPL`) | Required |
| `-i`, `--interval` | Chart interval (`15m`, `1h`, `4h`, `1D`, `1W`) | `1D` |
| `-s`, `--studies` | Indicators (comma-separated) | None (no indicators) |
| `-s` (no value) | Use default indicators | `MACD,RSI` |
| `-o`, `--output` | Output directory | Script directory |

---

## File Outputs
- HTML file: `tradingview_{interval}_chart_{ticker}.html`
- Screenshot (no indicators): `tradingview_{interval}_chart_{ticker}.png`
- Screenshot (with indicators): `tradingview_{interval}_chart_{ticker}_indicators.png`

---

## Dependencies
- Python 3.x
- Selenium
- Chromium / Chrome + Chromedriver
