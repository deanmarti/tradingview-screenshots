# TradingView Screenshot Tool - Deployment Manual

## Overview
Deploy the TradingView Screenshot Tool on a Raspberry Pi using Portainer.

## Prerequisites
- Raspberry Pi with Debian/Raspbian
- Docker and Portainer installed
- Internet connection

---

## Directory Structure on Host

```
/home/pi/tradingview-screenshots/
├── charts/           # Generated chart files (PNG, HTML)
└── archives/         # Weekly zip archives
```

Create directories:
```bash
mkdir -p /home/pi/tradingview-screenshots/charts
mkdir -p /home/pi/tradingview-screenshots/archives
```

---

## Deployment via Portainer

### Option 1: Build from Git Repository

1. Open Portainer → **Stacks** → **Add Stack**
2. Name: `tradingview-screenshot`
3. Select **Repository**
4. Enter your Git repository URL
5. Set **Compose path**: `docker/docker-compose.yml`
6. Click **Deploy the stack**

### Option 2: Upload Files

1. Copy all files to Raspberry Pi:
   ```bash
   scp -r * pi@<raspi-ip>:/home/pi/tradingview-build/
   ```

2. SSH into Raspberry Pi and build:
   ```bash
   cd /home/pi/tradingview-build
   docker build -t tradingview-screenshot:latest -f docker/Dockerfile .
   ```

3. In Portainer → **Stacks** → **Add Stack**
4. Name: `tradingview-screenshot`
5. Paste the contents of `docker/docker-compose.yml` in the Web editor
6. Click **Deploy the stack**

### Option 3: Web Editor (Copy & Paste)

1. In Portainer → **Stacks** → **Add Stack**
2. Name: `tradingview-screenshot`
3. Paste this in the Web editor:

```yaml
version: '3.8'

services:
  tradingview-screenshot:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    image: tradingview-screenshot:latest
    container_name: tradingview-screenshot
    hostname: tradingview-screenshot
    restart: unless-stopped
    ports:
      - "2222:22"
    volumes:
      - /home/pi/tradingview-screenshots/charts:/app/output
      - /home/pi/tradingview-screenshots/archives:/app/archives
    env_file:
      - .env
    environment:
      - ROOT_PASSWORD=${ROOT_PASSWORD}
      - TZ=${TZ}
    shm_size: '2gb'
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
```

**Note:** Create a `.env` file in the `docker/` directory (see `.env.example` for template).

---

## Project Structure

```
tradingview-screenshots/
├── src/
│   └── tradingview_screenshot.py    # Main Python script
├── docker/
│   ├── Dockerfile                   # Container build instructions
│   ├── docker-compose.yml           # Stack configuration
│   ├── requirements.txt             # Python dependencies
│   ├── archive_charts.sh            # Weekly archive script
│   ├── entrypoint.sh                # Container startup script
│   └── DEPLOYMENT.md                # This deployment guide
├── n8n/
│   ├── n8n_node_chart_normal.json   # n8n workflow (no indicators)
│   └── n8n_node_chart_indicators.json # n8n workflow (with indicators)
├── spec.md                          # Project specification
└── todo.md                          # Task tracking
```

---

## Usage

### Connect via SSH
```bash
ssh -p 2222 root@<raspi-ip>
# Password: Home4Charts8115$
```

### Generate Charts
```bash
# No indicators (chart only)
tradingview-screenshot NASDAQ:AAPL -i 1D

# With default indicators (MACD, RSI)
tradingview-screenshot NASDAQ:AAPL -i 4h -s

# With custom indicators
tradingview-screenshot NASDAQ:AAPL -i 4h -s BB,VWAP
```

### Run Remotely (Single Command)
```bash
ssh -p 2222 root@<raspi-ip> "tradingview-screenshot NASDAQ:AAPL -i 1D"
```

---

## Output Locations

| Location (Container) | Location (Host) | Description |
|---------------------|-----------------|-------------|
| `/app/output/` | `/home/pi/tradingview-screenshots/charts/` | Generated charts |
| `/app/archives/` | `/home/pi/tradingview-screenshots/archives/` | Weekly zip archives |

---

## Automated Weekly Archive

A cron job runs every **Sunday at 23:30** that:
1. Zips all PNG and HTML files in `/app/output/`
2. Saves archive to `/app/archives/charts_YYYY-MM-DD.zip`
3. Removes archived files from output directory

### Manual Archive
```bash
ssh -p 2222 root@<raspi-ip> "/app/archive_charts.sh"
```

### Check Cron Log
```bash
ssh -p 2222 root@<raspi-ip> "cat /var/log/cron.log"
```

---

## Configuration

### Environment Variables

Configuration is stored in `docker/.env`. Copy the example file and customize:

```bash
cp docker/.env.example docker/.env
nano docker/.env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `ROOT_PASSWORD` | SSH root password | (set in .env) |
| `TZ` | Container timezone | Europe/Berlin |

### SSH Port
Default: `2222` (change in `docker-compose.yml` under `ports`)

---

## Troubleshooting

### View Container Logs (Portainer)
1. Go to **Containers** → `tradingview-screenshot`
2. Click **Logs**

### View Container Logs (CLI)
```bash
docker logs tradingview-screenshot
```

### Restart Container
```bash
docker restart tradingview-screenshot
```

### Enter Container Shell
```bash
docker exec -it tradingview-screenshot /bin/bash
```

### Rebuild After Code Changes
```bash
cd /home/pi/tradingview-build
docker build -t tradingview-screenshot:latest -f docker/Dockerfile .
docker restart tradingview-screenshot
```

---

## Command Reference

| Command | Description |
|---------|-------------|
| `tradingview-screenshot TICKER` | Generate chart (1D, no indicators) |
| `tradingview-screenshot TICKER -i 4h` | Generate 4-hour chart |
| `tradingview-screenshot TICKER -s` | Chart with MACD,RSI indicators |
| `tradingview-screenshot TICKER -s BB,RSI` | Chart with custom indicators |
| `/app/archive_charts.sh` | Manually archive charts |

## Exit Codes
- `0` - Success (valid chart generated)
- `1` - Error (invalid ticker or chart render failed)
