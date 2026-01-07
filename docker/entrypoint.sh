#!/bin/bash
# Entrypoint script - starts cron and SSH

# Set root password from environment variable
if [ -n "$ROOT_PASSWORD" ]; then
    echo "root:$ROOT_PASSWORD" | chpasswd
fi

# Start cron daemon
echo "Starting cron..."
cron

# Start SSH daemon in foreground
echo "Starting SSH..."
exec /usr/sbin/sshd -D
