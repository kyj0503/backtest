# 백테스팅 프로젝트 개발 가이드

이 저장소에서 AI 코딩 에이전트가 효율적으로 작업하기 위한 핵심 가이드입니다.

## 빠른 개요

백테스팅 시스템은 FastAPI 백엔드(포트 8001)와 Vite 기반 React 프론트엔드(개발: 5174, 프로덕션: 8082)로 구성됩니다. 투자 전략은 `backend/app/services/strategy_service.py`에 등록된 Strategy 클래스들을 사용해 `backtesting` 라이브러리로 실행됩니다.

## 아키텍처

### 기술 스택
- **백엔드**: FastAPI + uvicorn, Pydantic V2, MySQL 캐시, yfinance API
- **프론트엔드**: React 18 + TypeScript + Vite, Tailwind CSS, Recharts
- **배포**: Docker + Jenkins CI/CD, nginx 프록시

### 데이터 흐름
- **데이터 수집**: yfinance → MySQL 캐시 → 백테스트 엔진
- **뉴스 검색**: 네이버 검색 API → 70+ 종목 지원, 날짜별 필터링
- **자산 관리**: 주식(ticker 기반)과 현금(asset_type='cash') 구분 처리
- **현금 자산**: 무위험 자산으로 0% 수익률, 변동성 없음 보장

### API 구조
- `/api/v1/backtest/run` - 단일 종목 백테스트
- `/api/v1/backtest/chart-data` - 백테스트 차트 데이터
- `/api/v1/backtest/portfolio` - 포트폴리오 백테스트
- `/api/v1/naver-news/*` - 뉴스 검색
- `/api/v1/strategies/*` - 전략 관리
- `/api/v1/optimize/*` - 최적화
- `/api/v1/yfinance/*` - yfinance 캐시

## 개발 환경

### 실행 명령어
```bash
# 개발 환경 (윈도우 + PowerShell + Docker Desktop)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 백그라운드 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 컨테이너 중지
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# 테스트 실행
docker-compose exec backend pytest tests/ -v
```

### 접속 정보
- 프론트엔드: http://localhost:5174
- 백엔드: http://localhost:8001
- API 문서: http://localhost:8001/docs

## 현재 개발 상황

### 완료된 주요 기능
- **진짜 현금 자산 처리**: asset_type 필드로 현금('cash')과 주식('stock') 구분
- **Pydantic V2 완전 마이그레이션**: 모든 deprecated 경고 제거
- **Tailwind CSS 마이그레이션**: React Bootstrap에서 Tailwind CSS로 완전 전환
- **네이버 뉴스 API**: 70+ 종목 지원, 날짜별 필터링, 자동 콘텐츠 정제
- **완전 오프라인 모킹 시스템**: CI/CD 안정성 극대화

### Jenkins CI/CD 파이프라인 상태
- **Frontend Tests**: 23/23 통과 (100%)
- **Backend Tests**: 65/68 통과 (95.3% + 3개 정상 스킵)
- **빌드 및 배포**: 모든 단계 성공
- **크로스 플랫폼 호환성**: Windows CRLF → Unix LF 완전 해결

## 개발 규칙

### 코드 변경 체크리스트
- 새 전략 추가: `backend/app/services/strategy_service.py`에 Strategy 클래스와 `_strategies` 엔트리 추가
- 외부 라이브러리: `backend/requirements.txt`에 추가
- 새 API: `backend/app/api/v1/endpoints/`에 추가, Response/Request 모델은 `backend/app/models/`에 확장
- 현금 자산: asset_type='cash'인 경우 symbol은 임의값 가능, 데이터 수집 없이 일정한 가치 유지
- 네이버 뉴스: 새 종목 추가 시 `ticker_mapping` 딕셔너리 업데이트
- 시스템 정보: 환경 변수나 버전 정보는 `system.py`와 `ServerStatus.tsx`에 반영

### 프론트엔드 개발 우선순위
1. 폼 상태 관리 개선
2. 에러 바운더리 구현
3. 성능 최적화
4. 테스트 코드 작성

