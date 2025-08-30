#!/usr/bin/env bash
set -euo pipefail

#!/usr/bin/env bash
BACKEND_IMAGE="$1"
FRONTEND_IMAGE="$2"
DEPLOY_PATH="${3:-/opt/backtest}"

# ensure deploy path exists
mkdir -p "${DEPLOY_PATH}"
chown $(whoami) "${DEPLOY_PATH}" 2>/dev/null || true

# Create override file directly in deploy path (atomic move reduces race)
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

# Show merged config for verification
docker compose -f docker-compose.yml -f override-images.yml config || true

# Deploy without building locally
docker compose -f docker-compose.yml -f override-images.yml up -d --remove-orphans --no-build

# health checks
sleep 5
curl -f http://localhost:8000/health || echo "Backend health check failed"
curl -f http://localhost:8080 || echo "Frontend health check failed"

# Optional: rotate old compose or notify

echo "Deployment finished"
