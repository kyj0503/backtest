# 백엔드 클린코드 리팩터링 계획

**작성일**: 2025-11-16
**대상**: backtest_be_fast 백엔드 서비스
**목표**: 클린코드 원칙에 따른 구조 개선 및 유지보수성 향상

## ✅ 실행 현황

**Phase 1.1: portfolio_service.py 분할 - 완료** (2025-11-16)

### 완료된 작업
- ✅ PortfolioDcaManager 클래스 추출 (DCA 투자 관리)
  - execute_initial_purchases(): 첫 날 초기 매수
  - execute_periodic_purchases(): Nth Weekday 기반 주기적 매수
  - Commits: 3c42d84

- ✅ PortfolioRebalancer 클래스 추출 (포트폴리오 리밸런싱)
  - calculate_adjusted_weights(): 상장폐지 종목을 고려한 목표 비중 동적 조정
  - execute_rebalancing_trades(): 리밸런싱 거래 실행
  - Commits: 9a092ec

- ✅ PortfolioSimulator 클래스 추출 (시뮬레이션 루프 실행)
  - initialize_portfolio_state(): 포트폴리오 상태 초기화
  - detect_and_update_delisting(): 상장폐지 종목 감지
  - fetch_and_convert_prices(): 가격 데이터 추출 및 USD 변환
  - calculate_daily_metrics_and_history(): 일일 메트릭 계산
  - Commits: 4e469f0

- ✅ PortfolioMetrics 클래스 추출 (지표 계산)
  - calculate_daily_metrics_and_history(): 정규화된 포트폴리오 가치 및 수익률
  - calculate_portfolio_statistics(): Sharpe ratio, max drawdown, volatility 등 통계
  - Commits: 6297fc1

- ✅ PortfolioService 리팩터링 (위임 패턴)
  - 컴포넌트 인스턴스 주입 (DcaManager, Rebalancer, Simulator, Metrics)
  - 모든 정적 메서드 호출을 인스턴스 메서드로 변환
  - calculate_dca_portfolio_returns 정적 메서드 제거
  - Commits: f64d085, 4f61258

### 통계 (Phase 1.1)
- 추출된 클래스: 4개
- 총 추출 라인 수: ~950줄
- 생성된 파일: 4개 (portfolio_dca_manager.py, portfolio_rebalancer.py, portfolio_simulator.py, portfolio_metrics.py)
- 리팩터링 코드 라인: 30줄 (PortfolioService)

---

## ✅ Phase 1.2 실행 현황

**Phase 1.2: yfinance_db.py 분할 - 완료** (2025-11-16)

### 완료된 작업

- ✅ DatabaseConfig 클래스 생성 (155줄)
  - 환경 변수 및 settings에서 DB 설정 로드
  - DATABASE_URL 파싱 및 개별 설정 혼합 지원
  - 마스킹된 URL 생성 (로깅용)
  - Commits: c728f37

- ✅ PoolConfig 클래스 생성 (130줄)
  - SQLAlchemy 연결 풀 설정 관리
  - 기본값 최적화 (pool_size=40, max_overflow=80)
  - 설정값 유효성 검증
  - SQLAlchemy create_engine() kwargs 제공
  - Commits: c728f37

- ✅ DatabaseConnectionManager 클래스 생성 (140줄)
  - 싱글톤 패턴으로 Engine 캐싱
  - DatabaseConfig와 PoolConfig 통합 관리
  - 테스트용 reset_cache() 제공
  - Commits: c728f37

- ✅ yfinance_db.py _get_engine() 간소화
  - 94줄 → 9줄 (90% 감소)
  - DatabaseConnectionManager로 위임
  - 복잡한 설정 로직 제거
  - Commits: 63f3db5

### 통계 (Phase 1.2)
- 생성된 클래스: 3개
- 생성된 파일: 4개 (database_config.py, pool_config.py, connection_manager.py, __init__.py)
- 총 추가 라인: ~402줄
- 제거된 라인: 85줄 (yfinance_db.py)
- 순 변경: +317줄 (더 나은 구조)

---

## ✅ Phase 1.3 실행 현황

**Phase 1.3: Repository Pattern 강화 - 완료** (2025-11-16)

### 완료된 작업

- ✅ StockRepository 클래스 생성 (280줄)
  - yfinance_db 모듈 전체 추상화 계층 제공
  - load_stock_data(): DB 우선 주가 데이터 조회
  - save_stock_data(): DataFrame을 DB에 저장
  - get_ticker_info(): 티커 메타데이터 조회
  - get_tickers_info_batch(): 여러 티커 배치 조회 (N+1 최적화)
  - load_ticker_news(), save_ticker_news(): 뉴스 데이터 조회/저장
  - Commits: 41a2abe

- ✅ portfolio_service.py 마이그레이션
  - `get_ticker_info_batch_from_db` → `stock_repository.get_tickers_info_batch()`
  - `load_ticker_data` (2회) → `stock_repository.load_stock_data()`
  - Repository 인스턴스 주입으로 DI 패턴 적용
  - Commits: 41a2abe

- ✅ data_service.py 마이그레이션
  - `load_ticker_data` → `stock_repository.load_stock_data()`
  - Repository 인스턴스 초기화
  - Commits: b5cacec

- ✅ currency_converter.py 마이그레이션
  - `load_ticker_data` (3회) → `stock_repository.load_stock_data()`
  - `get_ticker_info_from_db` → `stock_repository.get_ticker_info()`
  - __init__ 메서드 추가하여 Repository 초기화
  - Commits: e3c6451

- ✅ data_repository.py 마이그레이션
  - `load_ticker_data` → `stock_repository.load_stock_data()`
  - `save_ticker_data` → `stock_repository.save_stock_data()`
  - Repository 인스턴스 초기화
  - Commits: de6c389

- ✅ 미사용 import 제거
  - backtest_engine.py: 미사용 yfinance_db imports 제거 (실제로는 data_repository 사용)
  - portfolio_simulator.py: 미사용 `get_ticker_info_batch_from_db` import 제거
  - Commits: 6b986eb, f2341dc

### 통계 (Phase 1.3)
- 생성된 클래스: 1개 (StockRepository)
- 생성된 파일: 1개 (stock_repository.py)
- 마이그레이션된 파일: 5개 (portfolio_service, data_service, currency_converter, data_repository, backtest_engine)
- 제거된 직접 import: 100% (모든 yfinance_db 직접 import 제거)
- 총 추가 라인: ~280줄 (stock_repository.py)
- 수정된 라인: ~20줄 (5개 서비스)
- 순 변경: +260줄 (더 나은 구조)

---

## 📊 Phase 1 완료 요약

### Phase 1 전체 완료 상태: ✅ 100% 완료

**3개 Phase 모두 완료됨**:
1. ✅ Phase 1.1 - portfolio_service.py 분할 (4개 클래스 추출)
2. ✅ Phase 1.2 - yfinance_db.py 데이터베이스 연결 관리 분할 (3개 클래스 추출)
3. ✅ Phase 1.3 - Repository Pattern 강화 (1개 Repository 생성, 5개 서비스 마이그레이션)

### Phase 1 통계 종합

- **생성된 클래스**: 8개 (4+3+1)
- **생성된 파일**: 9개 (4+4+1)
- **마이그레이션된 파일**: 5개
- **총 코드 라인**: ~1,050줄 추가
- **직접 yfinance_db import**: 0개 (100% 제거)
- **정적 메서드**: 대부분 제거 (인스턴스 메서드로 전환)

### 아키텍처 개선 효과

✅ **분리 원칙 (Separation of Concerns)**
- portfolio_service: 1,820줄 → ~1,100줄 (40% 감소)
- 각 컴포넌트: 200-300줄 (균형 잡힌 구조)

✅ **Repository Pattern 적용**
- yfinance_db 직접 호출: 0회 (5개 서비스에서)
- StockRepository를 통한 일관된 접근

✅ **테스트 용이성**
- 컴포넌트별 독립적 테스트 가능
- Mock Repository로 쉬운 단위 테스트

✅ **유지보수성**
- 데이터 소스 변경 시 StockRepository만 수정
- 각 클래스의 책임 명확
- 순환 의존성 제거

---

## 📊 코드베이스 현황 분석

### 전체 통계

- **서비스 파일 수**: 14개
- **총 코드 라인 수**: 6,149줄
- **최대 파일 크기**: 1,820줄 (portfolio_service.py)
- **평균 함수 길이**: ~80줄
- **async/sync 경계**: 7개 파일에서 asyncio.to_thread() 사용

### 주요 문제점 (및 해결 상태)

#### 1. God Object 안티패턴 ✅ 해결됨

**문제**: `portfolio_service.py` (1,820줄)
- 단일 파일에 너무 많은 책임 집중
- 12개의 static methods (별도 클래스로 분리 신호)
- 데이터 로딩, DCA, 리밸런싱, 시뮬레이션, 통계 계산 모두 포함

**해결 방법** (Phase 1.1):
- ✅ PortfolioDcaManager로 DCA 로직 추출 (400줄)
- ✅ PortfolioRebalancer로 리밸런싱 로직 추출 (450줄)
- ✅ PortfolioSimulator로 시뮬레이션 로직 추출 (500줄)
- ✅ PortfolioMetrics로 통계 계산 로직 추출 (270줄)
- ✅ PortfolioService: 1,820줄 → ~1,100줄 (40% 감소)

**결과**:
- ✅ 각 컴포넌트 200-400줄 (관리 가능한 크기)
- ✅ 단일 책임 원칙 준수
- ✅ 테스트 작성 용이

#### 2. Repository Pattern 우회 ✅ 해결됨

**문제**: 5개 서비스가 `yfinance_db` 직접 import
```python
# 안티패턴 (이전)
from app.services.yfinance_db import load_ticker_data
data = await asyncio.to_thread(load_ticker_data, ...)
```

**위반 서비스** (이전):
- `portfolio_service.py` (5회 호출)
- `backtest_engine.py` (2회 호출)
- `data_service.py`
- `currency_converter.py` (3회 호출)
- `data_repository.py` (2회 호출)

**해결 방법** (Phase 1.3):
- ✅ StockRepository 생성 (280줄)
- ✅ portfolio_service.py 마이그레이션
- ✅ data_service.py 마이그레이션
- ✅ currency_converter.py 마이그레이션
- ✅ data_repository.py 마이그레이션
- ✅ backtest_engine.py 미사용 import 제거

