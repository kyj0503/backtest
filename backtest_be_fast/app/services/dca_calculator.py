"""분할 매수(DCA) 계산 서비스

Dollar Cost Averaging 투자의 총 주식 수량, 평균 단가, 수익률을 계산합니다.

[P2-13] 이 모듈은 표시(display)용으로 별도의 DCA 실행 모델을 재구현했었다.
실제 시뮬레이션(portfolio_dca_manager.PortfolioDcaManager)은 Nth-weekday
스케줄을 따르고 회당 투자금에서 수수료를 차감하는 반면, 이 모듈의 예전
구현은 "예정일 이후 첫 거래일에 매수, 수수료 무시"라는 다른 모델을 썼다. 두
모델은 같은 API 응답 안에서 종목별 표시값과 포트폴리오 합계가 서로 모순되는
결과를 냈다 (특히 예정일이 거래일이 아니거나 수수료가 0보다 클 때).

지금은 실제 시뮬레이션이 쓰는 바로 그 PortfolioDcaManager에 위임한다. 이
함수는 항상 "단일 종목"만 다루므로, 그 종목 자신의 RAW 인덱스를 date_range로
그대로 사용해 미니 시뮬레이션을 구동하면 다른 종목의 날짜가 섞여 들어올 일이
없다 -- 전체 포트폴리오 시뮬레이션에서 이 종목만 떼어낸 것과 수학적으로
동일한 결과를 낸다 (다른 종목은 이 종목이 관측되지 않은 날의 거래 여부에
영향을 주지 않으므로).
"""
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import pandas as pd
import logging
from app.schemas.schemas import FREQUENCY_MAP
from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager

logger = logging.getLogger(__name__)


class DcaCalculator:
    """분할 매수(DCA) 계산 유틸리티"""

    @staticmethod
    def calculate_dca_shares_and_return(
        df: pd.DataFrame,
        period_amount: float,
        dca_periods: int,
        start_date: str,
        frequency: str = 'monthly_1',
        commission: float = 0.0
    ) -> Tuple[float, float, float, List[Dict]]:
        """
        DCA 투자의 총 주식 수량과 평균 단가, 수익률, 매수 로그를 계산.

        [P2-13] PortfolioDcaManager(실제 시뮬레이션 엔진)에 위임하므로,
        Nth-weekday 스케줄/수수료 차감/결측일 이연 재시도가 실제 시뮬레이션과
        구조적으로 동일하다 (재구현으로 인한 괴리가 없다).

        Parameters
        ----------
        df : pd.DataFrame
            가격 데이터 (Close 컬럼 필수)
        period_amount : float
            회당 투자 금액
        dca_periods : int
            총 투자 횟수 (초회 포함)
        start_date : str
            시작 날짜 (YYYY-MM-DD 형식)
        frequency : str, optional
            투자 주기 (weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12, 기본값: monthly_1)
        commission : float, optional
            거래 수수료율 (0.002 = 0.2%, 기본값: 0.0).
            [주의] 현재 유일한 호출자인 portfolio_manager_service.py는 아직 이
            인자를 넘기지 않는다(하위 호환을 위해 기본값 0.0으로 둠). 실제
            요청의 commission을 반영하려면 그 호출부가 request.commission을
            넘기도록 바뀌어야 한다 (이 배치에서는 portfolio_manager_service.py를
            수정할 수 없어 후속 작업으로 남김).

        Returns
        -------
        tuple
            (총 주식 수량, 평균 단가, 수익률 %, 매수 로그 리스트)

        Examples
        --------
        >>> total_shares, avg_price, return_pct, log = DcaCalculator.calculate_dca_shares_and_return(
        ...     df=df,
        ...     period_amount=1000.0,
        ...     dca_periods=12,
        ...     start_date='2024-01-10',
        ...     frequency='monthly_1'
        ... )
        >>> print(f"Total shares: {total_shares}, Average price: {avg_price}")
        """
        if dca_periods <= 0 or df.empty:
            return 0, 0, 0, []

        # 주기 정보 가져오기 (알 수 없는 주기는 monthly_1로 대체 -- 이 정규화가
        # 없으면 PortfolioDcaManager가 잘못된 주기를 만나 정기 매수를 전부
        # 건너뛰게 된다).
        if not FREQUENCY_MAP.get(frequency):
            logger.warning(f"알 수 없는 DCA 주기: {frequency}, 기본값 monthly_1 사용")
            frequency = 'monthly_1'

        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')

        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.copy()
            df.index = pd.to_datetime(df.index)

        unique_key = '_DCA_DISPLAY_'
        dca_info: Dict[str, DcaStrategyInfo] = {
            unique_key: DcaStrategyInfo(
                symbol=unique_key, allocation=1.0, asset_type='stock',
                investment_type='dca', monthly_amount=period_amount,
                dca_frequency=frequency, dca_periods=dca_periods,
            )
        }
        stock_amounts = {unique_key: period_amount}
        shares = {unique_key: 0.0}
        pending_keys: Set[str] = {unique_key}

        manager = PortfolioDcaManager()
        total_invested = 0.0
        trade_log: List[Dict] = []
        prev_date: Optional[pd.Timestamp] = None

        for current_date in df.index:
            if current_date.date() < start_date_obj.date():
                continue

            price = df['Close'].at[current_date]
            # 이 종목 자신의 RAW 인덱스를 그대로 순회하므로, ffill 없이도
            # current_prices에 값이 있는 날 == 오늘 실제로 관측된 날이다.
            current_prices = {unique_key: float(price)} if pd.notna(price) else {}
            tradeable_keys = set(current_prices.keys())

            shares_before = shares[unique_key]

            if pending_keys:
                _, inflow = manager.execute_initial_purchases(
                    current_date=current_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=shares,
                    commission=commission,
                    pending_keys=pending_keys,
                    tradeable_keys=tradeable_keys,
                )
                total_invested += inflow

            if prev_date is not None and prev_date != current_date:
                _, inflow = manager.execute_periodic_purchases(
                    current_date=current_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=shares,
                    commission=commission,
                    start_date_obj=start_date_obj,
                    tradeable_keys=tradeable_keys,
                )
                total_invested += inflow

            shares_bought = shares[unique_key] - shares_before
            if shares_bought != 0.0:
                trade_log.append({
                    'EntryTime': current_date.isoformat(),
                    'EntryPrice': float(price),
                    'Size': float(shares_bought),
                    'Type': 'BUY',
                    'ExitTime': None,  # DCA는 매수만 있고 매도 없음
                    'ExitPrice': None,
                    'PnL': None,
                    'ReturnPct': None,
                    'Duration': None,
                })

            prev_date = current_date

        total_shares = shares[unique_key]

        if total_shares > 0:
            average_price = total_invested / total_shares
            end_price = df['Close'].iloc[-1]
            return_rate = (end_price / average_price - 1) * 100
            return total_shares, average_price, return_rate, trade_log

        return 0, 0, 0, []
