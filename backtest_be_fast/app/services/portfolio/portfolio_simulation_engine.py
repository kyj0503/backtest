"""포트폴리오 시뮬레이션 엔진 (Engine)

이 모듈은 '작업자' 역할로서 실제 날짜별 시뮬레이션 루프를 수행합니다.
매일의 시장 데이터(가격, 환율)를 처리하고 DCA 매수, 리밸런싱, 상장폐지 등의 핵심 로직을 실행합니다.
"""

import asyncio
import logging
from typing import Dict, Set, Tuple
from datetime import datetime, date
import pandas as pd

from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.rebalance_helper import RebalanceHelper, get_weekday_occurrence
from app.utils.currency_converter import currency_converter
from app.constants.data_loading import TradingThresholds
from app.domain.portfolio_domain import DcaStrategyInfo, PortfolioState
from app.services.portfolio.portfolio_metrics import PortfolioMetrics

logger = logging.getLogger(__name__)


class PortfolioSimulationEngine:
    """
    포트폴리오 시뮬레이션 엔진 클래스 (Worker/Engine Role)

    [역할 정의]
    이 클래스는 '작업자'로서 **실제 날짜별 시뮬레이션(루프)**을 수행합니다.
    Manager가 준비해준 데이터를 바탕으로 매일의 상태 변화를 계산합니다.

    주요 책임:
    1. Daily Loop: 매일의 시장 변화(가격 변동)를 반영.
    2. Core Logic: DCA 매수, 리밸런싱, 상장폐지 처리 등 핵심 계산 로직 수행.
    3. State Management: 포트폴리오의 일별 평가액, 보유 주식 수 등 상태 갱신.
    """

    def __init__(
        self,
        dca_manager: PortfolioDcaManager = None,
        rebalancer: PortfolioRebalancer = None
    ):
        """
        포트폴리오 시뮬레이션 엔진 초기화

        Args:
            dca_manager: DCA 관리 매니저
            rebalancer: 리밸런싱 리밸런서
        """
        self.dca_manager = dca_manager or PortfolioDcaManager()
        self.rebalancer = rebalancer or PortfolioRebalancer()
        self.logger = logging.getLogger(__name__)

    def initialize_portfolio_state(
        self,
        stock_amounts: Dict[str, float],
        cash_amount: float,
        amounts: Dict[str, float],
        dca_info: Dict[str, DcaStrategyInfo]
    ) -> PortfolioState:
        """
        포트폴리오 시뮬레이션을 위한 모든 추적 변수를 초기화합니다.

        Args:
            stock_amounts: 주식 종목별 투자 금액
            cash_amount: 총 현금 금액
            amounts: 전체 자산 금액 (주식 + 현금)
            dca_info: 분할 매수 정보

        Returns:
            초기화된 PortfolioState 객체
        """
        return PortfolioState(
            shares={key: 0.0 for key in stock_amounts.keys()},
            available_cash=cash_amount,
            cash_holdings={k: v for k, v in amounts.items() if dca_info[k].asset_type == 'cash'},
            delisted_stocks=set(),
            pending_initial_keys=set(stock_amounts.keys())
        )

    def detect_and_update_delisting(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        tradeable_today: Set[str],
        dca_info: Dict[str, DcaStrategyInfo],
        delisted_stocks: set,
        last_valid_prices: Dict[str, float],
        last_price_date: Dict[str, date]
    ) -> None:
        """
        상장폐지 종목을 감지하고 상태를 업데이트합니다.

        **역할**:
        - 30일 이상 RAW 가격 데이터가 없는 종목을 상장폐지로 판단
        - 마지막 유효 가격과 날짜를 추적
        - 재상장 케이스 처리

        **[P2-14] current_prices가 아닌 tradeable_today로 판단하는 이유**:
        current_prices는 _pre_calculate_prices가 만든 ffill 시리즈에서 유래한다.
        ffill은 결측치를 이전 값으로 무한정 채우므로, 종목이 실제로 사라진
        뒤에도 current_prices에는 (다른 종목이 date_range를 계속 늘리는 한)
        영원히 값이 남는다. 그 결과 "현재 가격이 없을 때"로 분기하는 예전
        로직은 종목이 사라진 이후로는 절대 실행되지 않아, last_price_date가
        멈추지 않고 상장폐지가 영영 감지되지 않았다. tradeable_today는
        reindex/ffill 이전의 RAW 인덱스에서 직접 파생되므로 이 문제가 없다.

        Args:
            current_date: 현재 시뮬레이션 날짜
            stock_amounts: 종목별 투자 금액
            current_prices: 종목별 현재 가격 (MODIFIED, 밸류에이션용 ffill 값)
            tradeable_today: [P2-14] 오늘 RAW 데이터로 실제 관측된 종목 집합
            dca_info: 종목 정보
            delisted_stocks: 상장폐지 종목 집합 (MODIFIED)
            last_valid_prices: 마지막 유효 가격 (MODIFIED)
            last_price_date: 마지막으로 RAW 관측된 날짜 (MODIFIED)
        """
        # 상장폐지 감지: RAW 데이터가 30일 이상 없으면 상장폐지로 판단
        for unique_key in stock_amounts.keys():
            if unique_key in tradeable_today:
                # 오늘 실제로 관측됐으면 마지막 유효 가격/날짜 갱신
                if unique_key in current_prices:
                    last_valid_prices[unique_key] = current_prices[unique_key]
                last_price_date[unique_key] = current_date.date()
                if unique_key in delisted_stocks:
                    # 상장 복원? (재상장 케이스)
                    self.logger.info(f"{unique_key} 가격 데이터 재등장 (재상장?), 상장폐지 상태 해제")
                    delisted_stocks.remove(unique_key)
            else:
                # 오늘 관측되지 않았을 때 (current_prices는 ffill로 여전히
                # 값을 갖고 있을 수 있으므로 여기서 참조하지 않는다)
                if unique_key in last_price_date:
                    days_without_price = (current_date.date() - last_price_date[unique_key]).days
                    if days_without_price >= TradingThresholds.DELISTING_THRESHOLD_DAYS and unique_key not in delisted_stocks:
                        # 상장폐지로 판단
                        symbol = dca_info[unique_key].symbol
                        self.logger.warning(
                            f"{symbol} ({unique_key}) 상장폐지 감지: "
                            f"마지막 RAW 관측 날짜 {last_price_date[unique_key]}, "
                            f"{days_without_price}일간 원본 데이터 없음. "
                            f"마지막 유효 가격 ${last_valid_prices.get(unique_key, 0):.2f} 유지"
                        )
                        delisted_stocks.add(unique_key)

        # 상장폐지된 종목의 가격을 마지막 유효 가격으로 유지 (일반적으로는
        # aligned_prices의 ffill이 이미 이 값을 제공하므로 아래는 방어적
        # fallback -- 예: 종목이 portfolio_data에 아예 없어 aligned_prices에
        # 항목 자체가 없는 경우).
        for unique_key in delisted_stocks:
            if unique_key in last_valid_prices and unique_key not in current_prices:
                current_prices[unique_key] = last_valid_prices[unique_key]

    def _pre_calculate_prices(
        self,
        date_range: pd.DatetimeIndex,
        stock_amounts: Dict[str, float],
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, DcaStrategyInfo],
        ticker_currencies: Dict[str, str],
        exchange_rates_by_currency: Dict[str, Dict[date, float]]
    ) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
        """
        [성능 최적화] 시뮬레이션 기간 동안의 모든 가격 데이터를 미리 정렬(Pre-align) 및 계산합니다.
        
        기존 로직(매일 슬라이싱)의 O(N^2) 복잡도를 O(N)으로 줄이기 위해 사용됩니다.
        - 각 종목의 데이터를 date_range에 맞춰 Reindex
        - Forward Fill로 결측치(휴장일 등) 채움
        - 환율 변환 미리 적용 (가능한 경우)

        Returns:
            aligned_prices: {ticker: Series(adjusted_price, index=date_range)}
            aligned_exchange_rates: {currency: Series(rate, index=date_range)}
        """
        aligned_prices = {}
        aligned_exchange_rates = {}

        # 1. 환율 데이터 정렬
        # (통화별로 미리 Series 생성)
        for currency, rates_map in exchange_rates_by_currency.items():
            if not rates_map:
                continue
            # date -> datetime64 변환을 위해 DataFrame/Series 생성
            rates_series = pd.Series(rates_map)
            rates_series.index = pd.to_datetime(rates_series.index)
            
            # Reindex & FFill
            # [Copilot Suggestion] ffill만 하면 시뮬레이션 시작일보다 환율 데이터가 늦게 시작될 경우 앞부분이 NaN이 됨.
            # bfill을 추가하여 앞부분 결측치도 보완 (최초 환율로 메꿈)
            aligned_rate = rates_series.reindex(date_range).ffill().bfill()
            aligned_exchange_rates[currency] = aligned_rate

        # 2. 주가 데이터 정렬 & 환율 적용
        for unique_key in stock_amounts.keys():
            symbol = dca_info[unique_key].symbol
            if symbol not in portfolio_data:
                continue

            df = portfolio_data[symbol]
            # 인덱스가 이미 datetime이어야 함
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Close 가격만 추출 및 정렬
            price_series = df['Close'].reindex(date_range).ffill()

            # 환율 변환
            currency = ticker_currencies.get(unique_key, 'USD')
            if currency != 'USD' and currency in aligned_exchange_rates:
                # 벡터 연산으로 전체 기간 환율 적용
                # [Copilot Suggestion] 벡터 연산 (환율 적용) - apply 제거 및 Vectorization 적용
                exchange_rates = aligned_exchange_rates[currency]
                
                # 주요 통화(EUR, GBP 등)는 직접 곱하기, 그 외(KRW, JPY 등)는 나누기 역수
                # CurrencyConverter.get_conversion_multiplier 로직을 벡터화
                if currency in ['EUR', 'GBP', 'AUD', 'CAD', 'CHF']:
                     # Direct multiplication
                     price_series = price_series * exchange_rates
                else:
                     # Inverse (1 / rate)
                     # 0 또는 NaN인 경우 1.0으로 처리 (Division by Zero 방지)
                     valid_mask = (exchange_rates > 0) & (pd.notnull(exchange_rates))
                     multipliers = pd.Series(1.0, index=exchange_rates.index)
                     multipliers[valid_mask] = 1.0 / exchange_rates[valid_mask]
                     
                     price_series = price_series * multipliers
            elif currency != 'USD':
                # [P2-02] 환율 데이터가 없다고 원본(비USD) 가격을 그대로 흘려보내면
                # 안 된다 -- 이후 시뮬레이션이 이 가격을 USD 현금과 그대로 합산해,
                # 예컨대 KRW 7만원대 가격이 $70,000짜리 자산으로 둔갑한 채 "성공"으로
                # 보고되는 조용한 오염이 발생한다 (기존에는 경고 로그만 남기고 계속
                # 진행했음). 지원하지 않는 통화이거나 환율 데이터 로딩이 실패한
                # 경우이므로 명시적으로 실패를 알린다.
                raise ValueError(
                    f"{symbol} ({unique_key}) 통화 '{currency}'의 환율 데이터가 없어 "
                    f"USD로 변환할 수 없습니다 (지원하지 않는 통화이거나 환율 데이터 "
                    f"로딩 실패). 변환되지 않은 원본 가격으로 백테스트를 진행할 수 없습니다."
                )
            
            aligned_prices[unique_key] = price_series

        return aligned_prices, aligned_exchange_rates

    def _get_daily_prices_from_aligned(
        self,
        current_date: pd.Timestamp,
        aligned_prices: Dict[str, pd.Series],
        aligned_exchange_rates: Dict[str, pd.Series],
        ticker_currencies: Dict[str, str],
        last_valid_exchange_rates: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        [성능 최적화] 미리 계산된 데이터에서 O(1)로 당일 가격 조회
        """
        current_prices = {}
        
        # 1. 환율 캐시 업데이트
        for currency, rates_series in aligned_exchange_rates.items():
            try:
                rate = rates_series.at[current_date]
                if pd.notnull(rate):
                    last_valid_exchange_rates[currency] = rate
            except KeyError:
                pass # 해당 통화의 환율 데이터가 없는 날짜는 캐시 갱신 없이 진행

        # 2. 가격 조회
        for unique_key, price_series in aligned_prices.items():
            try:
                price = price_series.at[current_date]
                # NaN 체크 (해당 날짜 데이터 없음 or 상장폐지 등)
                if pd.notnull(price):
                    current_prices[unique_key] = float(price)
            except KeyError:
                pass # 배열에 해당 날짜 데이터가 없으면 스킵 (상장폐지, 휴장일 등)
                
        return current_prices, last_valid_exchange_rates

    def _pre_calculate_tradeable_mask(
        self,
        date_range: pd.DatetimeIndex,
        stock_amounts: Dict[str, float],
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, DcaStrategyInfo]
    ) -> Dict[str, pd.Series]:
        """
        [P2-14] 종목별로 "해당 날짜에 실제로 RAW 데이터가 존재했는가"를 나타내는
        불리언 마스크를 date_range에 맞춰 미리 계산합니다.

        `_pre_calculate_prices`가 만드는 aligned_prices는 밸류에이션을 위해
        ffill로 결측치를 채운 시리즈이므로, 그 자체로는 "그 날짜에 실제로 거래가
        가능했는가"를 답할 수 없다 (ffill은 무한정 이전 값을 반복하기 때문에,
        상장폐지된 종목도 영원히 값을 갖는 것처럼 보인다). 이 메서드는 reindex
        직전의 RAW 인덱스만을 근거로 마스크를 만들어, 거래 실행(초기 매수/DCA
        정기 매수/리밸런싱)과 상장폐지 감지가 밸류에이션과 별개로 "실제로 관측된
        날"만 참조하도록 한다.

        `_pre_calculate_prices`와 정확히 같은 (date_range, stock_amounts,
        portfolio_data, dca_info) 조합에 대해 계산되므로, 함께 사용해도 두
        딕셔너리의 key 집합은 항상 일치한다 (같은 이유로 심볼이 없으면 둘 다
        해당 unique_key를 건너뛴다).

        Returns:
            {unique_key: Series(bool, index=date_range)} -- True인 날짜만 그
            종목의 원본 Close 데이터가 실제로 존재했던(관측된) 날이다.
        """
        aligned_tradeable: Dict[str, pd.Series] = {}

        for unique_key in stock_amounts.keys():
            symbol = dca_info[unique_key].symbol
            if symbol not in portfolio_data:
                continue

            df = portfolio_data[symbol]
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            observed = df['Close'].notna()
            aligned_tradeable[unique_key] = observed.reindex(date_range, fill_value=False)

        return aligned_tradeable

    def _get_daily_tradeable_keys(
        self,
        current_date: pd.Timestamp,
        aligned_tradeable: Dict[str, pd.Series]
    ) -> Set[str]:
        """
        [P2-14] 미리 계산된 tradeable 마스크에서 O(1)로 당일 관측 여부를 조회합니다.

        Returns:
            오늘 RAW 데이터로 실제 관측된 unique_key 집합.
        """
        tradeable_today: Set[str] = set()
        for unique_key, mask_series in aligned_tradeable.items():
            try:
                if bool(mask_series.at[current_date]):
                    tradeable_today.add(unique_key)
            except KeyError:
                pass  # 마스크에 해당 날짜가 없으면 관측되지 않은 것으로 취급
        return tradeable_today

    async def execute_simulation(
        self,
        date_range: pd.DatetimeIndex,
        start_date_obj: datetime,
        end_date_obj: datetime,
        stock_amounts: Dict[str, float],
        amounts: Dict[str, float],
        cash_amount: float,
        total_amount: float,
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, DcaStrategyInfo],
        ticker_currencies: Dict[str, str],
        exchange_rates_by_currency: Dict[str, Dict[date, float]],
        rebalance_frequency: str,
        commission: float
    ) -> pd.DataFrame:
        """
        전체 시뮬레이션 루프를 실행합니다.

        Args:
            date_range: 시뮬레이션 날짜 범위
            start_date_obj: 시작 날짜 객체
            end_date_obj: 종료 날짜 객체
            stock_amounts: 주식 종목별 투자 금액
            amounts: 전체 자산 금액
            cash_amount: 초기 현금
            total_amount: 총 투자 금액
            portfolio_data: 포트폴리오 데이터
            dca_info: DCA 정보 (DcaStrategyInfo 모델)
            ticker_currencies: 티커별 통화
            exchange_rates_by_currency: 환율 데이터
            rebalance_frequency: 리밸런싱 주기
            commission: 수수료율

        Returns:
            시뮬레이션 결과 DataFrame

        Note:
            [P2-01] 이 메서드 자체는 순수 CPU-bound 동기 작업(최대 10년 x N종목의
            pandas/pydantic 연산)이며 내부에 await가 없다. async def인데 await가
            전혀 없으면 실행되는 동안 이벤트 루프 전체를 독점해 다른 요청 처리가
            멈춘다. 그래서 실제 작업은 _execute_simulation_sync에 그대로 두고,
            여기서는 asyncio.to_thread로 워커 스레드에 위임만 한다 (공개 시그니처는
            그대로 유지되므로 호출자는 변경할 필요가 없다).
        """
        return await asyncio.to_thread(
            self._execute_simulation_sync,
            date_range,
            start_date_obj,
            end_date_obj,
            stock_amounts,
            amounts,
            cash_amount,
            total_amount,
            portfolio_data,
            dca_info,
            ticker_currencies,
            exchange_rates_by_currency,
            rebalance_frequency,
            commission,
        )

    def _execute_simulation_sync(
        self,
        date_range: pd.DatetimeIndex,
        start_date_obj: datetime,
        end_date_obj: datetime,
        stock_amounts: Dict[str, float],
        amounts: Dict[str, float],
        cash_amount: float,
        total_amount: float,
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, DcaStrategyInfo],
        ticker_currencies: Dict[str, str],
        exchange_rates_by_currency: Dict[str, Dict[date, float]],
        rebalance_frequency: str,
        commission: float
    ) -> pd.DataFrame:
        """
        execute_simulation의 실제 동기 구현체.

        [P2-01] execute_simulation(async 공개 API)이 asyncio.to_thread를 통해
        워커 스레드에서 이 메서드를 실행한다. 순수 동기 함수이므로 여기서는
        이벤트 루프가 필요한 어떤 작업(await 등)도 수행해서는 안 된다.
        """
        # 1. 상태 초기화
        state = self.initialize_portfolio_state(
            stock_amounts=stock_amounts,
            cash_amount=cash_amount,
            amounts=amounts,
            dca_info=dca_info
        )

        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)

        # [성능 최적화] 데이터 미리 준비 (Vectorization)
        aligned_prices, aligned_exchange_rates = self._pre_calculate_prices(
            date_range, stock_amounts, portfolio_data, dca_info, ticker_currencies, exchange_rates_by_currency
        )
        # [P2-14] 밸류에이션용 ffill 가격(aligned_prices)과는 별개로, 거래
        # 실행/상장폐지 감지에 쓸 "당일 RAW 관측 여부" 마스크를 미리 계산한다.
        aligned_tradeable = self._pre_calculate_tradeable_mask(
            date_range, stock_amounts, portfolio_data, dca_info
        )
        last_valid_exchange_rates = {} # 루프 내 캐싱용

        # 2. 메인 루프 실행
        for current_date in date_range:
            daily_cash_inflow = 0.0  # 당일 추가 투자금 (DCA)
            if current_date.date() < start_date_obj.date():
                continue
            if current_date.date() > end_date_obj.date():
                break

            # 2.1 가격 조회 (최적화 버전)
            current_prices, last_valid_exchange_rates = self._get_daily_prices_from_aligned(
                current_date=current_date,
                aligned_prices=aligned_prices,
                aligned_exchange_rates=aligned_exchange_rates,
                ticker_currencies=ticker_currencies,
                last_valid_exchange_rates=last_valid_exchange_rates
            )
            # [P2-14] 오늘 RAW 데이터로 실제 관측된 종목 집합. current_prices와
            # 달리 ffill로 채워지지 않으므로, 거래 실행 여부와 상장폐지 감지의
            # 근거로 쓴다 (밸류에이션은 계속 current_prices/ffill을 사용한다).
            tradeable_today = self._get_daily_tradeable_keys(current_date, aligned_tradeable)

            # 2.2 상장폐지 감지
            self.detect_and_update_delisting(
                current_date=current_date,
                stock_amounts=stock_amounts,
                current_prices=current_prices,
                tradeable_today=tradeable_today,
                dca_info=dca_info,
                delisted_stocks=state.delisted_stocks,
                last_valid_prices=state.last_valid_prices,
                last_price_date=state.last_price_date
            )

            # 2.3 리밸런싱 로깅 (상장폐지 관련)
            if state.original_rebalance_nth is None and rebalance_frequency != 'none':
                state.original_rebalance_nth = get_weekday_occurrence(start_date_obj)
                self.logger.debug(f"리밸런싱 원본 Nth 값 설정 = {state.original_rebalance_nth}번째 {['월','화','수','목','금','토','일'][start_date_obj.weekday()]}요일")

            should_rebalance = RebalanceHelper.is_rebalance_date(
                current_date, state.prev_date, rebalance_frequency, start_date_obj, state.last_rebalance_date, state.original_rebalance_nth
            )

            if state.delisted_stocks and (should_rebalance or current_date.weekday() == 0):
                delisted_symbols = [dca_info[key].symbol for key in state.delisted_stocks if key in dca_info]
                self.logger.info(
                    f"{current_date.date()}: 상장폐지 종목 {len(state.delisted_stocks)}개 추적 중 "
                    f"[{', '.join(delisted_symbols)}]"
                )

            # 2.4 DCA 실행 (초기 매수 또는 정기 매수)
            #
            # 초기 매수는 "첫날 한 번"이 아니라 "각 종목이 처음 가격을 갖는 날"에
            # 이뤄져야 한다. 혼합 시장 포트폴리오에서는 시작일에 한쪽 시장이
            # 휴장이라 가격이 없을 수 있는데, 과거에는 그 종목을 건너뛴 뒤 다시
            # 시도하지 않아 포지션이 영영 열리지 않고 투자금만 분모에 남았다.
            if state.pending_initial_keys:
                trades, cash_inflow = self.dca_manager.execute_initial_purchases(
                    current_date=current_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=state.shares,
                    commission=commission,
                    pending_keys=state.pending_initial_keys,
                    tradeable_keys=tradeable_today
                )
                state.total_trades += trades
                daily_cash_inflow += cash_inflow

            if state.is_first_day:
                state.is_first_day = False
                state.prev_date = current_date

            if state.prev_date is not None and state.prev_date != current_date:
                trades, cash_inflow = self.dca_manager.execute_periodic_purchases(
                    current_date=current_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=state.shares,
                    commission=commission,
                    start_date_obj=start_date_obj,
                    tradeable_keys=tradeable_today
                )
                state.total_trades += trades
                daily_cash_inflow += cash_inflow


            # 2.5 리밸런싱 실행
            if rebalance_frequency != 'none':
                if should_rebalance and len(target_weights) > 1:
                    last_rebal_str = state.last_rebalance_date.strftime('%Y-%m-%d') if state.last_rebalance_date else '없음'
                    self.logger.info(
                        f"{current_date.date()}: 리밸런싱 트리거됨 "
                        f"(주기: {rebalance_frequency}, 자산 수: {len(target_weights)}, "
                        f"마지막 리밸런싱: {last_rebal_str})"
                    )
                elif should_rebalance and len(target_weights) <= 1:
                    self.logger.debug(
                        f"{current_date.date()}: 리밸런싱 조건 충족하지만 자산 수 부족 (자산 수: {len(target_weights)})"
                    )

            if should_rebalance and len(target_weights) > 1:
                # [P2-14] 오늘 RAW로 관측되지 않은(하지만 상장폐지로 확정되지는
                # 않은) 종목은 이번 리밸런싱에서만 "일시적으로" 상장폐지 종목과
                # 동일하게 취급한다 -- 존재하지 않았던 오늘의 ffill 가격으로
                # 거래를 체결시키지 않기 위해서다. state.delisted_stocks 자체는
                # 건드리지 않고, 이번 호출에만 쓰는 지역 합집합을 만든다
                # (PortfolioRebalancer는 "보유 유지 + 재분배 풀에서 제외 +
                # 수수료 비례축소 제외"를 이미 delisted_stocks 파라미터만으로
                # 정확히 수행하므로, portfolio_rebalancer.py 자체를 변경할
                # 필요가 없다).
                non_tradeable_today_stocks = {
                    key for key in stock_amounts.keys()
                    if key not in state.delisted_stocks and key not in tradeable_today
                }
                rebalance_excluded_stocks = state.delisted_stocks | non_tradeable_today_stocks

                adjusted_target_weights = self.rebalancer.calculate_adjusted_weights(
                    target_weights=target_weights,
                    delisted_stocks=rebalance_excluded_stocks,
                    dca_info=dca_info
                )

                if rebalance_excluded_stocks:
                    for unique_key, adj_weight in adjusted_target_weights.items():
                        if unique_key not in rebalance_excluded_stocks:
                            original_weight = target_weights.get(unique_key, 0.0)
                            if original_weight != adj_weight:
                                symbol = dca_info[unique_key].symbol
                                self.logger.debug(
                                    f"  {symbol}: {original_weight:.2%} -> {adj_weight:.2%}"
                                )

                total_stock_value = sum(
                    state.shares[key] * current_prices.get(key, 0)
                    for key in state.shares.keys()
                    if key in current_prices
                )

                rebalance_result = self.rebalancer.execute_rebalancing_trades(
                    current_date=current_date,
                    adjusted_target_weights=adjusted_target_weights,
                    shares=state.shares,
                    current_prices=current_prices,
                    available_cash=state.available_cash,
                    cash_holdings=state.cash_holdings,
                    commission=commission,
                    total_stock_value=total_stock_value,
                    dca_info=dca_info,
                    delisted_stocks=rebalance_excluded_stocks
                )

                state.shares = rebalance_result['updated_shares']
                state.cash_holdings = rebalance_result['updated_cash_holdings']
                state.available_cash = rebalance_result['updated_available_cash']
                trades_in_rebalance = rebalance_result['trades_executed']

                if rebalance_result['rebalance_trades']:
                    state.rebalance_history.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'trades': rebalance_result['rebalance_trades'],
                        'weights_before': rebalance_result['weights_before'],
                        'weights_after': rebalance_result['weights_after'],
                        'commission_cost': rebalance_result['commission_cost']
                    })

                state.last_rebalance_date = current_date.date()
                state.total_trades += trades_in_rebalance

            # 2.6 메트릭 계산
            metrics_calculator = PortfolioMetrics()

            normalized_value, daily_return, current_weights = metrics_calculator.calculate_daily_metrics_and_history(
                current_date=current_date,
                shares=state.shares,
                available_cash=state.available_cash,
                current_prices=current_prices,
                cash_holdings=state.cash_holdings,
                prev_portfolio_value=state.prev_portfolio_value,
                daily_cash_inflow=daily_cash_inflow,
                total_amount=total_amount,
                dca_info=dca_info
            )

            state.portfolio_values.append(normalized_value)
            state.daily_returns.append(daily_return)
            state.weight_history.append(current_weights)

            state.prev_portfolio_value = normalized_value * total_amount
            state.prev_date = current_date

        # 3. 결과 정리
        valid_dates = [d for d in date_range if start_date_obj.date() <= d.date() <= end_date_obj.date()]

        if len(state.portfolio_values) != len(valid_dates):
            self.logger.warning(f"포트폴리오 값 길이 불일치: portfolio_values={len(state.portfolio_values)}, valid_dates={len(valid_dates)}")
            # 길이를 맞추거나 에러를 던지는데, 여기선 에러
            # (기존 로직 유지)

        result = pd.DataFrame({
            'Date': valid_dates,
            'Portfolio_Value': state.portfolio_values,
            'Daily_Return': state.daily_returns,
            'Cumulative_Return': [(v - 1) * 100 for v in state.portfolio_values]
        })
        result.set_index('Date', inplace=True)

        result.attrs['total_trades'] = state.total_trades
        result.attrs['rebalance_history'] = state.rebalance_history
        result.attrs['weight_history'] = state.weight_history

        return result
