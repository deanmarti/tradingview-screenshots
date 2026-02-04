#!/bin/bash
# Entrypoint script - starts cron, FastAPI, and SSH

# Set root password from environment variable
if [ -n "$ROOT_PASSWORD" ]; then
    echo "root:$ROOT_PASSWORD" | chpasswd
fi

# Start cron daemon
echo "Starting cron..."
cron

# Start FastAPI server in background
echo "Starting FastAPI API server on port 8000..."
cd /app && /app/venv/bin/python -m uvicorn api:app --host 0.0.0.0 --port 8000 >> /var/log/api.log 2>&1 &

# Start SSH daemon in foreground
echo "Starting SSH..."
exec /usr/sbin/sshd -D
