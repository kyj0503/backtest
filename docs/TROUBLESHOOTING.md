# 트러블슈팅 가이드

이 문서는 백테스팅 시스템에서 발생한 버그 해결, 문제 해결, 패치 내역을 날짜별로 기록합니다.

## 목차

1. [2025년 9월](#2025년-9월)
2. [트러블슈팅 가이드라인](#트러블슈팅-가이드라인)
3. [자주 발생하는 문제](#자주-발생하는-문제)

---

## 2025년 9월

### 2025-09-11

#### 🐛 뉴스 검색 기능 개선 (2차 수정)
**문제**: 백테스트 실행 후 "뉴스 보기"를 클릭하면 "이 기간의 뉴스가 없다"고 표시되는 문제 (1차 수정 후에도 여전히 발생)

**원인**: 
- API 호출 방식의 문제 (fetch 직접 호출 vs API 서비스 사용)
- `getApiBaseUrl()` 함수와 상대 경로 처리 불일치
- 백엔드 API 응답 구조와 프론트엔드 기대값 불일치

**해결방법**:
- `backtestApiService.searchNews()` 메서드 새로 추가
- fetch 직접 호출 대신 기존 API 서비스 패턴 사용
- 상대 경로 기반 API 호출로 프록시 설정 활용

**수정 파일**: 
- `frontend/src/services/api.ts` - searchNews 메서드 추가
- `frontend/src/hooks/useVolatilityNews.ts` - API 호출 방식 변경

**커밋**: `fix: improve news search using proper API service`

---

#### 🐛 뉴스 검색 기능 개선
**문제**: 백테스트 실행 후 "뉴스 보기"를 클릭하면 "이 기간의 뉴스가 없다"고 표시되는 문제

**원인**: 
- 특정 날짜 범위로 뉴스 검색 시 결과가 없는 경우가 많음
- 복잡한 날짜 기반 검색 로직이 실패하는 경우 발생

**해결방법**:
- API 가이드에 명시된 간단한 뉴스 검색 엔드포인트 사용
- `GET /api/v1/naver-news/search?query=회사명&display=10` 형태로 단순화
- 날짜 제한 없이 회사명만으로 관련 뉴스 검색

**수정 파일**: `frontend/src/hooks/useVolatilityNews.ts`
```typescript
// 기존: 복잡한 날짜 기반 검색 + fallback
// 변경: 간단한 회사명 검색
const apiUrl = `${baseUrl}/api/v1/naver-news/search?query=${encodeURIComponent(companyName)}&display=10`;
```

**커밋**: `fix: simplify news search to use company name only`

---

#### 🎯 6가지 주요 시스템 이슈 해결
**이전 세션에서 해결된 주요 문제들**:

1. **WebSocket 채팅 서버 연결 문제**
   - 파일: `frontend/src/pages/ChatPage.tsx`
   - 해결: URL 생성 로직 개선, localhost:8001 폴백 추가

2. **포트폴리오 백테스트 뉴스 표시 문제**
   - 파일: `backend/app/services/portfolio_service.py`
   - 해결: `unique_key` 대신 `original_symbol` 사용

3. **뉴스 검색 fallback 기능 부족**
   - 파일: `frontend/src/hooks/useVolatilityNews.ts`
   - 해결: 전체 기간 재검색 로직 추가

4. **중복 종목 처리 오류 (META_0 문제)**
   - 파일: `backend/app/services/portfolio_service.py`
   - 해결: 원본 심볼 사용으로 데이터 로딩 수정

5. **포트폴리오 지표 누락 문제**
   - 파일: `backend/app/services/portfolio_service.py`
   - 해결: Profit Factor 계산 및 반환 로직 추가

6. **금융 용어 도움말 기능 부재**
   - 파일: `frontend/src/components/common/FinancialTermTooltip.tsx` (신규)
   - 해결: 25개 이상 금융 용어 툴팁 시스템 구현

---

## 트러블슈팅 가이드라인

### 문제 보고 양식
새로운 문제를 발견했을 때는 다음 정보를 포함하여 이 문서에 기록해주세요:

```markdown
#### 🐛 문제 제목
**문제**: 문제 상황 상세 설명

**재현 단계**:
1. 단계 1
2. 단계 2
3. 단계 3

**예상 결과**: 기대했던 동작
**실제 결과**: 실제 발생한 동작

**원인**: 문제의 근본 원인
**해결방법**: 적용한 해결책
**수정 파일**: 변경된 파일 목록
**커밋**: 관련 커밋 메시지
```

### 우선순위 분류
- 🔥 **Critical**: 시스템 전체 중단
- 🐛 **High**: 주요 기능 장애
- ⚠️ **Medium**: 부분 기능 문제
- 💡 **Low**: 개선 사항

### 테스트 체크리스트
문제 해결 후 다음 사항들을 확인하세요:

- [ ] 유닛 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 수동 테스트 완료
- [ ] 관련 기능 회귀 테스트
- [ ] 문서 업데이트

---

## 자주 발생하는 문제

### 1. Docker 컨테이너 관련
**문제**: 컨테이너가 시작되지 않거나 연결 실패

**해결책**:
```bash
# 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs [service-name]

# 컨테이너 재시작
docker compose restart [service-name]

# 완전히 재빌드
docker compose down && docker compose up --build
```

### 2. 프론트엔드 빌드 오류
**문제**: npm 의존성 또는 TypeScript 컴파일 오류

**해결책**:
```bash
# 의존성 재설치
rm -rf node_modules package-lock.json
npm install

# TypeScript 검사
npm run type-check

# Lint 검사
npm run lint
```

### 3. 백엔드 API 오류
**문제**: FastAPI 서버 오류 또는 데이터베이스 연결 실패

**해결책**:
```bash
# 서버 로그 확인
docker compose logs backend

# 데이터베이스 연결 테스트
curl http://localhost:8001/health

# 의존성 재설치
pip install -r requirements.txt
```

### 4. 뉴스 API 오류
**문제**: 네이버 뉴스 검색 실패 또는 응답 없음

**해결책**:
- API 키 유효성 확인
- 요청 제한 확인 (1일 25,000건)
- 쿼리 형식 검증
- 네트워크 연결 상태 확인

### 5. 종목 데이터 오류
**문제**: yfinance 데이터 조회 실패

**해결책**:
- 종목 심볼 유효성 확인
- 날짜 범위 검증
- yfinance 라이브러리 업데이트
- 대체 데이터 소스 사용

---

## 관련 문서
- [API 가이드](./API_GUIDE.md) - API 엔드포인트 및 사용법
- [개발 가이드](./GUIDE.md) - 개발 환경 설정
- [실행 가이드](./RUNBOOK.md) - 배포 및 운영

---

**📝 문제 발생 시 이 문서에 기록해주세요!**
