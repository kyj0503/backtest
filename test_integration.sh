#!/bin/bash

# 통합 테스트 스크립트
# 도커 환경에서 전체 시스템 테스트

set -e

echo "========================================="
echo "통합 테스트 시작"
echo "========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 결과 카운터
PASS=0
FAIL=0

# 테스트 함수
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "테스트: $name ... "
    
    status=$(curl --max-time 5 -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status)"
        ((FAIL++))
        return 1
    fi
}

echo ""
echo "1. 서비스 상태 확인"
echo "-------------------"
docker compose -f compose.dev.yaml ps

echo ""
echo "2. Health Check 테스트"
echo "----------------------"

test_endpoint "FastAPI Health" "http://localhost:8000/health" 200
test_endpoint "Spring Boot Health" "http://localhost:8080/actuator/health" 200
test_endpoint "Frontend (Vite)" "http://localhost:5173/" 200

echo ""
echo "3. API 엔드포인트 테스트"
echo "------------------------"

# Spring Boot API 테스트 (인증 불필요한 엔드포인트)
test_endpoint "Spring Boot Root" "http://localhost:8080/" 404  # 루트는 404 정상

# FastAPI 문서 페이지
test_endpoint "FastAPI Docs" "http://localhost:8000/api/v1/docs" 200

echo ""
echo "4. 로그 확인 (최근 30줄)"
echo "------------------------"

echo ""
echo "=== Spring Boot 로그 ==="
docker compose -f compose.dev.yaml logs backtest-be-spring --tail=10 | grep -v "^$"

echo ""
echo "=== FastAPI 로그 ==="
docker compose -f compose.dev.yaml logs backtest-be-fast --tail=10 | grep -v "^$"

echo ""
echo "========================================="
echo "테스트 결과 요약"
echo "========================================="
echo -e "통과: ${GREEN}$PASS${NC}"
echo -e "실패: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}모든 테스트 통과!${NC}"
    exit 0
else
    echo -e "${RED}일부 테스트 실패${NC}"
    exit 1
fi
