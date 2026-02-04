# Use Debian Trixie as base (ARM64 compatible for Raspberry Pi)
FROM debian:trixie-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    chromium \
    chromium-driver \
    openssh-server \
    cron \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy application files
COPY src/tradingview_screenshot.py /app/
COPY src/api.py /app/
COPY docker/requirements.txt /app/
COPY docker/archive_charts.sh /app/

# Create virtual environment and install Python dependencies
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Create output and archive directories (same path as host)
RUN mkdir -p /home/pi/tradingview-screenshot/charts /home/pi/tradingview-screenshot/archives

# Configure SSH
RUN mkdir -p /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Root password is set at runtime via entrypoint.sh using ROOT_PASSWORD env var

# Create wrapper script for easy execution
RUN echo '#!/bin/bash\n/app/venv/bin/python /app/tradingview_screenshot.py -o /home/pi/tradingview-screenshot/charts "$@"' > /usr/local/bin/tradingview-screenshot \
    && chmod +x /usr/local/bin/tradingview-screenshot

# Make archive script executable
RUN chmod +x /app/archive_charts.sh

# Set up crontab for weekly archiving (Sunday 23:30)
RUN echo "30 23 * * 0 /app/archive_charts.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/archive-charts \
    && chmod 0644 /etc/cron.d/archive-charts \
    && crontab /etc/cron.d/archive-charts

# Create log file for cron
RUN touch /var/log/cron.log

# Expose SSH and API ports
EXPOSE 22
EXPOSE 8000

# Copy and set entrypoint script
COPY docker/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Start services via entrypoint
CMD ["/app/entrypoint.sh"]
