#!/bin/bash
set -e

# Ensure venv exists and dependencies installed (idempotent)
VENV_DIR=${VENV_DIR:-/opt/venv}
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
  echo "[entrypoint] Creating virtualenv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  export PATH="$VENV_DIR/bin:$PATH"
  if [ -f /app/requirements.txt ]; then
    echo "[entrypoint] Installing requirements.txt"
    pip install --no-cache-dir -r /app/requirements.txt
  fi
fi

# Clean up Prometheus multiprocess directory
if [ -n "$PROMETHEUS_MULTIPROC_DIR" ]; then
  echo "[entrypoint] Clearing Prometheus multiprocess directory: $PROMETHEUS_MULTIPROC_DIR"
  rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*
fi

echo "[entrypoint] Starting: $@"
exec "$@"
