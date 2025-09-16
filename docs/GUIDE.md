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
- 기본 검색 엔드포인트는 `display` 범위 1-100을 지원합니다.
- 날짜 범위 검색 엔드포인트(`/naver-news/search-by-date` 등)는 `display` 하한이 10이며 기본값 50입니다.
- 응답 구조는 `backend/app/api/v1/endpoints/naver_news.py`의 Pydantic 모델을 따릅니다.

#### 인증 API 응답 형식
`/api/v1/auth/login` 및 `/api/v1/auth/register`는 다음과 같은 JSON 응답을 반환합니다.

```json
{
  "token": "<세션 토큰>",
  "user_id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "investment_type": "balanced",
  "is_admin": false
}
```

응답은 `AuthResponse` 모델(`backend/app/api/v1/endpoints/auth.py`)을 기준으로 유지되며, 추가 필드를 도입할 때는 해당 모델과 DB 스키마를 함께 업데이트해야 합니다.


### 포트폴리오 비중(%) 직접 입력 UX
- 포트폴리오 구성 시 각 종목/자산의 "비중(%)" 칸에 사용자가 직접 값을 입력하면, 해당 값이 고정되어 amount(투자금액)와 무관하게 비중이 유지됩니다.
- amount(투자금액) 칸을 수정하면 해당 종목의 weight(비중)는 자동으로 해제되어, 전체 금액 비율로 다시 자동 계산됩니다.
- 비중 입력란이 비어 있으면, 현재 투자금액 기준 자동 계산된 비율이 표시됩니다.
- 비중 입력 시 합계가 100%가 아니면 에러가 표시되며, 모든 종목이 비중 입력 모드일 때만 금액이 자동으로 동기화됩니다.
- 금액 기반/비중 기반 입력은 혼용 불가(동일 포트폴리오 내에서 한 방식만 사용).

#### 주요 변경점
- 기존: 종목 2개 입력 시 50%/50%로 자동 고정, 사용자가 비중을 바꿔도 금액에 의해 덮어씌워짐
- 변경: 비중(%)을 직접 입력하면 해당 값이 유지되고, 금액을 수정하면 비중 입력이 해제되어 자동 계산으로 전환됨

#### 사용법
1. "비중(%)" 칸에 원하는 값을 직접 입력하면, 해당 종목의 투자 비중이 고정됩니다.
2. "투자 금액($)"을 수정하면 비중 입력이 해제되고, 전체 금액 대비 자동 계산된 비율이 표시됩니다.
3. 모든 종목의 비중 합이 100%가 되어야 하며, 합이 맞지 않으면 에러가 표시됩니다.
4. 금액 기반/비중 기반 입력은 혼용할 수 없습니다.

### 테스트 가이드
- 단위 테스트: 개별 함수/클래스 테스트
- 통합 테스트: API 엔드포인트 및 데이터베이스 연동 테스트
- 수동 테스트: 브라우저에서 사용자 시나리오 검증

### 코드 정리
모든 빌드와 실행은 도커 환경에서 수행합니다. 로컬 환경에서 의존성을 설치한 경우 아래 명령으로 정리할 수 있습니다.
```bash
# npm 캐시/설치본 정리 (필요한 경우에만)
rm -rf frontend/node_modules frontend/.npm frontend/package-lock.json

# Python 캐시 정리  
find backend -name "__pycache__" -type d -exec rm -rf {} +
find backend -name "*.pyc" -delete

# 테스트 산출물 정리
rm -rf .pytest_cache .coverage backend/htmlcov
```
정리 후에는 `docker compose` 기반 빌드로 필요한 의존성을 다시 설치하세요.