**결과**:
```python
# 개선된 패턴 (현재)
from app.repositories.stock_repository import get_stock_repository
stock_repo = get_stock_repository()
data = await asyncio.to_thread(stock_repo.load_stock_data, ...)
```
- ✅ yfinance_db 직접 import: 0개 (100% 제거)
- ✅ 일관된 Repository 패턴 적용
- ✅ Mock repository로 테스트 용이

#### 3. 과도한 Static Methods ✅ 해결됨

**문제**:
- `portfolio_service.py`: 12개 static methods
- Static method는 별도 클래스/모듈로 분리 신호
- OOP 설계 원칙 위반 (SRP, OCP)

**해결 방법** (Phase 1.1):
- ✅ 대부분의 static methods를 인스턴스 메서드로 변환
- ✅ 각 메서드를 적절한 컴포넌트 클래스에 배치
- ✅ Dependency Injection 패턴 적용

**결과**:
- ✅ Static methods 최소화 (필요한 것만 남김)
- ✅ 컴포넌트 간 느슨한 결합
- ✅ 테스트 시 의존성 주입 가능

#### 4. 긴 함수와 높은 복잡도 ✅ 부분 해결됨

**문제 함수들** (이전):
1. `_execute_rebalancing_trades()`: 175줄
2. `run_buy_and_hold_portfolio_backtest()`: 300+ 줄
3. `_get_engine()` in yfinance_db: 150+ 줄

**해결 방법**:
- ✅ Phase 1.1: PortfolioRebalancer, PortfolioSimulator로 로직 분리
- ✅ Phase 1.2: DatabaseConnectionManager, PoolConfig, DatabaseConfig로 _get_engine() 대체 (150줄 → 9줄)
- ⏳ Phase 2: 추가 리팩터링 (함수 분할, 복잡도 감소)

**결과**:
- ✅ 각 컴포넌트 150-400줄 (순환 복잡도 감소)
- ✅ Helper 함수로 작은 단위로 분할

#### 5. 서비스 간 강한 결합 ✅ 개선됨

**의존성 개선**:
```
개선 전:
portfolio_service.py (1820 lines)
├─> yfinance_db (직접 호출) ❌
├─> dca_calculator
├─> rebalance_helper
└─> currency_converter
    └─> yfinance_db (직접 호출) ❌

개선 후:
portfolio_service.py (~1100 lines)
├─> StockRepository (단일 진입점) ✅
├─> PortfolioDcaManager
├─> PortfolioRebalancer
└─> currency_converter
    └─> StockRepository ✅
```

**해결 방법** (Phase 1.3):
- ✅ 모든 서비스가 StockRepository를 통해 데이터 접근
- ✅ yfinance_db 직접 호출 제거
- ✅ Circular dependency 제거
- ⏳ Global singleton 최소화 (Phase 2에서 추가 개선)

#### 6. 명명 규칙 불일치 ⏳ Phase 2에서 처리

**Data Fetching 메서드**:
- `get_*`: 캐시된 데이터 조회
- `load_*`: DB에서 로드
- `fetch_*`: 외부 API 호출
- → 일관성 통일 필요 (Phase 2.2)

**클래스 명명**:
- `NaverNewsService` (일관성 있음)
- `DCACalculator` (통일 필요)
- `RebalanceHelper` vs `PortfolioCalculatorService` (suffix 통일 필요)

#### 7. 분산된 Validation 로직 ⏳ Phase 2에서 처리

**현재 상태**:
- **Pydantic schemas**: 타입 검증 + 일부 비즈니스 규칙
- **validation_service**: 백테스트 요청 검증
- **개별 서비스**: 각자 검증 로직 포함

**계획** (Phase 2.3):
- ✅ 중앙화된 validation layer 생성
- ✅ 중복된 검증 로직 통합

---

## 🎯 리팩터링 원칙

### 1. 금융 로직 보존 우선
- **기능 변경 없음**: 백테스트 결과 동일 보장
- **구조만 개선**: 내부 구조 리팩터링
- **역호환성**: 기존 API 엔드포인트 동작 보장

### 2. 점진적 리팩터링
- 한 번에 하나씩 단계별 진행
- 각 단계마다 테스트 실행
- 작은 커밋 단위로 진행

### 3. 테스트 우선
- 리팩터링 전: 현재 동작 테스트로 고정
- 리팩터링 중: 각 변경마다 테스트
- 리팩터링 후: 통합 테스트로 검증

### 4. 문서화
- 각 Phase마다 변경 사항 문서화
- 마이그레이션 가이드 작성
- CLAUDE.md 업데이트

---

## 📅 Phase 1: 긴급 구조 개선 (1-2주)

### 우선순위: ⭐⭐⭐ 최고

이 Phase는 가장 큰 문제를 해결하고 코드베이스의 기반을 개선합니다.

---

### 1.1 portfolio_service.py 분할 ⭐⭐⭐

#### 현재 문제
```
portfolio_service.py (1,820 lines)
├── PortfolioService class (79 lines)
├── 12 static methods (1,741 lines)
│   ├── DCA 로직 (400+ lines)
│   ├── 리밸런싱 로직 (450+ lines)
│   ├── 시뮬레이션 로직 (500+ lines)
│   └── 통계 계산 (270+ lines)
```

#### 목표 구조
```
app/services/portfolio/
├── __init__.py                    (20줄)  - 패키지 진입점
├── portfolio_service.py           (200줄) - 오케스트레이터
├── portfolio_dca_manager.py       (400줄) - DCA 로직
├── portfolio_rebalancer.py        (450줄) - 리밸런싱 로직
├── portfolio_simulator.py         (500줄) - 시뮬레이션 루프
└── portfolio_metrics.py           (270줄) - 통계 계산
```

#### 추출할 클래스

**1. PortfolioDcaManager** (400줄)
```python
class PortfolioDcaManager:
    """DCA(Dollar Cost Averaging) 투자 관리"""

    def execute_initial_purchases(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, Dict],
        shares: Dict[str, float],
        commission: float
    ) -> Tuple[int, float]:
        """첫 날 초기 매수 실행"""
        pass

    def execute_periodic_purchases(
        self,
        current_date: pd.Timestamp,
        prev_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, Dict],
        shares: Dict[str, float],
        commission: float,
        start_date_obj: datetime
    ) -> Tuple[int, float]:
        """주기적 DCA 투자 실행"""
        pass
```

**2. PortfolioRebalancer** (450줄)
```python
class PortfolioRebalancer:
    """포트폴리오 리밸런싱 로직"""

    def execute_rebalancing_trades(
        self,
        current_date: pd.Timestamp,
        adjusted_target_weights: Dict[str, float],
        shares: Dict[str, float],
        current_prices: Dict[str, float],
        available_cash: float,
        cash_holdings: Dict[str, float],
        commission: float,
        total_stock_value: float,
        dca_info: Dict[str, Dict],
        delisted_stocks: set
    ) -> Dict[str, Any]:
        """리밸런싱 거래 실행 및 히스토리 기록"""
        pass

    def calculate_adjusted_weights(
        self,
        target_weights: Dict[str, float],
        delisted_stocks: set,
        dca_info: Dict[str, Dict]
    ) -> Dict[str, float]:
        """상장폐지 종목 반영한 목표 비중 조정"""
        pass
```

**3. PortfolioSimulator** (500줄)
```python
class PortfolioSimulator:
    """포트폴리오 시뮬레이션 실행"""

    def __init__(
        self,
        dca_manager: PortfolioDcaManager,
        rebalancer: PortfolioRebalancer
    ):
        self.dca_manager = dca_manager
        self.rebalancer = rebalancer

    def initialize_state(
        self,
        stock_amounts: Dict[str, float],
        cash_amount: float,
        amounts: Dict[str, float],
        dca_info: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """포트폴리오 초기 상태 설정"""
        pass

    def detect_and_update_delisting(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, Dict],
        delisted_stocks: set,
        last_valid_prices: Dict[str, float],
        last_price_date: Dict[str, date]
    ) -> None:
        """상장폐지 종목 감지 및 상태 업데이트"""
        pass

    async def run_simulation(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        amounts: Dict[str, float],
        dca_info: Dict[str, Dict],
        start_date: str,
        end_date: str,
        rebalance_frequency: str,
        commission: float
    ) -> pd.DataFrame:
        """시뮬레이션 메인 루프"""
        pass
```

**4. PortfolioMetrics** (270줄)
```python
class PortfolioMetrics:
    """포트폴리오 통계 계산"""

    @staticmethod
    def calculate_portfolio_statistics(
        portfolio_returns: pd.DataFrame,
        initial_cash: float,
        commission: float
    ) -> Dict[str, Any]:
        """샤프 비율, 최대 낙폭 등 통계"""
        pass

    @staticmethod
    def calculate_daily_metrics(
        current_date: pd.Timestamp,
        shares: Dict[str, float],
        available_cash: float,
        current_prices: Dict[str, float],
        cash_holdings: Dict[str, float],
        prev_portfolio_value: float,
        daily_cash_inflow: float,
        total_amount: float,
        dca_info: Dict[str, Dict]
    ) -> Tuple[float, float, Dict[str, Any]]:
        """일일 포트폴리오 가치 및 수익률"""
        pass
```

#### 마이그레이션 전략

**Step 1: 클래스 추출 (Breaking Change 없음)**
```python
# 새 파일 생성, 기존 코드 복사
# app/services/portfolio/portfolio_dca_manager.py
class PortfolioDcaManager:
    # static method를 instance method로 변경
    def execute_initial_purchases(...):
        # 기존 _execute_initial_purchases 로직
        pass
```

