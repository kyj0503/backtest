# 시스템 아키텍처 및 기술 스택

백테스팅 시스템의 전체 아키텍처와 사용된 기술 스택에 대한 상세 정보입니다.

## 시스템 아키텍처

### 전체 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   React + TS    │────│   FastAPI       │────│   MySQL Cache   │
│   Port: 5174    │    │   Port: 8001    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vite Build    │    │  backtesting.py │    │   yfinance API  │
│   React Router  │    │   Strategy Engine│    │   External Data │
│   Bootstrap UI  │    │   Pydantic V2   │    │   News APIs     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 데이터 흐름
```
1. 사용자 입력 (프론트엔드)
   ↓
2. API 요청 검증 (Pydantic)
   ↓
3. 데이터 수집 (yfinance + MySQL 캐시)
   ↓
4. 전략 실행 (backtesting.py)
   ↓
5. 결과 처리 및 반환 (FastAPI)
   ↓
6. 차트 렌더링 (Recharts)
```

### 데이터 캐싱 전략
- **1차 캐시**: MySQL에 일별 주식 데이터 저장
- **TTL**: 1일 후 캐시 만료
- **캐시 미스**: yfinance API 호출 후 캐시 업데이트
- **오프라인 모드**: CI/CD 환경에서 완전 모킹

## 기술 스택

### 프론트엔드
- **React 18**: 최신 Hook 기반 컴포넌트
- **TypeScript**: 엄격한 타입 안정성
- **Vite**: 빠른 개발 서버 및 빌드
- **React Bootstrap**: 반응형 UI 컴포넌트
- **Recharts**: 데이터 시각화

### 백엔드
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Pydantic V2**: 데이터 검증 및 직렬화
- **MySQL**: 데이터 캐시 저장소
- **yfinance**: 실시간 주식 데이터
- **backtesting.py**: 백테스트 엔진

### 인프라
- **Docker**: 컨테이너화된 개발/배포 환경
- **Jenkins**: CI/CD 파이프라인
- **nginx**: 프로덕션 웹 서버
- **GitHub**: 소스 코드 관리

## 현금 자산 처리

### 개념 및 구현
현금 자산은 포트폴리오에서 무위험 자산 역할을 하며, 시간에 관계없이 0% 수익률을 보장합니다.

```typescript
// 프론트엔드: 현금 자산 타입
interface PortfolioStock {
  symbol: string;
  amount: number;
  asset_type: 'stock' | 'cash';  // 현금 자산 구분
  investment_type?: 'lump_sum' | 'dca';
}
```

```python
# 백엔드: 현금 자산 처리
def process_cash_assets(portfolio: List[PortfolioStock]) -> pd.DataFrame:
    """현금 자산을 무위험 자산으로 처리"""
    for asset in portfolio:
        if asset.asset_type == 'cash':
            # 0% 수익률, 변동성 없는 안전 자산으로 처리
            cash_data = create_constant_value_series(asset.amount)
```

### 리스크 관리 효과
- **변동성 감소**: 포트폴리오 전체 리스크 완화
- **안전 마진**: 시장 하락 시 손실 제한
- **리밸런싱**: 정기적 포트폴리오 조정 시 유동성 제공

## API 설계

### RESTful API 구조
```
/api/v1/
├── backtest/
│   ├── /chart-data          # 단일 종목 백테스트
│   └── /portfolio           # 포트폴리오 백테스트
├── naver-news/
│   ├── /{ticker}            # 종목별 뉴스
│   └── /supported-tickers   # 지원 종목 목록
├── strategies/
│   ├── /list                # 전략 목록
│   └── /{strategy}/params   # 전략별 매개변수
└── system/
    ├── /health              # 서버 상태
    └── /version             # 버전 정보
```

### 통합 백테스트 API
```python
@router.post("/backtest", response_model=UnifiedBacktestResponse)
async def run_unified_backtest(request: UnifiedBacktestRequest):
    """단일 종목 및 포트폴리오 백테스트 통합 처리"""
    # 입력 검증
    validate_request(request)
    
    # 데이터 수집
    data = await fetch_portfolio_data(request.portfolio)
    
    # 현금 자산 처리
    if has_cash_assets(request.portfolio):
        data = process_cash_assets(data, request.portfolio)
    
    # 백테스트 실행
    result = await run_backtest_engine(data, request)
    
    return format_unified_response(result)
```

## 핵심 기능

### 백테스트 엔진
- **backtesting.py**: Python 기반 백테스트 라이브러리
- **전략 실행**: 다양한 투자 전략 지원
- **성과 분석**: 수익률, 리스크 지표 계산

### 현금 자산 지원
- **무위험 자산**: 포트폴리오 리스크 관리
- **asset_type 구분**: 'stock' vs 'cash'
- **0% 수익률**: 시간에 관계없이 일정한 가치 유지

### 실시간 데이터
- **yfinance API**: 주식 데이터 수집
- **MySQL 캐싱**: 데이터 재사용으로 성능 향상
- **오프라인 모킹**: CI/CD 환경 안정성

### 뉴스 분석
- **네이버 뉴스 API**: 70+ 종목 뉴스 제공
- **날짜별 필터링**: 특정 기간 뉴스 검색
- **자동 콘텐츠 정제**: 불필요한 콘텐츠 제거

### CI/CD 파이프라인
- **Jenkins**: 자동 빌드/배포
- **Docker**: 컨테이너화된 환경
- **테스트 자동화**: 프론트엔드/백엔드 테스트
