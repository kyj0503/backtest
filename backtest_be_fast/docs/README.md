# 01. FastAPI 백엔드 문서 개요 (backtest_be_fast)

이 디렉터리는 백테스팅 서비스 FastAPI 백엔드 관련 문서를 모아둔 장소입니다. 실제 코드와 설정에 맞춰 작성되어 있으며, 빠르게 개발 환경을 세팅하고 API를 이해하는 데 목적이 있습니다.

## 기술 스택
- Python 3.11+, FastAPI, Pydantic v2
- 비동기 처리, CQRS/이벤트 패턴
- MySQL (사용자/커뮤니티), yfinance 캐시

## 실행 방법
- 로컬 단독: `python run_server.py` (포트 8000)
- 전체 스택: `docker compose -f compose.yaml -f compose/compose.dev.yml up --build`
- 헬스체크: `GET /health`

## 디렉터리 개요 (`app/`)
- `api/`: FastAPI 라우터 및 엔드포인트
- `services/`: 비즈니스 로직 및 서비스 레이어
- `cqrs/`: 명령/쿼리 분리 패턴 구현
- `domains/`: 도메인 엔티티 및 값 객체
- `repositories/`: 데이터 액세스 레이어
- `events/`: 이벤트 시스템 및 핸들러
- `models/`: Pydantic 요청/응답 모델

## 환경변수
- `HOST`, `PORT`: 서버 바인딩 설정 (기본값 0.0.0.0:8000)
- `DEBUG`: 개발 모드 활성화 (핫 리로드)
- `BACKEND_CORS_ORIGINS`: CORS 허용 오리진 (콤마 구분)

## 문서 색인
- 02. 개발 가이드: `./DEVELOPMENT_GUIDE.md`
- 03. API 가이드: `./API_GUIDE.md`
- 04. 아키텍처 가이드: `./ARCHITECTURE_GUIDE.md`