**Step 2: PortfolioService 리팩터링**
```python
# app/services/portfolio/portfolio_service.py
from .portfolio_dca_manager import PortfolioDcaManager
from .portfolio_rebalancer import PortfolioRebalancer
from .portfolio_simulator import PortfolioSimulator
from .portfolio_metrics import PortfolioMetrics

class PortfolioService:
    def __init__(self):
        self.dca_manager = PortfolioDcaManager()
        self.rebalancer = PortfolioRebalancer()
        self.simulator = PortfolioSimulator(
            dca_manager=self.dca_manager,
            rebalancer=self.rebalancer
        )
        self.metrics = PortfolioMetrics()

    async def run_portfolio_backtest(self, request: PortfolioBacktestRequest):
        """메인 진입점 - 위임만 수행"""
        # 단일 종목 → backtest_service
        if len(request.portfolios) == 1:
            return await backtest_service.run_backtest(...)

        # 다중 종목 → 전략별 분기
        if request.strategy == "buy_hold_strategy":
            return await self.run_buy_and_hold_portfolio_backtest(request)
        else:
            return await self.run_strategy_portfolio_backtest(request)

    async def run_buy_and_hold_portfolio_backtest(self, request):
        """Buy & Hold 전략 - Simulator에 위임"""
        # 데이터 로딩
        portfolio_data = await self._load_portfolio_data(...)

        # 시뮬레이션 실행
        returns_df = await self.simulator.run_simulation(
            portfolio_data=portfolio_data,
            amounts=amounts,
            dca_info=dca_info,
            start_date=request.start_date,
            end_date=request.end_date,
            rebalance_frequency=request.rebalance_frequency,
            commission=request.commission
        )

        # 통계 계산
        statistics = self.metrics.calculate_portfolio_statistics(
            returns_df, request.initial_cash, request.commission
        )

        return PortfolioBacktestResponse(...)
```

**Step 3: Import 경로 업데이트**
```python
# app/services/__init__.py
from app.services.portfolio.portfolio_service import PortfolioService

# 또는 backward compatibility
from app.services.portfolio import PortfolioService as _PortfolioService
portfolio_service = _PortfolioService()
```

**Step 4: 테스트 업데이트**
```python
# tests/unit/test_portfolio_service.py
from app.services.portfolio import PortfolioService
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager

class TestPortfolioDcaManager:
    def test_execute_initial_purchases(self):
        manager = PortfolioDcaManager()
        # 개별 테스트 가능
        ...
```

#### 예상 효과
- ✅ **파일 크기**: 1,820줄 → 4개 모듈 (200-500줄)
- ✅ **SRP 준수**: 각 클래스가 단일 책임
- ✅ **테스트 용이성**: 개별 클래스 단위 테스트
- ✅ **유지보수성**: 변경 영향 범위 명확
- ✅ **가독성**: 2배 향상

---

### 1.2 yfinance_db.py DB 연결 로직 분리

#### 현재 문제
```python
# app/services/yfinance_db.py
def _get_engine() -> Engine:
    """150줄의 복잡한 초기화 로직"""
    global _ENGINE_CACHE
    if _ENGINE_CACHE is not None:
        return _ENGINE_CACHE

    # 환경 변수 파싱 (50줄)
    try:
        from app.core.config import settings
        db_url = settings.database_url or os.getenv("DATABASE_URL")
    except Exception:
        db_url = os.getenv("DATABASE_URL")

    # URL 파싱 및 fallback (50줄)
    if db_url:
        try:
            from sqlalchemy.engine import make_url
            parsed = make_url(db_url)
            db_host = parsed.host
            # ... 20줄 더
        except Exception:
            # fallback 로직 30줄
            pass
    else:
        # 개별 환경 변수에서 빌드 (30줄)
        pass

    # 로깅 (20줄)
    logger.info(...)

    # Engine 생성 (10줄)
    _ENGINE_CACHE = create_engine(...)
    return _ENGINE_CACHE
```

#### 목표 구조
```
app/core/database/
├── __init__.py                 (30줄)
├── connection_manager.py       (100줄) - DB 연결 관리
├── connection_config.py        (50줄)  - 설정 파싱
└── pool_config.py              (30줄)  - Pool 설정
```

#### 추출할 클래스

**1. DatabaseConfig** (connection_config.py)
```python
@dataclass
class DatabaseConfig:
    """데이터베이스 연결 설정"""
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def url(self) -> str:
        """SQLAlchemy connection URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"

    @property
    def masked_url(self) -> str:
        """비밀번호를 마스킹한 URL (로깅용)"""
        return self.url.replace(self.password, "***")

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """환경 변수에서 설정 로드"""
        # DATABASE_URL 우선
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return cls._from_url(db_url)

        # 개별 환경 변수
        return cls(
            host=os.getenv("DATABASE_HOST", "127.0.0.1"),
            port=int(os.getenv("DATABASE_PORT", "3306")),
            user=os.getenv("DATABASE_USER", "root"),
            password=os.getenv("DATABASE_PASSWORD", "password"),
            database=os.getenv("DATABASE_NAME", "stock_data_cache")
        )

    @classmethod
    def _from_url(cls, url: str) -> 'DatabaseConfig':
        """DATABASE_URL 파싱"""
        from sqlalchemy.engine import make_url
        parsed = make_url(url)
        return cls(
            host=parsed.host,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.database
        )
```

**2. PoolConfig** (pool_config.py)
```python
@dataclass
class PoolConfig:
    """Connection Pool 설정"""
    pool_size: int = 40
    max_overflow: int = 80
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    def to_engine_kwargs(self) -> Dict[str, Any]:
        """create_engine() 인자로 변환"""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'future': True
        }
```

**3. DatabaseConnectionManager** (connection_manager.py)
```python
class DatabaseConnectionManager:
    """데이터베이스 연결 및 풀 관리"""

    def __init__(
        self,
        config: DatabaseConfig,
        pool_config: PoolConfig = PoolConfig()
    ):
        self.config = config
        self.pool_config = pool_config
        self._engine: Optional[Engine] = None
        self.logger = logging.getLogger(__name__)

    def get_engine(self) -> Engine:
        """Engine 싱글톤 반환"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def _create_engine(self) -> Engine:
        """Engine 생성"""
        self.logger.info(
            "Creating SQLAlchemy engine -> host=%s port=%s user=%s db=%s",
            self.config.host,
            self.config.port,
            self.config.user,
            self.config.database
        )
        self.logger.debug(f"SQLAlchemy URL (masked): {self.config.masked_url}")

        return create_engine(
            self.config.url,
            **self.pool_config.to_engine_kwargs()
        )

    def close(self):
        """연결 종료"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
```

#### 마이그레이션

**Before**:
```python
# app/services/yfinance_db.py
_ENGINE_CACHE: Optional[Engine] = None

def _get_engine() -> Engine:
    """150줄 복잡한 로직"""
    global _ENGINE_CACHE
    # ... 150 lines ...
    return _ENGINE_CACHE
```

**After**:
```python
# app/services/yfinance_db.py
from app.core.database import DatabaseConnectionManager, DatabaseConfig, PoolConfig

# 모듈 레벨 싱글톤
_connection_manager: Optional[DatabaseConnectionManager] = None

def _get_engine() -> Engine:
    """간결해진 로직"""
    global _connection_manager
    if _connection_manager is None:
        config = DatabaseConfig.from_env()
        _connection_manager = DatabaseConnectionManager(
            config=config,
            pool_config=PoolConfig()
        )
    return _connection_manager.get_engine()
```

#### 예상 효과
- ✅ **코드 감소**: 150줄 → 30줄 (wrapper)
- ✅ **테스트 가능**: Config를 주입하여 테스트
- ✅ **재사용**: 다른 DB 연결에도 사용 가능
- ✅ **명확성**: 설정/연결/풀 책임 분리

---

### 1.3 Repository Pattern 강화 ⭐⭐⭐

#### 현재 문제

**5개 서비스가 직접 DB 접근**:
```python
# ❌ Anti-pattern
from app.services.yfinance_db import load_ticker_data

class PortfolioService:
    async def run_backtest(...):
        # Repository를 우회하고 직접 DB 접근
        df = await asyncio.to_thread(
            load_ticker_data, symbol, start_date, end_date
        )
```

**위반 위치**:
1. `portfolio_service.py`: 5회 호출
2. `backtest_engine.py`: 2회 호출
3. `data_service.py`: 직접 접근
4. `unified_data_service.py`: 직접 접근
5. `chart_data_service.py`: 혼용 (일부는 repository 사용)

#### 목표 구조

**Repository 계층 강화**:
```
app/repositories/
├── __init__.py
├── data_repository.py          (기존) - 캐싱 + 조율
├── stock_repository.py          (신규) - 주가 데이터
├── news_repository.py           (신규) - 뉴스 데이터
└── exchange_rate_repository.py  (신규) - 환율 데이터
```

#### 추가할 Repository

**1. StockRepository** (stock_repository.py)
```python
class StockRepository:
    """주가 데이터 저장소"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_price_data(
        self,
        ticker: str,
        start_date: Union[str, date],
        end_date: Union[str, date]
    ) -> pd.DataFrame:
        """
        주가 데이터 조회 (3-tier caching)

        1. In-memory cache 확인
        2. MySQL cache 확인
        3. yfinance API 호출
        """
        # asyncio.to_thread로 동기 함수 안전하게 호출
        return await asyncio.to_thread(
            load_ticker_data, ticker, start_date, end_date
        )

    async def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """종목 정보 조회"""
        return await asyncio.to_thread(
            get_ticker_info_from_db, ticker
        )

    async def get_ticker_info_batch(
        self,
        tickers: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """종목 정보 배치 조회"""
        return await asyncio.to_thread(
            get_ticker_info_batch_from_db, tickers
        )
```

**2. 기존 DataRepository 활용**
```python
# app/repositories/data_repository.py (이미 존재)
class DataRepository:
    """
    데이터 저장소 파사드

    여러 데이터 소스를 조율하는 상위 레벨 Repository
    """
    def __init__(self):
        self.stock_repo = StockRepository()
        self.news_repo = NewsRepository()
        self.exchange_repo = ExchangeRateRepository()

    async def get_stock_data(self, ticker, start, end):
        """기존 메서드 유지 (역호환성)"""
        return await self.stock_repo.get_price_data(ticker, start, end)
```

#### 마이그레이션 계획

**Step 1: StockRepository 생성**
```bash
# 새 파일 생성
touch app/repositories/stock_repository.py
```

**Step 2: 서비스별 수정**

**portfolio_service.py 수정**:
```python
# Before
from app.services.yfinance_db import load_ticker_data, get_ticker_info_batch_from_db

class PortfolioService:
    async def run_backtest(...):
        df = await asyncio.to_thread(load_ticker_data, symbol, start, end)
        ticker_info = await asyncio.to_thread(get_ticker_info_batch_from_db, symbols)

# After
from app.repositories.stock_repository import stock_repository

class PortfolioService:
    def __init__(self, stock_repo: StockRepository = None):
        self.stock_repo = stock_repo or stock_repository

    async def run_backtest(...):
        df = await self.stock_repo.get_price_data(symbol, start, end)
        ticker_info = await self.stock_repo.get_ticker_info_batch(symbols)
```

