#!/bin/bash
set -e

# Ensure venv exists and dependencies installed (idempotent)
VENV_DIR=${VENV_DIR:-/opt/venv}
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
  echo "[entrypoint] Creating virtualenv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  export PATH="$VENV_DIR/bin:$PATH"
  if [ -f /requirements.txt ]; then
    echo "[entrypoint] Installing requirements.txt"
    pip install --no-cache-dir -r /requirements.txt || true
  fi
fi

# Fix permissions for mounted volumes (if needed)
if [ -d "$VENV_DIR" ]; then
  chown -R root:root "$VENV_DIR" || true
fi

echo "[entrypoint] Starting: $@"
exec "$@"
