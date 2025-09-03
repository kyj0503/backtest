#!/usr/bin/env bash
set -euo pipefail

BACKEND_IMAGE="$1"
FRONTEND_IMAGE="$2"
DEPLOY_PATH="${3:-/opt/backtest}"

# ensure deploy path exists
mkdir -p "${DEPLOY_PATH}"

# Update the docker-compose.yml file directly with the new image tags
sed -i "s|image: backtest-backend:latest|image: ${BACKEND_IMAGE}|g" "${DEPLOY_PATH}/docker-compose.yml"
sed -i "s|image: backtest-frontend:latest|image: ${FRONTEND_IMAGE}|g" "${DEPLOY_PATH}/docker-compose.yml"

# Pull images (best-effort)
docker pull "${BACKEND_IMAGE}" || true
docker pull "${FRONTEND_IMAGE}" || true

TIMESTAMP=$(date --iso-8601=seconds)
LOGFILE="${DEPLOY_PATH}/deploy.log"

echo "[${TIMESTAMP}] Starting deploy: backend=${BACKEND_IMAGE} frontend=${FRONTEND_IMAGE}" | tee -a "${LOGFILE}"

# Show current config for verification
echo "Current docker-compose.yml configuration:" | tee -a "${LOGFILE}"
cat "${DEPLOY_PATH}/docker-compose.yml" | tee -a "${LOGFILE}"

# Attempt deployment with rollback on failure
BACKUP_COMPOSE="${DEPLOY_PATH}/docker-compose.yml.bak.$(date +%s)"
if [ -f "${DEPLOY_PATH}/docker-compose.yml" ]; then
  cp "${DEPLOY_PATH}/docker-compose.yml" "${BACKUP_COMPOSE}" || true
fi

if docker compose -f "${DEPLOY_PATH}/docker-compose.yml" up -d --remove-orphans --no-build; then
  echo "[${TIMESTAMP}] Deploy succeeded" | tee -a "${LOGFILE}"
  STATUS=success
else
  echo "[${TIMESTAMP}] Deploy failed — attempting rollback" | tee -a "${LOGFILE}"
  STATUS=failure
  # Find latest backup and restore
  LATEST_BACKUP=$(ls -1t ${DEPLOY_PATH}/docker-compose.yml.bak.* 2>/dev/null | head -n1 || true)
  if [ -n "${LATEST_BACKUP}" ]; then
    echo "Restoring backup compose: ${LATEST_BACKUP}" | tee -a "${LOGFILE}"
    cp "${LATEST_BACKUP}" "${DEPLOY_PATH}/docker-compose.yml"
    docker compose -f "${DEPLOY_PATH}/docker-compose.yml" up -d --remove-orphans --no-build || true
  else
    echo "No backup compose found; manual intervention required" | tee -a "${LOGFILE}"
  fi
fi

# health checks (best-effort)
sleep 5
curl -f http://localhost:8001/health || echo "Backend health check failed" | tee -a "${LOGFILE}"
curl -f http://localhost:8082 || echo "Frontend health check failed" | tee -a "${LOGFILE}"

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
