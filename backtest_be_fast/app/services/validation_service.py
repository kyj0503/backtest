"""백테스트 검증 서비스

백테스트 요청 검증을 BacktestValidator에 위임합니다.
폴백 통계 생성 유틸리티를 제공합니다.
"""
import logging
import pandas as pd
from typing import Dict, Any

from app.schemas.requests import BacktestRequest
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.exceptions import ValidationError
from app.validators.backtest_validator import BacktestValidator


class ValidationService:
    """백테스트 요청 검증 서비스 (BacktestValidator로 위임)"""

    # 연환산 계수: 표준 거래일 기준(252일). 실제 backtesting._stats.compute_stats도
    # 동일한 연간 거래일 수를 사용해 일간 변동성을 연환산한다.
    _ANNUAL_TRADING_DAYS = 252

    def __init__(self, data_fetcher_instance=None, strategy_service_instance=None):
        self.data_fetcher = data_fetcher_instance or data_fetcher
        self.strategy_service = strategy_service_instance or strategy_service
        self.logger = logging.getLogger(__name__)

        self.backtest_validator = BacktestValidator(
            data_fetcher=self.data_fetcher,
            strategy_service=self.strategy_service
        )

    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 검증 (BacktestValidator로 위임)"""
        try:
            self.backtest_validator.validate_request(request)
            self.logger.info(f"백테스트 요청 검증 완료: {request.ticker}")

        except ValueError as ve:
            self.logger.error(f"백테스트 요청 검증 실패: {str(ve)}")
            raise ValidationError(str(ve))
        except Exception as e:
            self.logger.error(f"백테스트 요청 검증 중 오류: {str(e)}")
            raise ValidationError(f"요청 검증 실패: {str(e)}")

    def create_fallback_stats(self, data: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """폴백 통계 생성 (백테스트 실패 시 Buy & Hold 수익률 계산)

        주의(P3-21): 이 메서드가 반환하는 값은 백테스팅 엔진이 실제로 시뮬레이션한
        거래가 아니라 Buy & Hold 가정으로 계산한 참고용 수치다. 실제 거래가
        시뮬레이션되지 않았으므로 '# Trades'/'Win Rate [%]'처럼 거래 실행을
        전제로 하는 지표를 꾸며서 채우지 않고 정직하게 0으로 표시한다
        (이전에는 '# Trades': 1, 'Win Rate [%]': 100.0(또는 0.0)을 조작해
        반환했다). 변동성은 실제 backtesting.py 경로 및 응답 스키마와 단위를
        맞추기 위해 연환산(sqrt(252) 스케일링)한다 (이전에는 일간 표준편차를
        연환산 없이 그대로 반환했다).
        """
        try:
            if data.empty:
                return {
                    'Equity Final [$]': initial_cash,
                    'Return [%]': 0.0,
                    '# Trades': 0,
                    'Win Rate [%]': 0.0,
                    'Max. Drawdown [%]': 0.0,
                    'Sharpe Ratio': 0.0,
                    'Volatility [%]': 0.0
                }

            # Buy & Hold 수익률 계산 (실제 가격 데이터 기반 — 조작값 아님)
            initial_price = float(data['Close'].iloc[0])
            final_price = float(data['Close'].iloc[-1])
            buy_hold_return = ((final_price / initial_price) - 1) * 100
            final_equity = initial_cash * (final_price / initial_price)

            # 변동성 계산 (연환산)
            returns = data['Close'].pct_change().dropna()
            daily_volatility = returns.std() if len(returns) > 1 else 0.0
            annualized_volatility_pct = daily_volatility * (self._ANNUAL_TRADING_DAYS ** 0.5) * 100

            return {
                'Equity Final [$]': final_equity,
                'Return [%]': buy_hold_return,
                # 실제로 시뮬레이션된 거래는 없다 (Buy & Hold 가정치일 뿐) —
                # 거래가 일어난 것처럼 조작하지 않는다.
                '# Trades': 0,
                'Win Rate [%]': 0.0,
                'Max. Drawdown [%]': 0.0,
                'Sharpe Ratio': 0.0,
                'Volatility [%]': annualized_volatility_pct,
                'Buy & Hold Return [%]': buy_hold_return,  # 실제 Buy & Hold 수익률
            }

        except Exception as e:
            self.logger.error(f"폴백 통계 생성 실패: {str(e)}")
            return {
                'Equity Final [$]': initial_cash,
                'Return [%]': 0.0,
                '# Trades': 0,
                'Win Rate [%]': 0.0,
                'Max. Drawdown [%]': 0.0,
                'Sharpe Ratio': 0.0,
                'Volatility [%]': 0.0
            }


# 글로벌 인스턴스
validation_service = ValidationService()
