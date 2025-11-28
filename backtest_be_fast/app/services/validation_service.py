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
        """폴백 통계 생성 (백테스트 실패 시 Buy & Hold 수익률 계산)"""
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
            
            # Buy & Hold 수익률 계산
            initial_price = float(data['Close'].iloc[0])
            final_price = float(data['Close'].iloc[-1])
            buy_hold_return = ((final_price / initial_price) - 1) * 100
            final_equity = initial_cash * (final_price / initial_price)
            
            # 변동성 계산
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std() * 100 if len(returns) > 1 else 0.0
            
            return {
                'Equity Final [$]': final_equity,
                'Return [%]': buy_hold_return,
                '# Trades': 1,
                'Win Rate [%]': 100.0 if buy_hold_return > 0 else 0.0,
                'Max. Drawdown [%]': 0.0,
                'Sharpe Ratio': 0.0,
                'Volatility [%]': volatility,
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
