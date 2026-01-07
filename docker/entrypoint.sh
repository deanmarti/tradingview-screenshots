#!/bin/bash
# Entrypoint script - starts cron and SSH

# Start cron daemon
echo "Starting cron..."
cron

# Start SSH daemon in foreground
echo "Starting SSH..."
exec /usr/sbin/sshd -D
