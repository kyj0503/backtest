#!/usr/bin/env bash
set -euo pipefail

BACKEND_IMAGE="$1"
FRONTEND_IMAGE="$2"
DEPLOY_PATH="${3:-/opt/backtest}"

# ensure deploy path exists
mkdir -p "${DEPLOY_PATH}"

# Create override file directly in deploy path
cat > "${DEPLOY_PATH}/override-images.yml" <<YAML
services:
  backend:
    image: ${BACKEND_IMAGE}
  frontend:
    image: ${FRONTEND_IMAGE}
YAML

# Pull images (best-effort)
docker pull "${BACKEND_IMAGE}" || true
docker pull "${FRONTEND_IMAGE}" || true

# Show merged config for verification using absolute paths
docker compose -f "${DEPLOY_PATH}/docker-compose.yml" -f "${DEPLOY_PATH}/override-images.yml" config || true

# Deploy without building locally
docker compose -f "${DEPLOY_PATH}/docker-compose.yml" -f "${DEPLOY_PATH}/override-images.yml" up -d --remove-orphans --no-build

# health checks
sleep 5
curl -f http://localhost:8000/health || echo "Backend health check failed"
curl -f http://localhost:8080 || echo "Frontend health check failed"

echo "Deployment finished"
