# 프론트엔드 개발 가이드

## 개요

React 18 + TypeScript 기반의 백테스팅 웹 애플리케이션입니다. 사용자가 포트폴리오 백테스트를 실행하고 결과를 시각화할 수 있는 인터페이스를 제공합니다.

## 기술 스택

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Framework**: React Bootstrap + Bootstrap 5
- **Charting**: Recharts
- **Container**: Docker

## 프로젝트 구조

```
frontend/
├── src/
│   ├── App.tsx              # 메인 애플리케이션
│   ├── main.tsx            # React 진입점
│   ├── components/         # React 컴포넌트
│   │   ├── UnifiedBacktestForm.tsx    # 통합 백테스트 폼
│   │   ├── UnifiedBacktestResults.tsx # 통합 결과 표시
│   │   ├── OHLCChart.tsx              # OHLC 차트
│   │   ├── EquityChart.tsx            # 자산 곡선 차트
│   │   ├── TradesChart.tsx            # 거래 차트
│   │   ├── StatsSummary.tsx           # 성과 요약
│   │   └── PortfolioResults.tsx       # 포트폴리오 결과
│   └── types/
│       └── api.ts          # TypeScript 타입 정의
├── doc/                    # 프론트엔드 문서
├── package.json           # 의존성 관리
├── vite.config.ts        # Vite 설정
└── Dockerfile           # Docker 설정
```

## 주요 기능

### 1. 통합 백테스트 폼 (UnifiedBacktestForm)
- **투자 금액 기반 포트폴리오**: 각 종목에 투자할 금액 직접 입력
- **자동 비중 계산**: 입력한 금액을 바탕으로 포트폴리오 비중 자동 계산
- **투자 전략**: Buy & Hold, SMA Crossover, RSI, Bollinger Bands, MACD 전략 지원
- **동적 파라미터**: 선택한 전략에 따른 파라미터 입력 폼 동적 생성

### 2. 결과 시각화 (UnifiedBacktestResults)
- **포트폴리오 성과 요약**: 총 수익률, 개별 종목 성과 등
- **차트 시각화**: OHLC, 자산 곡선, 거래 내역 차트
- **성과 지표**: 샤프 비율, 최대 손실, 승률 등 주요 지표

### 3. 개별 차트 컴포넌트
- **OHLCChart**: 가격 데이터 및 기술 지표
- **EquityChart**: 포트폴리오 가치 변화 곡선
- **TradesChart**: 개별 거래 분석
- **StatsSummary**: 핵심 성과 지표 카드

## 개발 환경 설정

### Docker 사용 (권장)

```bash
# 프로젝트 루트에서
docker compose -f docker-compose.yml -f docker-compose.dev.yml up frontend --build
```

### 로컬 개발

```bash
cd frontend
npm install
npm run dev
```

## 지원하는 투자 전략

| 전략 | 설명 | 파라미터 |
|------|------|----------|
| Buy & Hold | 매수 후 보유 | 없음 |
| SMA Crossover | 단순이동평균 교차 | 단기/장기 기간 |
| RSI Strategy | RSI 기반 매매 | RSI 기간, 과매수/과매도 기준 |
| Bollinger Bands | 볼린저 밴드 기반 매매 | 기간, 표준편차 배수 |
| MACD Strategy | MACD 교차 기반 매매 | 빠른/느린/시그널 기간 |

## API 연동

자세한 API 연동 방법은 [API_GUIDE.md](API_GUIDE.md)를 참조하세요.

### 주요 엔드포인트
- `POST /api/v1/backtest/portfolio` - 포트폴리오 백테스트
- `POST /api/v1/backtest/chart-data` - 단일 종목 차트 데이터

## 컴포넌트 가이드

자세한 컴포넌트 사용법은 [COMPONENTS.md](COMPONENTS.md)를 참조하세요.

## 스타일링

자세한 스타일링 가이드는 [STYLING.md](STYLING.md)를 참조하세요.

## 상태 관리

자세한 상태 관리 방법은 [STATE_MANAGEMENT.md](STATE_MANAGEMENT.md)를 참조하세요.