**backtest_engine.py 수정**:
```python
# Before
from app.services.yfinance_db import load_ticker_data

class BacktestEngine:
    async def _get_price_data(...):
        data = await asyncio.to_thread(
            self.data_fetcher.get_stock_data, ticker, start, end
        )

# After
class BacktestEngine:
    def __init__(
        self,
        data_repository=None,  # 이미 있음
        stock_repo: StockRepository = None,  # 추가
        ...
    ):
        self.data_repository = data_repository
        self.stock_repo = stock_repo or stock_repository

    async def _get_price_data(...):
        # Repository 우선 사용
        if self.data_repository:
            return await self.data_repository.get_stock_data(ticker, start, end)
        else:
            return await self.stock_repo.get_price_data(ticker, start, end)
```

**Step 3: 모든 직접 import 제거**
```python
# 제거 대상
from app.services.yfinance_db import load_ticker_data
from app.services.yfinance_db import get_ticker_info_from_db
from app.services.yfinance_db import get_ticker_info_batch_from_db

# 대체
from app.repositories.stock_repository import stock_repository
# 또는 DI를 통해 주입
```

**Step 4: Global instance 생성**
```python
# app/repositories/stock_repository.py
# 파일 끝에
stock_repository = StockRepository()
```

#### 체크리스트

**파일별 마이그레이션**:
- [x] `StockRepository` 생성 (app/repositories/stock_repository.py)
- [x] `portfolio_service.py`: `load_ticker_data`, `get_ticker_info_batch_from_db` → `stock_repository` 사용
- [x] `backtest_engine.py`: 미사용 import 제거 (data_repository 사용)
- [x] `data_service.py`: `load_ticker_data` → `stock_repository` 사용
- [x] `currency_converter.py`: `load_ticker_data`, `get_ticker_info_from_db` → `stock_repository` 사용
- [x] `data_repository.py`: `load_ticker_data`, `save_ticker_data` → `stock_repository` 사용
- [x] `portfolio_simulator.py`: 미사용 import 제거
- [x] 모든 직접 yfinance_db import 제거 (stock_repository만 사용)

**마이그레이션 완료**:
✅ Phase 1.3 Repository Pattern 강화 완료 (5개 서비스 모두 마이그레이션)

**테스트 (추후)**:
- [ ] 각 서비스별 unit test 통과
- [ ] Integration test 통과 (실제 DB 연결)
- [ ] E2E test 통과 (API 엔드포인트)

#### 예상 효과
- ✅ **데이터 접근 통합**: 모든 데이터 접근이 Repository를 통함
- ✅ **캐싱 일관성**: Repository에서 캐싱 정책 중앙 관리
- ✅ **테스트 용이성**: Mock repository로 쉽게 테스트
- ✅ **유지보수성**: 데이터 소스 변경 시 Repository만 수정

---

## 📅 Phase 2: 코드 품질 개선 (2-3주)

### 우선순위: ⭐⭐ 높음

Phase 1 완료 후 진행하며, 코드 품질과 확장성을 개선합니다.

---

## ✅ Phase 2.1 실행 현황

**Phase 2.1: chart_data_service.py Indicator Strategy Pattern - 완료** (2025-11-16)

### 완료된 작업

- ✅ IndicatorStrategy 추상 기본 클래스 생성 (base.py, 97줄)
  - 모든 지표가 구현해야 할 인터페이스 정의
  - 공통 검증 로직 (_validate_data)
  - 공통 로깅 로직 (_log_calculation)
  - Commits: ea82411

- ✅ SmaIndicator 구현 (sma_indicator.py, 100줄)
  - short_window (default 10), long_window (default 20) 지원
  - SMA_short, SMA_long 컬럼 추가
  - Commits: cdb1d7c

- ✅ RsiIndicator 구현 (rsi_indicator.py, 129줄)
  - Wilder's method (EMA 기반) 구현
  - period (14), overbought (70), oversold (30) 지원
  - 나눗셈 0 보호 (np.finfo(float).eps)
  - Commits: 29b6878

- ✅ BollingerIndicator 구현 (bollinger_indicator.py, 116줄)
  - period (20), std_dev (2.0) 지원
  - BB_MIDDLE, BB_UPPER, BB_LOWER 컬럼 추가
  - Commits: 8259aac

- ✅ MacdIndicator 구현 (macd_indicator.py, 127줄)
  - fast_period (12), slow_period (26), signal_period (9) 지원
  - MACD, MACD_SIGNAL, MACD_HISTOGRAM 컬럼 추가
  - Commits: b2c2557

- ✅ EmaIndicator 구현 (ema_indicator.py, 110줄)
  - short_span (12), long_span (26) 지원
  - EMA_short, EMA_long 컬럼 추가
  - Commits: e502bf2

- ✅ IndicatorFactory 생성 (__init__.py, 157줄)
  - 모든 5개 지표 자동 등록
  - get_indicator(name) 팩토리 메서드
  - register(name, indicator) 확장 메서드
  - list_indicators() 발견 메서드
  - Commits: b4b0a8f

- ✅ ChartDataService 리팩터링 (chart_data_service.py)
  - STRATEGY_TO_INDICATOR_MAP 상수 추가 (전략→지표 매핑)
  - _generate_indicators() 메서드 리팩터링 (Factory Pattern 적용)
  - _convert_indicator_results() 추가 (결과 변환)
  - 5개 _extract_*_lines() 추가 (지표별 결과 추출)
  - 224줄의 중복 지표 계산 로직 제거
  - Commits: 6fdde4f

### 통계 (Phase 2.1)
- 생성된 클래스: 6개 (5개 지표 + 1개 팩토리)
- 생성된 파일: 6개 (base + 5개 지표 + __init__)
- 총 추가 라인: ~637줄 (indicators 패키지)
- 제거된 라인: 224줄 (chart_data_service 중복 로직)
- 순 변경: +413줄 (더 나은 구조)
- 파일 크기: chart_data_service 627줄 → 598줄 (-29줄)

### 아키텍처 개선 효과

✅ **Open/Closed Principle (OCP)**
- 새로운 지표 추가 시 chart_data_service 수정 불필요
- IndicatorFactory에 등록만 하면 자동으로 사용 가능

✅ **Single Responsibility Principle (SRP)**
- 각 지표는 자신의 계산 로직만 담당
- ChartDataService는 지표 오케스트레이션만 담당

✅ **코드 재사용성**
- 각 지표를 독립적으로 테스트 가능
- 지표 로직을 다른 서비스에서도 재사용 가능

✅ **유지보수성**
- 지표별 버그 수정이 한 곳에서만 필요
- 파라미터 변경이 명확하고 일관성 있음

---

## ✅ Phase 2.2 실행 현황

**Phase 2.2: Naming Convention 표준화 - 진행 중** (2025-11-16)

### 완료된 작업

- ✅ Phase 2.2.1: DCACalculator → DcaCalculator 변경
  - dca_calculator.py: 클래스 정의 변경
  - dca_calculator.py: docstring 예제 코드 업데이트
  - portfolio_service.py: import 및 사용처 업데이트
  - docs/architecture/date_calculation.md: 문서 업데이트
  - Commits: c10b9a7

- ✅ Phase 2.2.2: Strategy 클래스들 (SMA, EMA, RSI, MACD) 변경
  - strategies.py: SMACrossStrategy → SmaCrossStrategy
  - strategies.py: EMAStrategy → EmaStrategy
  - strategies.py: RSIStrategy → RsiStrategy
  - strategies.py: MACDStrategy → MacdStrategy
  - __init__.py: export 업데이트
  - strategy_service.py: import 및 STRATEGIES 딕셔너리 업데이트
  - tests/unit/test_sma_strategy.py: import 및 클래스 참조 업데이트
  - tests/unit/test_ema_strategy.py: import 및 클래스 참조 업데이트
  - tests/unit/test_rsi_strategy.py: import 및 클래스 참조 업데이트
  - tests/unit/test_macd_strategy.py: import 및 클래스 참조 업데이트
  - tests/unit/test_strategy_service.py: import 및 클래스 참조 업데이트
  - Commits: (pending)

- ✅ Phase 2.2.3: YFinance → Yfinance 변경
  - data_repository.py: YFinanceDataRepository → YfinanceDataRepository
  - exceptions.py: YFinanceRateLimitError → YfinanceRateLimitError
  - data_fetcher.py: YFinanceRateLimitError → YfinanceRateLimitError
  - decorators.py: YFinanceRateLimitError import 업데이트
  - Commits: (pending)

- ✅ Phase 2.2.4: PortfolioCalculatorService → PortfolioCalculator 변경
  - portfolio_calculator_service.py: PortfolioCalculatorService → PortfolioCalculator
  - portfolio_calculator_service.py: portfolio_calculator_service → portfolio_calculator (싱글톤 인스턴스)
  - portfolio_service.py: import 및 사용처 업데이트
  - Commits: (pending)

### 진행 예정
- ⏳ Phase 2.2.5: NaverNewsService → NewsService 변경
- ⏳ Phase 2.2.6: DataFetcher 메서드 (get_ → fetch_) 변경

---

### 2.1 chart_data_service.py Indicator Strategy Pattern

#### 현재 문제

**반복적인 indicator 생성 메서드**:
```python
class ChartDataService:
    def _generate_sma_indicator(...):      # 80줄
        """SMA 계산 로직"""

    def _generate_rsi_indicator(...):      # 90줄
        """RSI 계산 로직"""

    def _generate_bollinger_indicator(...): # 100줄
        """Bollinger Bands 계산 로직"""

    def _generate_macd_indicator(...):     # 85줄
        """MACD 계산 로직"""

    def _generate_ema_indicator(...):      # 75줄
        """EMA 계산 로직"""
```

**문제점**:
- 각 50-100줄의 유사한 패턴
- 새 지표 추가 시 ChartDataService 수정 필요 (OCP 위반)
- 지표별 테스트 어려움

#### 목표 구조

**Strategy Pattern 적용**:
```
app/services/indicators/
├── __init__.py                    (30줄)
├── base.py                        (40줄) - IndicatorStrategy ABC
├── sma_indicator.py               (80줄)
├── rsi_indicator.py               (90줄)
├── bollinger_indicator.py         (100줄)
├── macd_indicator.py              (85줄)
└── ema_indicator.py               (75줄)
```

#### 구현

