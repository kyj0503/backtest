#!/usr/bin/env bash
set -euo pipefail

# 스마트 포트 배포 스크립트
DEPLOY_PATH="${1:-/opt/backtest}"

# 기본 포트 설정
DEFAULT_BACKEND_PORT=8001
DEFAULT_FRONTEND_PORT=8082

# 포트 사용 가능 여부 확인
check_port() {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        return 1  # 사용 중
    else
        return 0  # 사용 가능
    fi
}

# 사용 가능한 포트 찾기
find_alternative_port() {
    local base_port=$1
    local port=$base_port
    while ! check_port $port; do
        ((port++))
        if [ $port -gt $((base_port + 100)) ]; then
            echo "ERROR: Cannot find available port near $base_port" >&2
            exit 1
        fi
    done
    echo $port
}

# 포트 결정
if check_port $DEFAULT_BACKEND_PORT; then
    BACKEND_PORT=$DEFAULT_BACKEND_PORT
    echo "✅ Backend: Using default port $BACKEND_PORT"
else
    BACKEND_PORT=$(find_alternative_port $DEFAULT_BACKEND_PORT)
    echo "⚠️  Backend: Port $DEFAULT_BACKEND_PORT busy, using $BACKEND_PORT"
fi

if check_port $DEFAULT_FRONTEND_PORT; then
    FRONTEND_PORT=$DEFAULT_FRONTEND_PORT
    echo "✅ Frontend: Using default port $FRONTEND_PORT"
else
    FRONTEND_PORT=$(find_alternative_port $DEFAULT_FRONTEND_PORT)
    echo "⚠️  Frontend: Port $DEFAULT_FRONTEND_PORT busy, using $FRONTEND_PORT"
fi

# Docker Compose 파일 동적 수정
sed -i "s|\"[0-9]*:8000\"|\"$BACKEND_PORT:8000\"|g" "$DEPLOY_PATH/docker-compose.yml"
sed -i "s|\"[0-9]*:80\"|\"$FRONTEND_PORT:80\"|g" "$DEPLOY_PATH/docker-compose.yml"

echo "📝 Updated docker-compose.yml with ports: Backend=$BACKEND_PORT, Frontend=$FRONTEND_PORT"

# 서비스 정보 저장 (Nginx나 다른 서비스가 참조 가능)
cat > "$DEPLOY_PATH/service-ports.env" <<EOF
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_URL=http://localhost:$BACKEND_PORT
FRONTEND_URL=http://localhost:$FRONTEND_PORT
EOF

echo "💾 Service configuration saved to service-ports.env"
