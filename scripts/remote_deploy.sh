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

TIMESTAMP=$(date --iso-8601=seconds)
LOGFILE="${DEPLOY_PATH}/deploy.log"

echo "[${TIMESTAMP}] Starting deploy: backend=${BACKEND_IMAGE} frontend=${FRONTEND_IMAGE}" | tee -a "${LOGFILE}"

# Show merged config for verification using absolute paths
docker compose -f "${DEPLOY_PATH}/docker-compose.yml" -f "${DEPLOY_PATH}/override-images.yml" config || true

# Attempt deployment with rollback on failure
PREV_OVERRIDE="${DEPLOY_PATH}/override-images.yml.bak"
if [ -f "${DEPLOY_PATH}/override-images.yml" ]; then
  cp "${DEPLOY_PATH}/override-images.yml" "${PREV_OVERRIDE}.$(date +%s)" || true
fi

if docker compose -f "${DEPLOY_PATH}/docker-compose.yml" -f "${DEPLOY_PATH}/override-images.yml" up -d --remove-orphans --no-build; then
  echo "[${TIMESTAMP}] Deploy succeeded" | tee -a "${LOGFILE}"
  STATUS=success
else
  echo "[${TIMESTAMP}] Deploy failed — attempting rollback" | tee -a "${LOGFILE}"
  STATUS=failure
  # Find latest backup (if any) and restore
  LATEST_BACKUP=$(ls -1t ${DEPLOY_PATH}/override-images.yml.bak.* 2>/dev/null | head -n1 || true)
  if [ -n "${LATEST_BACKUP}" ]; then
    echo "Restoring backup override: ${LATEST_BACKUP}" | tee -a "${LOGFILE}"
    cp "${LATEST_BACKUP}" "${DEPLOY_PATH}/override-images.yml"
    docker compose -f "${DEPLOY_PATH}/docker-compose.yml" -f "${DEPLOY_PATH}/override-images.yml" up -d --remove-orphans --no-build || true
  else
    echo "No backup override found; manual intervention required" | tee -a "${LOGFILE}"
  fi
fi

# health checks (best-effort)
sleep 5
curl -f http://localhost:8001/health || echo "Backend health check failed" | tee -a "${LOGFILE}"
curl -f http://localhost:8081 || echo "Frontend health check failed" | tee -a "${LOGFILE}"

# Optional webhook notification if DEPLOY_NOTIFY_WEBHOOK is set
if [ -n "${DEPLOY_NOTIFY_WEBHOOK:-}" ]; then
  PAYLOAD="{\"status\":\"${STATUS}\",\"backend\":\"${BACKEND_IMAGE}\",\"frontend\":\"${FRONTEND_IMAGE}\",\"time\":\"${TIMESTAMP}\"}"
  curl -s -X POST -H 'Content-Type: application/json' -d "${PAYLOAD}" "${DEPLOY_NOTIFY_WEBHOOK}" || true
fi

echo "[${TIMESTAMP}] Deployment finished with status=${STATUS}" | tee -a "${LOGFILE}"

# Exit non-zero if deployment failed
if [ "${STATUS}" = "failure" ]; then
  exit 1
fi