**1. Base Strategy** (base.py)
```python
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional

class IndicatorStrategy(ABC):
    """기술 지표 계산 전략 인터페이스"""

    @abstractmethod
    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        지표 계산

        Args:
            data: OHLC 데이터
            params: 지표별 파라미터

        Returns:
            지표 값이 추가된 DataFrame
        """
        pass

    @abstractmethod
    def get_indicator_name(self) -> str:
        """지표 이름 반환"""
        pass
```

**2. Concrete Strategies**

**SMAIndicator** (sma_indicator.py):
```python
class SMAIndicator(IndicatorStrategy):
    """Simple Moving Average 지표"""

    def calculate(self, data: pd.DataFrame, params: Optional[Dict] = None) -> pd.DataFrame:
        params = params or {}
        period = params.get('sma_period', 20)

        result = data.copy()
        result['SMA'] = data['Close'].rolling(window=period).mean()
        return result

    def get_indicator_name(self) -> str:
        return 'SMA'
```

**RSIIndicator** (rsi_indicator.py):
```python
class RSIIndicator(IndicatorStrategy):
    """Relative Strength Index 지표"""

    def calculate(self, data: pd.DataFrame, params: Optional[Dict] = None) -> pd.DataFrame:
        params = params or {}
        period = params.get('rsi_period', 14)

        result = data.copy()
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
        return result

    def get_indicator_name(self) -> str:
        return 'RSI'
```

**3. Indicator Factory** (__init__.py)
```python
from .base import IndicatorStrategy
from .sma_indicator import SMAIndicator
from .rsi_indicator import RSIIndicator
from .bollinger_indicator import BollingerIndicator
from .macd_indicator import MACDIndicator
from .ema_indicator import EMAIndicator

class IndicatorFactory:
    """지표 생성 팩토리"""

    _indicators: Dict[str, IndicatorStrategy] = {
        'sma': SMAIndicator(),
        'rsi': RSIIndicator(),
        'bollinger': BollingerIndicator(),
        'macd': MACDIndicator(),
        'ema': EMAIndicator(),
    }

    @classmethod
    def get_indicator(cls, name: str) -> IndicatorStrategy:
        """지표 전략 가져오기"""
        indicator = cls._indicators.get(name.lower())
        if not indicator:
            raise ValueError(f"Unknown indicator: {name}")
        return indicator

    @classmethod
    def register_indicator(cls, name: str, indicator: IndicatorStrategy):
        """새 지표 등록 (확장 포인트)"""
        cls._indicators[name.lower()] = indicator

# Global instance
indicator_factory = IndicatorFactory()
```

**4. ChartDataService 수정**

**Before**:
```python
class ChartDataService:
    def _generate_indicators(self, data, strategy_name, params):
        indicators = []

        if strategy_name == 'sma_strategy':
            # 80줄 SMA 로직
            ...
        elif strategy_name == 'rsi_strategy':
            # 90줄 RSI 로직
            ...
        # ... 500줄 더

        return indicators
```

**After**:
```python
from app.services.indicators import indicator_factory

class ChartDataService:
    def _generate_indicators(self, data, strategy_name, params):
        indicators = []

        # 전략명에서 지표 타입 추출
        indicator_type = self._extract_indicator_type(strategy_name)

        if indicator_type:
            try:
                indicator = indicator_factory.get_indicator(indicator_type)
                result_data = indicator.calculate(data, params)

                # IndicatorData 형식으로 변환
                indicators.append(IndicatorData(
                    name=indicator.get_indicator_name(),
                    data=result_data.to_dict(orient='records')
                ))
            except ValueError as e:
                self.logger.warning(f"Indicator not found: {e}")

        return indicators

    def _extract_indicator_type(self, strategy_name: str) -> Optional[str]:
        """전략명에서 지표 타입 추출"""
        # 'sma_strategy' -> 'sma'
        # 'rsi_strategy' -> 'rsi'
        if strategy_name.endswith('_strategy'):
            return strategy_name.replace('_strategy', '')
        return None
```

#### 예상 효과
- ✅ **코드 감소**: 626줄 → 50-100줄 (ChartDataService)
- ✅ **OCP 준수**: 새 지표 추가 시 기존 코드 수정 불필요
- ✅ **테스트 용이성**: 지표별 독립 테스트
- ✅ **확장성**: `register_indicator()`로 런타임 확장

---

### 2.2 Naming Convention 표준화

#### 현재 불일치

**Data Fetching 메서드**:
```python
# 혼용
get_stock_data()      # 캐시된 데이터
load_ticker_data()    # DB에서 로드
fetch_from_yfinance() # 외부 API
get_price_data()      # 캐시 or API?
```

**클래스 명명**:
```python
NaverNewsService      # ✅ 일관성
DCACalculator         # ❌ 'DCA' 대문자
RebalanceHelper       # ✅ Helper suffix
PortfolioCalculatorService  # ❌ 너무 길고 불명확
```

#### 표준화 규칙

**메서드 Prefix**:

| Prefix | 용도 | 예시 | 캐싱 여부 |
|--------|------|------|-----------|
| `get_` | 캐시된 데이터 조회 | `get_stock_data()` | ✅ Yes |
| `fetch_` | 외부 API 호출 (신선한 데이터) | `fetch_from_yfinance()` | ❌ No |
| `load_` | DB에서 조회 | `load_ticker_data()` | ✅ DB Cache |
| `calculate_` | 계산/연산 | `calculate_statistics()` | ❌ No |
| `validate_` | 검증 | `validate_params()` | ❌ No |
| `execute_` | 액션 수행 | `execute_rebalancing()` | ❌ No |

**클래스 Suffix**:

| Suffix | 용도 | 예시 |
|--------|------|------|
| `*Service` | 비즈니스 로직 서비스 | `PortfolioService` |
| `*Repository` | 데이터 저장소 | `StockRepository` |
| `*Calculator` | 계산 전담 | `DcaCalculator` |
| `*Helper` | 유틸리티 헬퍼 | `RebalanceHelper` |
| `*Manager` | 리소스 관리 | `PortfolioDcaManager` |
| `*Engine` | 핵심 실행 엔진 | `BacktestEngine` |

#### 변경 계획

**클래스 이름**:
```python
# Before
class DCACalculator:        # ❌ 대문자 약어
class NaverNewsService:     # ✅ 유지
class PortfolioCalculatorService:  # ❌ 중복 suffix

# After
class DcaCalculator:        # ✅ Pascal case
class NewsService:          # ✅ 간결화 (Naver는 impl detail)
class PortfolioMetrics:     # ✅ 명확한 책임
```

**메서드 이름**:
```python
# Before
def get_ticker_info()      # DB에서? API에서?
def load_ticker_data()     # 명확함 ✅
def fetch_stock_data()     # 명확함 ✅

# After
def load_ticker_info()     # DB에서 로드
def fetch_ticker_info()    # API에서 fetch
def get_stock_data()       # 캐시 우선 조회
```

#### 마이그레이션 전략

**Step 1: 별칭(Alias) 생성**
```python
# 기존 이름 유지하면서 새 이름 추가
class DcaCalculator:
    pass

# Backward compatibility
DCACalculator = DcaCalculator  # Deprecated alias
```

**Step 2: Deprecation Warning**
```python
import warnings

class DCACalculator(DcaCalculator):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "DCACalculator is deprecated, use DcaCalculator instead",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

**Step 3: 단계적 제거**
- Version N: 새 이름 도입 + 별칭
- Version N+1: Deprecation warning
- Version N+2: 별칭 제거

---

### 2.3 Validation Logic 통합

#### 현재 문제

**Validation 3곳에 분산**:
```python
# 1. Pydantic schemas (schemas.py)
class BacktestRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date

    @validator('end_date')
    def validate_end_date(cls, v, values):
        # 날짜 검증 로직
        ...

# 2. validation_service.py
class ValidationService:
    def validate_backtest_request(self, request):
        # 또 다른 날짜 검증
        ...

# 3. 개별 서비스
class BacktestEngine:
    async def run_backtest(self, request):
        if request.end_date < request.start_date:
            raise ValueError(...)
```

#### 목표 구조

**책임 분리**:
```
app/validators/
├── __init__.py
├── backtest_validator.py    - 백테스트 비즈니스 규칙
├── portfolio_validator.py   - 포트폴리오 비즈니스 규칙
├── date_validator.py        - 날짜 검증 로직
└── symbol_validator.py      - 심볼 검증 로직
```

**역할 정의**:
- **Pydantic schemas**: 타입 검증만 (str, int, date 등)
- **Validators**: 비즈니스 규칙 검증
- **Services**: 검증 호출 + 로직 실행

#### 구현

**1. Date Validator** (date_validator.py)
```python
from datetime import date, timedelta

class DateValidator:
    """날짜 검증 로직"""

    @staticmethod
    def validate_date_range(
        start_date: date,
        end_date: date,
        min_days: int = 1,
        max_days: int = 3650
    ) -> None:
        """날짜 범위 검증"""
        if end_date < start_date:
            raise ValueError(
                f"종료일({end_date})이 시작일({start_date})보다 이전입니다"
            )

        delta = (end_date - start_date).days

        if delta < min_days:
            raise ValueError(
                f"백테스트 기간이 너무 짧습니다: {delta}일 (최소 {min_days}일)"
            )

        if delta > max_days:
            raise ValueError(
                f"백테스트 기간이 너무 깁니다: {delta}일 (최대 {max_days}일)"
            )

    @staticmethod
    def validate_not_future(target_date: date) -> None:
        """미래 날짜가 아닌지 검증"""
        today = date.today()
        if target_date > today:
            raise ValueError(
                f"미래 날짜는 사용할 수 없습니다: {target_date} (오늘: {today})"
            )
```

**2. Backtest Validator** (backtest_validator.py)
```python
from app.validators.date_validator import DateValidator
from app.validators.symbol_validator import SymbolValidator

