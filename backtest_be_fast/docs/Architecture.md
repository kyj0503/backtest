# 백엔드 아키텍처

## 디렉터리 구조

```
app/
├── main.py              # FastAPI 앱 진입점
├── api/                 # API 라우터 및 엔드포인트
│   └── v1/
│       ├── api.py       # 라우터 통합
│       ├── decorators.py # 에러 핸들링
│       └── endpoints/   # HTTP 엔드포인트
├── services/            # 비즈니스 로직
├── repositories/        # 데이터 액세스
├── strategies/          # 백테스팅 전략
├── schemas/             # 요청/응답 스키마
├── factories/           # 객체 생성 팩토리
├── events/              # 이벤트 핸들러
├── core/                # 설정 및 예외 처리
└── utils/               # 유틸리티 함수
```

## 핵심 파일

### API 계층
- `app/main.py`: FastAPI 애플리케이션 생성, CORS 설정
- `app/api/v1/api.py`: 라우터 등록
- `app/api/v1/endpoints/backtest.py`: 백테스트 API 엔드포인트

### 서비스 계층
- `app/services/portfolio_service.py`: 포트폴리오 백테스트
- `app/services/backtest_service.py`: 개별 백테스트 로직
- `app/services/unified_data_service.py`: 데이터 통합 수집
- `app/services/news_service.py`: 뉴스 데이터 처리

### 데이터 계층
- `app/repositories/data_repository.py`: 주가/환율 데이터 저장
- `app/repositories/news_repository.py`: 뉴스 데이터 저장
- `app/utils/data_fetcher.py`: yfinance 데이터 수집

### 전략 계층
- `app/strategies/`: 백테스팅 전략 클래스들
- `app/factories/`: 전략 인스턴스 생성

### 설정
- `app/core/config.py`: 환경 변수 관리 (Settings 클래스)
- `app/core/exceptions.py`: 커스텀 예외
- `app/schemas/schemas.py`: Pydantic 모델

## 아키텍처 패턴

**Controller-Service-Repository**
- Controller (api/): HTTP 요청/응답만 처리
- Service (services/): 비즈니스 로직
- Repository (repositories/): 데이터 저장/조회

**Factory 패턴**
- factories/: 전략 객체 생성 담당
