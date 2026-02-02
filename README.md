# TradingView Screenshot Tool

Automated chart screenshot generator for TradingView using Selenium and headless Chrome. Designed for deployment on Raspberry Pi via Docker/Portainer.

## Features

- **Configurable Time Intervals**: 15m, 1h, 4h, 1D, 1W with auto-adjusted lookback periods
- **Optional Technical Indicators**: Supports any TradingView study (MACD, RSI, BB, VWAP, etc.)
- **Chart Validation**: Exit codes for success/failure detection
- **Docker Deployment**: Ready for Raspberry Pi via Portainer
- **Automated Archiving**: Weekly cron job zips and archives charts
- **n8n Integration**: Workflow templates included

## Quick Start

### Local Usage

```bash
# Install dependencies
pip install -r docker/requirements.txt

# Generate a daily chart (no indicators)
python src/tradingview_screenshot.py NASDAQ:AAPL -i 1D

# Generate a 4-hour chart with default indicators (MACD, RSI)
python src/tradingview_screenshot.py NASDAQ:AAPL -i 4h -s

# Generate a chart with custom indicators
python src/tradingview_screenshot.py NASDAQ:AAPL -i 1h -s BB,VWAP,RSI
```

### Docker Deployment (Raspberry Pi)

1. Create directories on host:
   ```bash
   mkdir -p /home/pi/tradingview-screenshot/charts
   mkdir -p /home/pi/tradingview-screenshot/archives
   ```

2. Deploy via Portainer:
   - Go to **Stacks** > **Add Stack**
   - Select **Repository** and enter your Git URL
   - Set **Compose path**: `docker/docker-compose.yml`
   - Add **Environment variable**: `ROOT_PASSWORD` = `your_password`
   - Click **Deploy**

3. Generate charts via SSH:
   ```bash
   ssh -p 2222 root@<raspi-ip> "tradingview-screenshot NASDAQ:AAPL -i 1D"
   ```

See [docker/DEPLOYMENT.md](docker/DEPLOYMENT.md) for detailed deployment instructions.

## REST API

The tool includes a FastAPI-based REST API for programmatic access.

### API Setup

1. Create a `key.md` file in the project root with your API key:
   ```bash
   echo "YourSecretAPIKey123" > key.md
   ```

2. Install dependencies:
   ```bash
   pip install -r docker/requirements.txt
   ```

3. Start the API server:
   ```bash
   cd src
   python -m uvicorn api:app --host 0.0.0.0 --port 8000
   ```

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/intervals` | Yes | List available intervals |
| GET | `/api/indicators` | Yes | List indicator shortcuts |
| POST | `/api/chart/generate` | Yes | Generate chart screenshot |
| GET | `/api/chart/download/{filename}` | Yes | Download chart file |
| GET | `/api/chart/list` | Yes | List generated charts |
| GET | `/api/archive/list` | Yes | List archives |
| POST | `/api/archive/trigger` | Yes | Trigger manual archive |
| GET | `/api/archive/download/{filename}` | Yes | Download archive |

### Authentication

All endpoints (except `/health`) require a Bearer token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YourSecretAPIKey123" http://localhost:8000/api/intervals
```

### Example: Generate Chart

```bash
curl -X POST http://localhost:8000/api/chart/generate \
  -H "Authorization: Bearer YourSecretAPIKey123" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "NASDAQ:AAPL", "interval": "1D", "studies": ["MACD", "RSI"]}'
```

Response:
```json
{
  "success": true,
  "filename": "tradingview_1D_chart_NASDAQ_AAPL_indicators.png",
  "html_filename": "tradingview_1D_chart_NASDAQ_AAPL_indicators.html",
  "message": "Chart generated successfully"
}
```

### Interactive API Docs

Swagger UI available at: `http://localhost:8000/docs`

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `TICKER` | Stock symbol (e.g., NASDAQ:AAPL, NYSE:IBM) | Required |
| `-i, --interval` | Time interval: 15m, 1h, 4h, 1D, 1W (case-insensitive) | 1D |
| `-s, --studies` | Technical indicators (optional value) | None |
| `-o, --output` | Output directory | Current directory |

**Note:** Intervals are case-insensitive. `15m`, `15M`, `1h`, `1H`, `4h`, `4H`, `1d`, `1D`, `1w`, `1W` all work.

### Indicator Examples

```bash
# No indicators
tradingview-screenshot NASDAQ:AAPL -i 1D

# Default indicators (MACD, RSI)
tradingview-screenshot NASDAQ:AAPL -i 4h -s

# Custom indicators
tradingview-screenshot NASDAQ:AAPL -i 4h -s BB,VWAP
tradingview-screenshot NASDAQ:AAPL -i 1h -s "MACD,RSI,DMI,BB"
```

### Supported Indicators

Common shortcuts: `MACD`, `RSI`, `DMI`, `BB`, `VWAP`, `EMA`, `SMA`, `ATR`, `OBV`, `MFI`, `CCI`, `STOCH`, `ADX`, `PSAR`, `ICHIMOKU`

Any TradingView study name is supported (e.g., `Volume`, `VWMA`, `Momentum`).

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - valid chart generated |
| 1 | Error - invalid ticker or render failure |

## Project Structure

```
tradingview-screenshot/
├── src/
│   ├── tradingview_screenshot.py    # Main Python script (CLI)
│   └── api.py                       # FastAPI REST API
├── docker/
│   ├── Dockerfile                   # Container build instructions
│   ├── docker-compose.yml           # Stack configuration
│   ├── requirements.txt             # Python dependencies
│   ├── archive_charts.sh            # Weekly archive script
│   ├── entrypoint.sh                # Container startup script
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── .env.example                 # Environment template
│   └── .env                         # Environment config (not in git)
├── n8n/
│   ├── n8n_node_chart_normal.json   # n8n workflow (no indicators)
│   └── n8n_node_chart_indicators.json
├── key.md                           # API key (not in git)
├── spec.md                          # Project specification
└── README.md
```

## Output Files

Generated files follow this naming convention:

```
tradingview_{interval}_chart_{EXCHANGE}_{SYMBOL}.png
tradingview_{interval}_chart_{EXCHANGE}_{SYMBOL}_indicators.png  # When -s used
tradingview_{interval}_chart_{EXCHANGE}_{SYMBOL}.html
```

Example: `tradingview_4h_chart_NASDAQ_AAPL_indicators.png`

## Docker Configuration

Copy the environment template and configure:

```bash
cp docker/.env.example docker/.env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `ROOT_PASSWORD` | SSH root password | (set in .env) |
| `TZ` | Container timezone | Europe/Berlin |

| Setting | Default | Description |
|---------|---------|-------------|
| SSH Port | 2222 | External SSH port |
| Archive Schedule | Sunday 23:30 | Weekly archive cron |

## Requirements

- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver
- Selenium
- FastAPI + Uvicorn (for REST API)

## License

MIT