class BacktestValidator:
    """백테스트 비즈니스 규칙 검증"""

    def __init__(self):
        self.date_validator = DateValidator()
        self.symbol_validator = SymbolValidator()

    def validate_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 전체 검증"""
        # 날짜 검증
        self.date_validator.validate_date_range(
            request.start_date,
            request.end_date
        )
        self.date_validator.validate_not_future(request.end_date)

        # 심볼 검증
        self.symbol_validator.validate_ticker(request.ticker)

        # 초기 자본 검증
        if request.initial_cash <= 0:
            raise ValueError(
                f"초기 자본은 0보다 커야 합니다: {request.initial_cash}"
            )

        # 수수료 검증
        if not 0 <= request.commission < 0.1:
            raise ValueError(
                f"수수료는 0~10% 사이여야 합니다: {request.commission}"
            )
```

**3. Pydantic Schema 단순화**

**Before**:
```python
class BacktestRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date
    initial_cash: float

    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v) > 10:
            raise ValueError("Invalid ticker")
        return v.upper()

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("end_date must be after start_date")
        return v
```

**After**:
```python
class BacktestRequest(BaseModel):
    """타입 검증만 수행"""
    ticker: str
    start_date: date
    end_date: date
    initial_cash: float = Field(gt=0)
    commission: float = Field(ge=0, lt=0.1)

    # 비즈니스 규칙 검증은 제거
    # → BacktestValidator로 이동
```

**4. Service에서 사용**

**Before**:
```python
class BacktestEngine:
    async def run_backtest(self, request):
        # 검증 로직 내장
        if request.end_date < request.start_date:
            raise ValueError(...)
        if request.initial_cash <= 0:
            raise ValueError(...)
        # ... 실행
```

**After**:
```python
from app.validators import BacktestValidator

class BacktestEngine:
    def __init__(self, validator: BacktestValidator = None):
        self.validator = validator or BacktestValidator()

    async def run_backtest(self, request):
        # 검증 위임
        self.validator.validate_request(request)

        # 실행 로직에만 집중
        ...
```

#### 예상 효과
- ✅ **단일 책임**: 검증 로직이 Validator에 집중
- ✅ **재사용**: 같은 검증 로직을 여러 곳에서 사용
- ✅ **테스트**: Validator만 독립 테스트
- ✅ **명확성**: Pydantic은 타입만, Validator는 규칙만

---

## 📅 Phase 3: 아키텍처 개선 (3-4주)

### 우선순위: ⭐ 중간

Phase 1, 2 완료 후 진행하며, 장기적인 아키텍처 개선을 목표로 합니다.

---

### 3.1 Domain Model 도입

#### 현재 문제: Primitive Obsession

**문제 코드**:
```python
# 모든 것이 primitive type
amount: float = 1000.0
currency: str = 'USD'
weight: float = 0.3
commission: float = 0.002

# 비즈니스 규칙이 서비스에 흩어짐
if weight < 0 or weight > 1:
    raise ValueError("Weight must be 0-1")

if currency not in SUPPORTED_CURRENCIES:
    raise ValueError(f"Unsupported currency: {currency}")
```

**문제점**:
- 타입 안전성 결여 (float는 금액? 비중? 수수료?)
- 비즈니스 규칙이 여러 곳에 중복
- 도메인 지식이 코드에 명확히 드러나지 않음

#### 목표: Rich Domain Model

**구조**:
```
app/domain/
├── __init__.py
├── value_objects/
│   ├── money.py           - Money 값 객체
│   ├── weight.py          - Weight 값 객체
│   ├── date_range.py      - DateRange 값 객체
│   └── commission.py      - Commission 값 객체
├── entities/
│   ├── portfolio.py       - Portfolio 엔티티
│   ├── asset.py           - Asset 엔티티
│   └── trade.py           - Trade 엔티티
└── repositories/
    └── portfolio_repository.py
```

#### Value Objects

**1. Money** (money.py)
```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass(frozen=True)
class Money:
    """금액 값 객체 (불변)"""
    amount: Decimal
    currency: str = 'USD'

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")
        if self.currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def to_usd(self, exchange_rate: 'ExchangeRate') -> 'Money':
        """USD로 변환"""
        if self.currency == 'USD':
            return self

        usd_amount = exchange_rate.convert(self)
        return Money(amount=usd_amount, currency='USD')

    def __add__(self, other: 'Money') -> 'Money':
        """금액 더하기 (같은 통화만)"""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} + {other.currency}"
            )
        return Money(
            amount=self.amount + other.amount,
            currency=self.currency
        )

    def __mul__(self, multiplier: float) -> 'Money':
        """금액 곱하기"""
        return Money(
            amount=self.amount * Decimal(str(multiplier)),
            currency=self.currency
        )

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"
```

**2. Weight** (weight.py)
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Weight:
    """포트폴리오 비중 값 객체 (0~1)"""
    value: float

    def __post_init__(self):
        if not 0 <= self.value <= 1:
            raise ValueError(f"Weight must be 0-1, got {self.value}")

    @classmethod
    def from_percentage(cls, percentage: float) -> 'Weight':
        """퍼센트(0-100)에서 생성"""
        return cls(value=percentage / 100)

    def to_percentage(self) -> float:
        """퍼센트로 변환"""
        return self.value * 100

    def __str__(self) -> str:
        return f"{self.to_percentage():.2f}%"
```

**3. DateRange** (date_range.py)
```python
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass(frozen=True)
class DateRange:
    """날짜 범위 값 객체"""
    start: date
    end: date

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError(
                f"End date {self.end} is before start date {self.start}"
            )

    @property
    def duration_days(self) -> int:
        """기간 (일)"""
        return (self.end - self.start).days

    def contains(self, target: date) -> bool:
        """날짜 포함 여부"""
        return self.start <= target <= self.end

    def __str__(self) -> str:
        return f"{self.start} ~ {self.end} ({self.duration_days}일)"
```

#### Entities

**1. Portfolio** (portfolio.py)
```python
from dataclasses import dataclass, field
from typing import List, Dict
from app.domain.value_objects import Money, Weight
from app.domain.entities import Asset, Trade

@dataclass
class Portfolio:
    """포트폴리오 엔티티"""
    id: str
    assets: List[Asset] = field(default_factory=list)
    weights: Dict[str, Weight] = field(default_factory=dict)
    cash: Money = field(default_factory=lambda: Money(Decimal('0'), 'USD'))

    def total_value(self) -> Money:
        """총 포트폴리오 가치"""
        asset_value = sum(
            (asset.current_price * asset.quantity for asset in self.assets),
            start=Money(Decimal('0'), 'USD')
        )
        return asset_value + self.cash

    def rebalance(self, target_weights: Dict[str, Weight]) -> List[Trade]:
        """
        리밸런싱 로직을 도메인에 캡슐화

        Returns:
            필요한 거래 목록
        """
        trades = []
        total_value = self.total_value()

        for asset in self.assets:
            current_weight = self._calculate_current_weight(asset)
            target_weight = target_weights.get(asset.symbol, Weight(0))

            if abs(current_weight.value - target_weight.value) > 0.01:  # 1% 이상 차이
                target_value = total_value * target_weight.value
                current_value = asset.current_price * asset.quantity

                if target_value > current_value:
                    # 매수
                    shares_to_buy = (target_value - current_value) / asset.current_price
                    trades.append(Trade(
                        asset=asset,
                        action='BUY',
                        quantity=shares_to_buy,
                        price=asset.current_price
                    ))
                else:
                    # 매도
                    shares_to_sell = (current_value - target_value) / asset.current_price
                    trades.append(Trade(
                        asset=asset,
                        action='SELL',
                        quantity=shares_to_sell,
                        price=asset.current_price
                    ))

        return trades

    def add_dca_purchase(self, asset: Asset, amount: Money) -> None:
        """DCA 투자 추가"""
        shares = amount.amount / asset.current_price.amount

        # 기존 자산 찾기
        existing_asset = next(
            (a for a in self.assets if a.symbol == asset.symbol),
            None
        )

        if existing_asset:
            existing_asset.quantity += shares
        else:
            asset.quantity = shares
            self.assets.append(asset)

        self.cash = self.cash - amount

    def _calculate_current_weight(self, asset: Asset) -> Weight:
        """현재 비중 계산"""
        total = self.total_value()
        asset_value = asset.current_price * asset.quantity
        return Weight(value=float(asset_value.amount / total.amount))
```

**2. Asset** (asset.py)
```python
from dataclasses import dataclass
from app.domain.value_objects import Money

@dataclass
class Asset:
    """자산 엔티티"""
    symbol: str
    name: str
    current_price: Money
    quantity: float = 0.0

    @property
    def total_value(self) -> Money:
        """총 가치"""
        return self.current_price * self.quantity
```

#### 사용 예시

**Before (Primitive Obsession)**:
```python
# portfolio_service.py
def execute_rebalancing(
    shares: Dict[str, float],  # 뭘 의미하는지 불명확
    prices: Dict[str, float],   # USD? KRW?
    weights: Dict[str, float],  # 0-1? 0-100?
    cash: float                 # USD? KRW?
):
    # 비즈니스 규칙이 여기저기 흩어짐
    for symbol, target_weight in weights.items():
        if target_weight < 0 or target_weight > 1:
            raise ValueError(...)
        # ... 100줄의 복잡한 로직
```

**After (Rich Domain Model)**:
```python
# domain/entities/portfolio.py
portfolio = Portfolio(
    id="portfolio-1",
    assets=[
        Asset('AAPL', 'Apple Inc.', Money(Decimal('150'), 'USD'), quantity=10),
        Asset('GOOGL', 'Alphabet', Money(Decimal('2800'), 'USD'), quantity=5)
    ],
    weights={
        'AAPL': Weight(0.6),
        'GOOGL': Weight(0.4)
    },
    cash=Money(Decimal('1000'), 'USD')
)

# 리밸런싱 로직이 도메인에 캡슐화됨
target_weights = {
    'AAPL': Weight(0.5),
    'GOOGL': Weight(0.5)
}
trades = portfolio.rebalance(target_weights)

# 서비스는 얇아짐
class PortfolioService:
    async def rebalance_portfolio(self, portfolio_id: str, target_weights):
        portfolio = await self.repo.get_portfolio(portfolio_id)
        trades = portfolio.rebalance(target_weights)
        await self.trade_executor.execute(trades)
```

#### 예상 효과
- ✅ **타입 안전성**: Money는 Money, Weight는 Weight
- ✅ **비즈니스 규칙 캡슐화**: Portfolio.rebalance()
- ✅ **테스트 용이성**: 도메인 객체만 단위 테스트
- ✅ **가독성**: 코드가 도메인 언어로 표현됨

---

### 3.2 Dependency Injection 강화

#### 현재 문제

**Global Singleton 남용**:
```python
# 모듈 레벨에서 생성
strategy_service = StrategyService()
backtest_service = BacktestService()
portfolio_service = PortfolioService()

# 다른 파일에서 import
from app.services.strategy_service import strategy_service
```

**문제점**:
- 초기화 순서 의존성
- Circular import 위험
- 테스트 시 mocking 어려움
- 설정 변경 불가

#### 목표: Constructor Injection

**구조**:
```
app/di/
├── __init__.py
├── container.py       - Service Container
└── providers.py       - Provider 함수들
```

#### DI Container 개선

**Before** (container.py):
```python
class ServiceContainer:
    """현재 단순한 Registry 패턴"""
    _instances = {}

    @classmethod
    def register(cls, name, instance):
        cls._instances[name] = instance

    @classmethod
    def get(cls, name):
        return cls._instances.get(name)
```

**After** (container.py):
```python
from typing import Type, TypeVar, Callable, Dict, Any

T = TypeVar('T')

class ServiceContainer:
    """DI Container with factory support"""

    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register_singleton(self, interface: Type[T], instance: T):
        """싱글톤 인스턴스 등록"""
        self._singletons[interface] = instance

    def register_factory(self, interface: Type[T], factory: Callable[[], T]):
        """팩토리 함수 등록"""
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """의존성 해결"""
        # 싱글톤 먼저 확인
        if interface in self._singletons:
            return self._singletons[interface]

        # 팩토리로 생성
        if interface in self._factories:
            instance = self._factories[interface]()
            return instance

        raise ValueError(f"No registration found for {interface}")

    def resolve_with_deps(self, cls: Type[T]) -> T:
        """의존성 자동 주입 (타입 힌트 기반)"""
        import inspect

        sig = inspect.signature(cls.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            if param.annotation != inspect.Parameter.empty:
                # 타입 힌트가 있으면 자동 resolve
                dep = self.resolve(param.annotation)
                kwargs[param_name] = dep

        return cls(**kwargs)

# Global container
container = ServiceContainer()
```

#### Service Registration

**providers.py**:
```python
from app.di.container import container
from app.repositories import StockRepository, DataRepository
from app.services import (
    StrategyService,
    ValidationService,
    BacktestEngine,
    PortfolioService
)

def register_repositories():
    """Repository 등록"""
    container.register_singleton(
        StockRepository,
        StockRepository()
    )
    container.register_singleton(
        DataRepository,
        DataRepository()
    )

def register_services():
    """Service 등록 (팩토리 패턴)"""

    # StrategyService (싱글톤)
    container.register_singleton(
        StrategyService,
        StrategyService()
    )

    # ValidationService (싱글톤)
    container.register_singleton(
        ValidationService,
        ValidationService()
    )

    # BacktestEngine (팩토리 - 매번 새 인스턴스)
    def create_backtest_engine():
        return BacktestEngine(
            data_repository=container.resolve(DataRepository),
            strategy_service=container.resolve(StrategyService),
            validation_service=container.resolve(ValidationService)
        )
    container.register_factory(BacktestEngine, create_backtest_engine)

    # PortfolioService (팩토리)
    def create_portfolio_service():
        return PortfolioService(
            stock_repo=container.resolve(StockRepository),
            backtest_engine=container.resolve(BacktestEngine)
        )
    container.register_factory(PortfolioService, create_portfolio_service)

def initialize_di_container():
    """전체 초기화"""
    register_repositories()
    register_services()
```

#### Service 리팩터링

**Before**:
```python
# app/services/backtest_engine.py
from app.repositories.data_repository import data_repository
from app.services.strategy_service import strategy_service
from app.services.validation_service import validation_service

class BacktestEngine:
    def __init__(self):
        # Global import
        self.data_repository = data_repository
        self.strategy_service = strategy_service
        self.validation_service = validation_service
```

**After**:
```python
# app/services/backtest_engine.py
from app.repositories import DataRepository
from app.services import StrategyService, ValidationService

class BacktestEngine:
    def __init__(
        self,
        data_repository: DataRepository,
        strategy_service: StrategyService,
        validation_service: ValidationService
    ):
        # Constructor injection
        self.data_repository = data_repository
        self.strategy_service = strategy_service
        self.validation_service = validation_service
```

#### FastAPI Integration

**main.py**:
```python
from fastapi import FastAPI, Depends
from app.di.providers import initialize_di_container
from app.di.container import container

# 앱 시작 시 DI Container 초기화
@app.on_event("startup")
async def startup_event():
    initialize_di_container()

# Dependency 함수
def get_portfolio_service() -> PortfolioService:
    return container.resolve(PortfolioService)

# 엔드포인트에서 사용
@app.post("/api/v1/portfolio/backtest")
async def run_portfolio_backtest(
    request: PortfolioBacktestRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    return await portfolio_service.run_portfolio_backtest(request)
```

#### 테스트에서 사용

**Before**:
```python
# 어려운 mocking
import app.services.backtest_service
app.services.backtest_service.strategy_service = Mock()
```

**After**:
```python
# 쉬운 DI
from app.di.container import ServiceContainer

def test_portfolio_service():
    # 테스트용 container
    test_container = ServiceContainer()

    # Mock 등록
    mock_stock_repo = Mock(spec=StockRepository)
    test_container.register_singleton(StockRepository, mock_stock_repo)

    # 서비스 생성 (자동으로 mock 주입)
    portfolio_service = test_container.resolve_with_deps(PortfolioService)

    # 테스트 실행
    ...
```

#### 예상 효과
- ✅ **테스트 용이성**: 의존성 쉽게 mocking
- ✅ **유연성**: 런타임에 구현체 교체 가능
- ✅ **명확한 의존성**: 생성자에서 명시적 표현
- ✅ **Circular dependency 방지**: Container가 해결

---

### 3.3 CQRS-lite 패턴 (선택사항)

#### 개념

**CQRS**: Command Query Responsibility Segregation
- **Command**: 상태 변경 작업 (백테스트 실행, 포트폴리오 리밸런싱)
- **Query**: 데이터 조회 (차트 데이터, 뉴스, 통계)

**CQRS-lite**: 완전한 CQRS는 아니고, 읽기/쓰기를 명확히 분리

#### 목표 구조

```
app/commands/
├── __init__.py
├── base.py                           - Command 인터페이스
├── run_backtest_command.py           - 백테스트 실행
├── run_portfolio_backtest_command.py - 포트폴리오 백테스트
└── rebalance_portfolio_command.py    - 리밸런싱

app/queries/
├── __init__.py
├── base.py                      - Query 인터페이스
├── get_stock_data_query.py      - 주가 데이터 조회
├── get_chart_data_query.py      - 차트 데이터 조회
└── get_news_query.py            - 뉴스 조회
```

#### Command 구현

**base.py**:
```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')

class Command(ABC, Generic[TRequest, TResponse]):
    """커맨드 인터페이스"""

    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """커맨드 실행"""
        pass
```

**run_backtest_command.py**:
```python
from app.commands.base import Command
from app.schemas.requests import BacktestRequest
from app.schemas.responses import BacktestResult

class RunBacktestCommand(Command[BacktestRequest, BacktestResult]):
    """백테스트 실행 커맨드"""

    def __init__(
        self,
        backtest_engine: BacktestEngine,
        validator: BacktestValidator
    ):
        self.engine = backtest_engine
        self.validator = validator

    async def execute(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행"""
        # 검증
        self.validator.validate_request(request)

        # 실행
        result = await self.engine.run_backtest(request)

        return result
