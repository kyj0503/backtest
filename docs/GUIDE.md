# 개발 가이드

이 문서는 백테스팅 시스템 개발 시 따라야 할 가이드라인을 설명합니다.

## 개발 프로세스

### 기능 수정/추가 후 필수 절차
모든 기능 수정이나 추가가 완료되면 다음 절차를 따라야 합니다:

1. 도커 빌드 및 테스트
```bash
# 전체 시스템 빌드
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 테스트 실행
./scripts/test-runner.sh unit
./scripts/test-runner.sh integration

# 수동 기능 테스트
# 브라우저에서 http://localhost:5174 접속하여 주요 기능 확인
```

2. 문제가 없을 경우 커밋
```bash
git add -A
git commit -m "feat: 기능 설명

- 변경사항 1
- 변경사항 2
- 테스트 완료"
```

### API 개발 가이드

#### 네이버 뉴스 API 사용 시 주의사항
- `display` 매개변수는 반드시 10 이상으로 설정해야 정상 작동
- 10 미만으로 설정할 경우 빈 결과 또는 오류 발생 가능

#### 백엔드 API 응답 형식
모든 API는 다음 형식을 따라야 합니다:
```json
{
  "status": "success" | "error",
  "message": "사용자 친화적 메시지",
  "data": { /* 실제 데이터 */ }
}
```

#### 프론트엔드 컴포넌트 가이드
- 단일 종목과 포트폴리오 백테스트는 동일한 UI 구성 요소를 표시해야 함
- 모든 백테스트 결과에는 '포트폴리오 성과 요약'이 포함되어야 함
- 매수후보유 전략에서는 거래 내역을 표시하지 않음

### 테스트 가이드
- 단위 테스트: 개별 함수/클래스 테스트
- 통합 테스트: API 엔드포인트 및 데이터베이스 연동 테스트
- 수동 테스트: 브라우저에서 사용자 시나리오 검증

### 코드 정리
로컬 개발 시 불필요한 캐시 파일 정리:
```bash
# npm 캐시 정리
rm -rf frontend/node_modules frontend/.npm frontend/package-lock.json

# Python 캐시 정리  
find backend -name "__pycache__" -type d -exec rm -rf {} +
find backend -name "*.pyc" -delete

# 기타 캐시 파일
rm -rf .pytest_cache .coverage
```

모든 빌드와 실행은 도커 환경에서 수행하므로 로컬 의존성은 제거해도 됩니다.
