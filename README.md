# 백테스팅 프로젝트

FastAPI 백엔드와 React 프론트엔드를 활용한 주식 투자 전략 백테스팅 시스템입니다.

## 빠른 시작

### 개발 환경 실행
```bash
# 개발 환경 시작 (실시간 코드 반영)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 백그라운드 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 서비스 중지
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### 접속 정보
- **프론트엔드**: http://localhost:5174
- **백엔드 API**: http://localhost:8001
- **API 문서**: http://localhost:8001/docs

### 테스트 실행
```bash
# 백엔드 테스트
docker-compose exec backend pytest tests/ -v

# 프론트엔드 테스트
docker-compose exec frontend npm test
```

## 주요 기능

### 지원하는 투자 전략
| 전략 | 설명 | 파라미터 |
|------|------|----------|
| Buy & Hold | 매수 후 보유 | 없음 |
| SMA Crossover | 단순이동평균 교차 | 단기/장기 기간 |
| RSI Strategy | RSI 기반 매매 | RSI 기간, 과매수/과매도 기준 |
| Bollinger Bands | 볼린저 밴드 기반 매매 | 기간, 표준편차 배수 |
| MACD Strategy | MACD 교차 기반 매매 | 빠른/느린/시그널 기간 |

### 백테스트 결과
- **성과 지표**: 총 수익률, 연간 수익률, 샤프 비율, 최대 손실폭 등
- **시각화**: 자산 성장 차트, OHLC 차트, 거래 내역 차트
- **비교 분석**: 전략별 성과 비교 및 벤치마크 대비 분석

## 기술 스택

### 백엔드
- **FastAPI**: 고성능 API 서버
- **uvicorn**: ASGI 서버
- **yfinance**: 주식 데이터 수집
- **backtesting**: 백테스트 엔진
- **MySQL**: 데이터 캐시

### 프론트엔드
- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안전성
- **Vite**: 빌드 도구
- **React Bootstrap**: UI 컴포넌트
- **Recharts**: 차트 라이브러리

### 인프라
- **Docker**: 컨테이너화
- **nginx**: 프로덕션 프록시
- **Jenkins**: CI/CD 파이프라인

## 프로젝트 구조

```
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/         # API 엔드포인트
│   │   ├── services/    # 비즈니스 로직
│   │   ├── models/      # 데이터 모델
│   │   └── utils/       # 유틸리티
│   ├── tests/           # 테스트 코드
│   └── doc/             # 백엔드 문서
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── components/  # React 컴포넌트
│   │   ├── types/       # TypeScript 타입
│   │   └── utils/       # 유틸리티
│   └── doc/             # 프론트엔드 문서
└── doc/                 # 전체 프로젝트 문서
```

## 개발 환경

### 필수 요구사항
- Docker Desktop
- Git

### 환경 변수 설정
```bash
# backend/.env
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_DATABASE=stock_data_cache
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
```

## 문서

- [백엔드 API 가이드](backend/doc/api.md)
- [프론트엔드 개발 가이드](frontend/doc/README.md)
- [테스트 아키텍처](backend/doc/TEST_ARCHITECTURE.md)

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.