```

#### Query 구현

**base.py**:
```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TQuery = TypeVar('TQuery')
TResult = TypeVar('TResult')

class Query(ABC, Generic[TQuery, TResult]):
    """쿼리 인터페이스"""

    @abstractmethod
    async def execute(self, query: TQuery) -> TResult:
        """쿼리 실행"""
        pass
```

**get_chart_data_query.py**:
```python
from app.queries.base import Query
from app.schemas.requests import BacktestRequest
from app.schemas.responses import ChartDataResponse

class GetChartDataQuery(Query[BacktestRequest, ChartDataResponse]):
    """차트 데이터 조회 쿼리"""

    def __init__(
        self,
        chart_service: ChartDataService,
        stock_repo: StockRepository
    ):
        self.chart_service = chart_service
        self.stock_repo = stock_repo

    async def execute(self, request: BacktestRequest) -> ChartDataResponse:
        """차트 데이터 생성"""
        # 읽기 전용 (상태 변경 없음)
        data = await self.stock_repo.get_price_data(
            request.ticker,
            request.start_date,
            request.end_date
        )

        chart_data = await self.chart_service.generate_chart_data(
            request, data
        )

        return chart_data
```

#### 사용 예시

**Before**:
```python
# 서비스에 읽기/쓰기 혼재
class BacktestService:
    async def run_backtest(self, request):
        # 상태 변경 (쓰기)
        ...

    async def get_chart_data(self, request):
        # 읽기만
        ...
```

**After**:
```python
# 엔드포인트에서 Command/Query 사용
from app.commands import RunBacktestCommand
from app.queries import GetChartDataQuery

@app.post("/api/v1/backtest/run")
async def run_backtest(
    request: BacktestRequest,
    command: RunBacktestCommand = Depends(get_run_backtest_command)
):
    # Command 실행 (쓰기)
    result = await command.execute(request)
    return result

@app.get("/api/v1/backtest/chart")
async def get_chart_data(
    request: BacktestRequest,
    query: GetChartDataQuery = Depends(get_chart_data_query)
):
    # Query 실행 (읽기)
    chart_data = await query.execute(request)
    return chart_data
