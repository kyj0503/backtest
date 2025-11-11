#!/bin/bash
set -e

# 사용법: deploy.sh <backend-image> <frontend-image>
BE_IMAGE=$1
FE_IMAGE=$2

if [ -z "$BE_IMAGE" ] || [ -z "$FE_IMAGE" ]; then
    echo "Usage: deploy.sh <backend-image> <frontend-image>"
    exit 1
fi

DEPLOY_DIR="/opt/backtest"
COMPOSE_FILE="$DEPLOY_DIR/compose.yml"

echo "=========================================="
echo "Starting deployment process"
echo "Backend Image: $BE_IMAGE"
echo "Frontend Image: $FE_IMAGE"
echo "=========================================="

# 배포 디렉토리로 이동
cd "$DEPLOY_DIR"

# 새 이미지 pull
echo "Pulling new images..."
docker pull "$BE_IMAGE"
docker pull "$FE_IMAGE"

# latest 태그 업데이트
echo "Updating latest tags..."
docker tag "$BE_IMAGE" "ghcr.io/kyj0503/backtest-be:latest"
docker tag "$FE_IMAGE" "ghcr.io/kyj0503/backtest-fe:latest"

# 기존 컨테이너 중지 및 제거
echo "Stopping and removing old containers..."
docker compose -f "$COMPOSE_FILE" down || true

# 새 컨테이너 시작
echo "Starting new containers..."
docker compose -f "$COMPOSE_FILE" up -d

# 헬스체크 대기
echo "Waiting for services to be healthy..."
sleep 10

# 컨테이너 상태 확인
echo "Checking container status..."
docker compose -f "$COMPOSE_FILE" ps

# 사용하지 않는 이미지 정리
echo "Cleaning up unused images..."
docker image prune -f

echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
