"""
포트폴리오 요청 검증 로직

**역할**:
- 포트폴리오 백테스트 요청 검증
- DateValidator, SymbolValidator 조합
- 포트폴리오 구성 비즈니스 규칙 검증

**주요 기능**:
1. validate_request(): 포트폴리오 요청 전체 검증
2. validate_portfolio_composition(): 포트폴리오 구성 검증
3. validate_weights(): 비중 합계 검증
4. validate_rebalance_frequency(): 리밸런싱 주기 검증

**검증 항목**:
- 날짜 범위 (DateValidator)
- 티커 심볼 (SymbolValidator)
- 포트폴리오 구성 (종목 수, 중복, 비중 합계)
- DCA 주기 유효성
- 리밸런싱 주기 유효성

**사용 예**:
```python
from app.validators import PortfolioValidator

validator = PortfolioValidator(data_fetcher)
validator.validate_request(request)
```
"""
import logging
from typing import List, Optional
from datetime import datetime

from .date_validator import DateValidator
from .symbol_validator import SymbolValidator

logger = logging.getLogger(__name__)


class PortfolioValidator:
    """포트폴리오 요청 검증 전담 클래스"""

    # 유효한 주기
    VALID_FREQUENCIES = [
        'weekly_1', 'weekly_2',
        'monthly_1', 'monthly_2', 'monthly_3', 'monthly_6', 'monthly_12',
        'none'
    ]

    def __init__(self, data_fetcher=None):
        """
        Args:
            data_fetcher: 티커 확인용 DataFetcher (선택)
        """
        self.date_validator = DateValidator()
        self.symbol_validator = SymbolValidator(data_fetcher)

    def validate_portfolio_composition(
        self,
        portfolio: List,
        min_items: int = 1,
        max_items: int = 10
    ) -> None:
        """
        포트폴리오 구성 검증

        Args:
            portfolio: 포트폴리오 종목 리스트
            min_items: 최소 종목 수
            max_items: 최대 종목 수

        Raises:
            ValueError: 포트폴리오 구성이 유효하지 않은 경우
        """
        if not portfolio:
            raise ValueError("포트폴리오는 최소 1개 종목을 포함해야 합니다")

        if len(portfolio) < min_items:
            raise ValueError(f"포트폴리오는 최소 {min_items}개 종목이 필요합니다")

        if len(portfolio) > max_items:
            raise ValueError(f"포트폴리오는 최대 {max_items}개 종목으로 제한됩니다")

        # 중복 종목 검증 (현금 제외)
        stock_symbols = [
            item.symbol.upper()
            for item in portfolio
            if getattr(item, 'asset_type', 'stock') != 'cash'
        ]

        if len(stock_symbols) != len(set(stock_symbols)):
            seen = set()
            duplicates = set()
            for symbol in stock_symbols:
                if symbol in seen:
                    duplicates.add(symbol)
                seen.add(symbol)
            raise ValueError(
                f"중복된 종목이 있습니다: {', '.join(sorted(duplicates))}. "
                f"같은 종목은 한 번만 추가할 수 있습니다"
            )

        logger.debug(f"포트폴리오 구성 검증 통과: {len(portfolio)}개 종목")

    def validate_weights(self, portfolio: List) -> None:
        """
        포트폴리오 비중 합계 검증

        Args:
            portfolio: 포트폴리오 종목 리스트

        Raises:
            ValueError: 비중 합계가 유효하지 않은 경우
        """
        # weight 기반인지 확인
        has_weight = any(getattr(item, 'weight', None) is not None for item in portfolio)

        if not has_weight:
            # amount 기반인 경우, 총액만 확인
            total_amount = sum(getattr(item, 'amount', 0) or 0 for item in portfolio)
            if total_amount <= 0:
                raise ValueError("총 투자 금액은 0보다 커야 합니다")
            logger.debug(f"총 투자 금액 검증 통과: {total_amount:,.2f}")
            return

        # weight 기반인 경우, 합계 검증
        total_weight = sum(getattr(item, 'weight', 0) or 0 for item in portfolio)

        # 95~105% 범위 허용 (반올림 오차 고려)
        if total_weight < 95 or total_weight > 105:
            raise ValueError(
                f"종목 비중 합계가 95-105% 범위를 벗어났습니다. "
                f"현재: {total_weight:.1f}%"
            )

        logger.debug(f"포트폴리오 비중 검증 통과: {total_weight:.1f}%")

    def validate_rebalance_frequency(self, frequency: str) -> None:
        """
        리밸런싱 주기 검증

        Args:
            frequency: 리밸런싱 주기

        Raises:
            ValueError: 주기가 유효하지 않은 경우
        """
        if frequency not in self.VALID_FREQUENCIES:
            raise ValueError(
                f"유효하지 않은 리밸런싱 주기: {frequency}. "
                f"사용 가능: {', '.join(self.VALID_FREQUENCIES)}"
            )

        logger.debug(f"리밸런싱 주기 검증 통과: {frequency}")

    def validate_dca_frequency(self, frequency: str) -> None:
        """
        DCA 주기 검증

        Args:
            frequency: DCA 주기

        Raises:
            ValueError: 주기가 유효하지 않은 경우
        """
        valid_dca_frequencies = [f for f in self.VALID_FREQUENCIES if f != 'none']

        if frequency not in valid_dca_frequencies:
            raise ValueError(
                f"유효하지 않은 DCA 주기: {frequency}. "
                f"사용 가능: {', '.join(valid_dca_frequencies)}"
            )

        logger.debug(f"DCA 주기 검증 통과: {frequency}")

    def validate_request(self, request) -> None:
        """
        포트폴리오 백테스트 요청 전체 검증

        Args:
            request: PortfolioBacktestRequest 객체

        Raises:
            ValueError: 요청이 유효하지 않은 경우
        """
        try:
            # 1. 날짜 검증
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()

            self.date_validator.validate_date_range(start_date, end_date, min_days=30)
            self.date_validator.validate_not_future(end_date)
            logger.debug(f"날짜 검증 완료: {start_date} ~ {end_date}")

            # 2. 포트폴리오 구성 검증
            self.validate_portfolio_composition(request.portfolio)

            # 3. 비중/금액 검증
            self.validate_weights(request.portfolio)

            # 4. 개별 종목 검증
            for item in request.portfolio:
                # 주식인 경우 티커 검증
                if getattr(item, 'asset_type', 'stock') == 'stock':
                    self.symbol_validator.validate_and_normalize(item.symbol)

                # DCA 주기 검증
                if getattr(item, 'investment_type', 'lump_sum') == 'dca':
                    dca_frequency = getattr(item, 'dca_frequency', 'monthly_1')
                    self.validate_dca_frequency(dca_frequency)

            # 5. 리밸런싱 주기 검증
            if hasattr(request, 'rebalance_frequency'):
                self.validate_rebalance_frequency(request.rebalance_frequency)

            # 6. 수수료 검증
            if hasattr(request, 'commission'):
                if request.commission < 0 or request.commission >= 0.1:
                    raise ValueError(
                        f"수수료가 유효하지 않습니다: {request.commission*100:.2f}% "
                        f"(0~10% 범위)"
                    )

            logger.info(
                f"포트폴리오 백테스트 요청 검증 완료: "
                f"{len(request.portfolio)}개 종목, {start_date} ~ {end_date}"
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"포트폴리오 요청 검증 중 오류: {str(e)}")
            raise ValueError(f"요청 검증 실패: {str(e)}")