```

#### 예상 효과
- ✅ **명확한 책임 분리**: 읽기 vs 쓰기
- ✅ **확장성**: 읽기는 캐싱, 쓰기는 이벤트 발행 가능
- ✅ **성능 최적화**: Query는 read replica로 분산 가능
- ⚠️ **복잡도 증가**: 단순한 앱에는 오버엔지니어링 가능

---

## 📋 Phase별 체크리스트

### Phase 1 체크리스트 (필수)

**1.1 portfolio_service.py 분할**:
- [x] `PortfolioDcaManager` 클래스 추출 (commit: 3c42d84)
- [x] `PortfolioRebalancer` 클래스 추출 (commit: 9a092ec)
- [x] `PortfolioSimulator` 클래스 추출 (commit: 4e469f0)
- [x] `PortfolioMetrics` 클래스 추출 (commit: 6297fc1)
- [x] `PortfolioService` 리팩터링 (위임 패턴) (commit: f64d085)
- [x] Import 경로 업데이트 (commit: 4f61258)
- [ ] 단위 테스트 작성
- [ ] Integration 테스트 통과

**1.2 yfinance_db.py 분할**:
- [x] `DatabaseConfig` 클래스 생성 (commit: c728f37)
- [x] `PoolConfig` 클래스 생성 (commit: c728f37)
- [x] `DatabaseConnectionManager` 클래스 생성 (commit: c728f37)
- [x] `_get_engine()` 간소화 (commit: 63f3db5)
- [ ] 단위 테스트 작성

**1.3 Repository Pattern 강화**:
- [ ] `StockRepository` 생성
- [ ] `portfolio_service.py` 마이그레이션 (5개 호출)
- [ ] `backtest_engine.py` 마이그레이션 (2개 호출)
- [ ] `data_service.py` 마이그레이션
- [ ] `unified_data_service.py` 마이그레이션
- [ ] `chart_data_service.py` 마이그레이션
- [ ] 모든 직접 import 제거 확인
- [ ] Integration 테스트 통과

**Phase 1 완료 조건**:
- [ ] 모든 기존 테스트 통과
- [ ] API 엔드포인트 동작 확인
- [ ] 백테스트 결과 일치 확인 (before/after)
- [ ] 성능 벤치마크 (저하 없음)

---

### Phase 2 체크리스트 (권장)

**2.1 Indicator Strategy Pattern**:
- [ ] `IndicatorStrategy` 인터페이스 정의
- [ ] `SMAIndicator` 구현
- [ ] `RSIIndicator` 구현
- [ ] `BollingerIndicator` 구현
- [ ] `MACDIndicator` 구현
- [ ] `EMAIndicator` 구현
- [ ] `IndicatorFactory` 구현
- [ ] `ChartDataService` 리팩터링
- [ ] 지표별 단위 테스트

**2.2 Naming Convention**:
- [ ] 클래스 이름 변경 (`DCACalculator` → `DcaCalculator`)
- [ ] 메서드 prefix 표준화
- [ ] Backward compatibility alias 추가
- [ ] 문서 업데이트 (CLAUDE.md 등)

**2.3 Validation Logic**:
- [ ] `DateValidator` 생성
- [ ] `SymbolValidator` 생성
- [ ] `BacktestValidator` 생성
- [ ] `PortfolioValidator` 생성
- [ ] Pydantic schema 단순화 (타입만)
- [ ] Service에서 Validator 사용
- [ ] 검증 로직 테스트

**Phase 2 완료 조건**:
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서화 완료

---

### Phase 3 체크리스트 (선택)

**3.1 Domain Model**:
- [ ] `Money` 값 객체 구현
- [ ] `Weight` 값 객체 구현
- [ ] `DateRange` 값 객체 구현
- [ ] `Portfolio` 엔티티 구현
- [ ] `Asset` 엔티티 구현
- [ ] `Trade` 엔티티 구현
- [ ] 도메인 로직 이동 (서비스 → 도메인)
- [ ] 도메인 객체 단위 테스트

**3.2 DI Container**:
- [ ] `ServiceContainer` 개선
- [ ] Provider 함수 작성
- [ ] 모든 Service Constructor injection 변경
- [ ] FastAPI Depends 통합
- [ ] 테스트에서 DI 활용

**3.3 CQRS-lite** (평가 후 결정):
- [ ] Command/Query 인터페이스 정의
- [ ] 주요 Command 구현
- [ ] 주요 Query 구현
- [ ] 엔드포인트 리팩터링
- [ ] 성능 테스트

---

## ⚠️ 리스크 및 대응 전략

### 리스크 1: 금융 계산 로직 손상

**영향**: 백테스트 결과가 달라지면 사용자 신뢰 손실

**대응**:
1. **Golden Test 작성**
   ```python
   # 리팩터링 전 결과를 저장
   def test_portfolio_backtest_golden():
       request = PortfolioBacktestRequest(...)
       result_before = await old_portfolio_service.run_backtest(request)

       # 리팩터링 후 결과 비교
       result_after = await new_portfolio_service.run_backtest(request)

       assert result_before.final_equity == result_after.final_equity
       assert result_before.total_return_pct == result_after.total_return_pct
       # ... 모든 필드 비교
   ```

2. **샘플 데이터로 회귀 테스트**
   - 고정된 샘플 데이터로 백테스트
   - 결과를 JSON으로 저장
   - 리팩터링 후 결과 비교

3. **점진적 롤아웃**
   - Feature flag로 신/구 버전 전환
   - 소수 사용자 대상 테스트
   - 결과 모니터링 후 전체 배포

---

### 리스크 2: 성능 저하

**영향**: 백테스트 실행 시간 증가

**대응**:
1. **벤치마크 측정**
   ```python
   import time

   def benchmark_backtest():
       start = time.time()
       await portfolio_service.run_backtest(...)
       elapsed = time.time() - start

       assert elapsed < 5.0  # 5초 이내
   ```

2. **프로파일링**
   ```bash
   # cProfile로 병목 지점 확인
   python -m cProfile -o profile.stats app/main.py

   # 분석
   python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
   ```

3. **캐싱 유지**
   - Repository 캐싱 정책 유지
   - 불필요한 재계산 방지

---

### 리스크 3: API 호환성 깨짐

**영향**: 프론트엔드 또는 외부 클라이언트 오류

**대응**:
1. **API Contract 고정**
   - Request/Response schema 변경 금지
   - 내부 구현만 리팩터링

2. **E2E 테스트**
   ```python
   @pytest.mark.e2e
   async def test_portfolio_backtest_endpoint():
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.post(
               "/api/v1/portfolio/backtest",
               json=request_data
           )
           assert response.status_code == 200
           assert "final_equity" in response.json()
   ```

3. **Swagger 문서 검증**
   - OpenAPI spec이 변경되지 않았는지 확인

---

### 리스크 4: 팀원 학습 곡선

**영향**: 새로운 구조에 적응 시간 필요

**대응**:
1. **문서화**
   - 각 Phase마다 마이그레이션 가이드 작성
   - Before/After 코드 예시 제공
   - CLAUDE.md 업데이트

2. **코드 리뷰**
   - 리팩터링 PR에 충분한 설명 추가
   - 변경 이유와 효과 명시

3. **점진적 적용**
   - 한 번에 모든 것을 바꾸지 않음
   - Phase별로 나눠서 진행

---

## 📈 예상 효과 및 측정 지표

### 정량적 개선 목표

**코드 품질**:
| 지표 | Before | After | 개선율 |
|------|--------|-------|--------|
| 최대 파일 크기 | 1,820줄 | 500줄 | 72%↓ |
| 평균 함수 길이 | 80줄 | 30줄 | 62%↓ |
| Cyclomatic Complexity (평균) | 15 | 8 | 47%↓ |
| 테스트 커버리지 | 현재 | +20%p | - |

**구조 개선**:
| 지표 | Before | After | 개선율 |
|------|--------|-------|--------|
| God Object 파일 수 | 2개 | 0개 | 100%↓ |
| Static Method 비율 | 35% | 10% | 71%↓ |
| Repository Pattern 준수율 | 20% | 100% | 400%↑ |
| DI 사용 비율 | 10% | 80% | 700%↑ |

**유지보수성**:
| 지표 | Before | After | 개선율 |
|------|--------|-------|--------|
| 버그 수정 시간 | 기준 | -40% | 40%↓ |
| 신규 기능 개발 시간 | 기준 | -30% | 30%↓ |
| 온보딩 시간 | 2주 | 1주 | 50%↓ |

---

### 정성적 개선 목표

**SOLID 원칙 준수**:
- ✅ **SRP** (Single Responsibility): 각 클래스가 하나의 책임
- ✅ **OCP** (Open/Closed): Strategy Pattern으로 확장 가능
- ✅ **LSP** (Liskov Substitution): Interface 기반 설계
- ✅ **ISP** (Interface Segregation): 작은 인터페이스
- ✅ **DIP** (Dependency Inversion): DI Container 활용

**클린 코드 원칙**:
- ✅ 명확한 이름 (Naming Convention)
- ✅ 작은 함수 (30줄 이하)
- ✅ 적은 매개변수 (3개 이하)
- ✅ 단일 추상화 레벨
- ✅ 중복 제거 (DRY)

**아키텍처 패턴**:
- ✅ Layered Architecture (API → Service → Repository)
- ✅ Repository Pattern
- ✅ Strategy Pattern
- ✅ Factory Pattern
- ✅ Dependency Injection

---

## 🚀 다음 단계

### 즉시 시작 가능

**Step 1: Phase 1.1 시작**
```bash
# 브랜치 생성
git checkout -b refactor/phase-1.1-portfolio-service-split

# 디렉토리 생성
mkdir -p app/services/portfolio

# 첫 번째 파일 생성
touch app/services/portfolio/__init__.py
touch app/services/portfolio/portfolio_dca_manager.py
```

**Step 2: 첫 번째 클래스 추출**
- `PortfolioDcaManager` 추출
- 기존 static method 복사
- 단위 테스트 작성

**Step 3: 검증 및 커밋**
```bash
# 테스트 실행
pytest tests/unit/test_portfolio_dca_manager.py

# 커밋
git add .
git commit -m "refactor: Extract PortfolioDcaManager from PortfolioService"
```

---

### 권장 진행 순서

1. **Phase 1.1** (1주) - portfolio_service.py 분할
2. **Phase 1.3** (1주) - Repository Pattern 강화
3. **Phase 1.2** (3일) - yfinance_db.py 분할
4. **Phase 2.1** (1주) - Indicator Strategy Pattern
5. **Phase 2.2** (3일) - Naming Convention
6. **Phase 2.3** (1주) - Validation 통합
7. **Phase 3** (평가 후 결정)

---

## 📚 참고 문서

### 내부 문서
- [CLAUDE.md](../../CLAUDE.md) - 백엔드 아키텍처 개요
- [백테스트 로직 아키텍처](../architecture/backtest_logic.md)
- [Race Condition 문제](../troubleshooting/race_condition.md)

### 외부 자료
- [Clean Code (Robert C. Martin)](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Refactoring (Martin Fowler)](https://refactoring.com/)
- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-11-16 | 1.0.2 | **Phase 1.3 완료**: StockRepository 생성, 5개 서비스 마이그레이션, 모든 직접 yfinance_db import 제거 |
| 2025-11-16 | 1.0.1 | Phase 1.2 완료: DatabaseConfig, PoolConfig, DatabaseConnectionManager 생성 |
| 2025-11-16 | 1.0.0 | 초안 작성 |