### 커밋 메시지 규칙
- **형식**: `type: 간결한 제목` (이모지 사용 금지)
- **본문**: 필요시 상세 설명 추가 (불필요한 수식어 제거)
- **예시**: `fix: TypeScript 빌드 오류 해결`, `feat: 현금 자산 처리 기능 추가`

### 문서화 규칙
- 코드 수정 시 관련 마크다운 문서 최신화 필수
- 백엔드 문서: `backend/doc/`, 프론트엔드 문서: `frontend/doc/`
- 디렉터리 계층 구조에 맞는 문서 배치

## 주요 위치

### 중요 파일
- 전략 등록: `backend/app/services/strategy_service.py`
- 데이터 수집: `backend/app/utils/data_fetcher.py` (yfinance 사용)
- 뉴스 API: `backend/app/api/v1/endpoints/naver_news.py`
- 설정 관리: `backend/app/core/config.py`

### 문서 위치
- 백엔드 개발 가이드: `backend/doc/README.md`
- 테스트 아키텍처: `backend/doc/TEST_ARCHITECTURE.md`
- 현금 자산 처리: `backend/doc/CASH_ASSETS.md`
- 프론트엔드 개발 가이드: `frontend/doc/README.md`

## 외부 의존성

### API 키 필요
- **네이버 검색 API**: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
- **yfinance**: API 키 불필요

### 데이터베이스
- **MySQL**: 캐시 저장소 (윈도우: host.docker.internal, 운영: 127.0.0.1)

## 제한 사항

### 환경별 고려사항
- **윈도우 도커**: `host.docker.internal` 사용 필수
- **우분투 CI/CD**: MySQL 직접 접근 불가, 완전 오프라인 모킹 사용
- **포트 매핑**: 프론트엔드 5174:5174, 백엔드 8001:8000

### 기술적 제약
- **yfinance**: 시장 휴일/주말 데이터 없음, 일일 API 제한 존재
- **TypeScript strict 모드**: 사용하지 않는 변수 선언 시 빌드 실패
- **Pydantic V2**: @field_validator, json_schema_extra, lifespan 패턴 등 최신 문법 사용

## To-Do 우선순위

### 1. High (비즈니스 핵심 기능)
- [x] 진짜 현금 자산 처리: asset_type 필드로 현금과 주식 구분, 무위험 자산으로 0% 수익률 보장
- [ ] 백테스트 결과 개선: 월별/연도별 수익률 분석, 베타 계수, 최대 연속 손실 기간 등 추가 통계 제공
- [ ] 회원 가입 기능: 사용자 관리 시스템 구축
- [ ] 내 포트폴리오 저장 기능: 사용자별 포트폴리오 관리

### 2. Medium (사용자 경험 개선)
- [ ] 폼 상태 관리 개선: `UnifiedBacktestForm.tsx`의 복잡한 상태를 useReducer로 리팩토링
- [ ] TypeScript 타입 안정성: 이벤트 핸들러 타입 명시로 any 타입 제거
- [ ] 테스트 커버리지 향상: 단위/통합/E2E 테스트 강화

### 3. Low (고급 기능 및 확장)
- [ ] OpenAI API 포트폴리오 적합성 분석: AI 기반 투자 성향 분석
- [ ] 커뮤니티 기능: 수익률 공유 및 랭킹 시스템
- [ ] 주식 티커 자동 완성: 자연어 → 티커 자동 변환

## 참고 명령어

### 개발 효율성
- **실시간 개발**: Docker 볼륨 마운트(`./backend:/app`)로 로컬 파일 수정 시 컨테이너에 즉시 반영
- **테스트**: `docker-compose exec backend pytest tests/ -v` (docker cp 불필요)
- **재빌드**: 새 패키지 의존성 추가 시에만 `--build` 플래그 필요

### CI/CD
- **젠킨스**: main 브랜치 푸시 시 자동 실행
- **테스트 분리**: 프론트엔드 `npm test`, 백엔드 `pytest` 각각 별도 스테이지
- **배포**: scp 파일 복사 + 직접 실행 방식으로 안정성 확보

로그만 입력하면 로그를 바탕으로 문제점이나 개선점을 찾아 분석하고 해결방안을 제시합니다.
