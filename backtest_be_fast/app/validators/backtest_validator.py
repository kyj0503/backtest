"""
백테스트 요청 검증 로직

**역할**:
- 백테스트 요청 전체 검증
- DateValidator, SymbolValidator 조합
- 전략 파라미터 검증

**주요 기능**:
1. validate_request(): 백테스트 요청 전체 검증
2. validate_initial_cash(): 초기 자본 검증
3. validate_commission(): 수수료 검증
4. validate_strategy_params(): 전략 파라미터 검증

**검증 항목**:
- 날짜 범위 (DateValidator)
- 티커 심볼 (SymbolValidator)
- 초기 자본 (양수)
- 수수료 (0~10%)
- 전략 파라미터 (전략별 규칙)

**사용 예**:
```python
from app.validators import BacktestValidator
from app.schemas.requests import BacktestRequest

validator = BacktestValidator(data_fetcher, strategy_service)
validator.validate_request(request)
```
"""
import logging
from typing import Optional, Dict, Any
from datetime import date

from .date_validator import DateValidator
from .symbol_validator import SymbolValidator

logger = logging.getLogger(__name__)


class BacktestValidator:
    """백테스트 요청 검증 전담 클래스"""

    def __init__(self, data_fetcher=None, strategy_service=None):
        """
        Args:
            data_fetcher: 티커 확인용 DataFetcher (선택)
            strategy_service: 전략 검증용 StrategyService (선택)
        """
        self.date_validator = DateValidator()
        self.symbol_validator = SymbolValidator(data_fetcher)
        self.strategy_service = strategy_service

    def validate_initial_cash(self, initial_cash: float) -> None:
        """
        초기 자본 검증

        Args:
            initial_cash: 초기 자본

        Raises:
            ValueError: 초기 자본이 유효하지 않은 경우
        """
        if not isinstance(initial_cash, (int, float)):
            raise ValueError(f"초기 자본은 숫자여야 합니다: {type(initial_cash)}")

        if initial_cash <= 0:
            raise ValueError(f"초기 자본은 0보다 커야 합니다: {initial_cash}")

        if initial_cash > 1_000_000_000:  # 10억 제한 (합리적인 상한)
            logger.warning(f"초기 자본이 매우 큽니다: {initial_cash:,.0f}")

        logger.debug(f"초기 자본 검증 통과: {initial_cash:,.2f}")

    def validate_commission(self, commission: float) -> None:
        """
        수수료 검증

        Args:
            commission: 수수료 (0.0 ~ 1.0)

        Raises:
            ValueError: 수수료가 유효하지 않은 경우
        """
        if not isinstance(commission, (int, float)):
            raise ValueError(f"수수료는 숫자여야 합니다: {type(commission)}")

        if commission < 0:
            raise ValueError(f"수수료는 0 이상이어야 합니다: {commission}")

        if commission >= 0.1:  # 10% 이상은 비정상
            raise ValueError(
                f"수수료가 너무 높습니다: {commission*100:.2f}% (최대 10%)"
            )

        logger.debug(f"수수료 검증 통과: {commission*100:.3f}%")

    def validate_strategy_params(
        self,
        strategy_name: str,
        params: Optional[Dict[str, Any]]
    ) -> None:
        """
        전략 파라미터 검증

        Args:
            strategy_name: 전략 이름
            params: 전략 파라미터

        Raises:
            ValueError: 전략이나 파라미터가 유효하지 않은 경우
        """
        if not self.strategy_service:
            logger.warning("StrategyService가 없어 전략 파라미터를 검증할 수 없습니다")
            return

        # 전략 존재 확인
        available_strategies = self.strategy_service.get_all_strategies()
        if strategy_name not in available_strategies:
            raise ValueError(
                f"지원하지 않는 전략입니다: {strategy_name}. "
                f"사용 가능한 전략: {', '.join(available_strategies.keys())}"
            )

        # 파라미터 검증
        if params:
            try:
                self.strategy_service.validate_strategy_params(strategy_name, params)
                logger.debug(f"전략 파라미터 검증 통과: {strategy_name}")
            except ValueError as e:
                raise ValueError(f"전략 파라미터 오류 ({strategy_name}): {str(e)}")

    def validate_request(self, request) -> None:
        """
        백테스트 요청 전체 검증

        Args:
            request: BacktestRequest 객체

        Raises:
            ValueError: 요청이 유효하지 않은 경우

        Examples:
            >>> from app.schemas.requests import BacktestRequest
            >>> validator = BacktestValidator()
            >>> validator.validate_request(request)
        """
        try:
            # 1. 티커 검증 및 정규화
            ticker = self.symbol_validator.validate_and_normalize(request.ticker)
            logger.debug(f"티커 검증 완료: {ticker}")

            # 2. 날짜 검증
            # request.start_date와 end_date가 문자열일 수 있으므로 처리
            start_date = request.start_date
            end_date = request.end_date

            if isinstance(start_date, str):
                from datetime import datetime
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            if isinstance(end_date, str):
                from datetime import datetime
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            self.date_validator.validate_date_range(start_date, end_date, min_days=30)
            self.date_validator.validate_not_future(end_date)
            logger.debug(f"날짜 검증 완료: {start_date} ~ {end_date}")

            # 3. 초기 자본 검증
            self.validate_initial_cash(request.initial_cash)

            # 4. 수수료 검증
            self.validate_commission(request.commission)

            # 5. 전략 검증
            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            self.validate_strategy_params(strategy_name, request.strategy_params)

            logger.info(f"백테스트 요청 검증 완료: {ticker}, {start_date} ~ {end_date}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"백테스트 요청 검증 중 오류: {str(e)}")
            raise ValueError(f"요청 검증 실패: {str(e)}")
