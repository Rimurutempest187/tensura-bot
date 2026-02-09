#!/usr/bin/env bash
set -euo pipefail

# Optional: allow overriding the command
if [ "${1:-}" = "shell" ]; then
  /bin/bash
  exit 0
fi

# Ensure required env var exists
if [ -z "${BOT_TOKEN:-}" ]; then
  echo "ERROR: BOT_TOKEN environment variable is not set."
  exit 1
fi

# If requirements.txt changed after build, ensure installed (safe idempotent)
if [ -f "/app/requirements.txt" ]; then
  pip install --no-cache-dir -r /app/requirements.txt || true
fi

# Simple supervisor loop to restart on crash (keeps container alive)
MAX_RESTARTS=${MAX_RESTARTS:-5}
RESTART_DELAY=${RESTART_DELAY:-5}
count=0

while true; do
  python /app/main.py && break
  count=$((count+1))
  if [ "$count" -ge "$MAX_RESTARTS" ]; then
    echo "Exceeded max restarts ($MAX_RESTARTS). Exiting."
    exit 1
  fi
  echo "App crashed. Restarting in ${RESTART_DELAY}s (attempt $count/$MAX_RESTARTS)..."
  sleep "$RESTART_DELAY"
done
