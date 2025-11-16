"""
백테스트 검증 서비스

**역할**:
- 백테스트 요청 데이터의 유효성 검증 (Validator 위임)
- 폴백 통계 생성 유틸리티

**주요 기능**:
1. validate_backtest_request(): 백테스트 요청 전체 검증 → BacktestValidator로 위임
2. create_fallback_stats(): 폴백 통계 생성

**리팩터링 변경사항**:
- 검증 로직은 BacktestValidator로 위임
- 이 서비스는 호환성 레이어 역할
- 향후 deprecate 예정

**의존성**:
- app/validators/backtest_validator: 검증 로직
- app/core/exceptions: 검증 예외

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (검증 호출)
- Backend: app/services/backtest_service.py (검증 후 실행)

**사용 패턴**:
- 백테스트 실행 전 요청 검증
- 조기 에러 감지로 불필요한 연산 방지
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
    """백테스트 요청 검증 및 유틸리티 전담 서비스

    Note: 검증 로직은 BacktestValidator로 위임됨 (Phase 2.3 리팩터링)
    """

    def __init__(self, data_fetcher_instance=None, strategy_service_instance=None):
        """
        Args:
            data_fetcher_instance: DataFetcher 인스턴스 (선택)
            strategy_service_instance: StrategyService 인스턴스 (선택)
        """
        self.data_fetcher = data_fetcher_instance or data_fetcher
        self.strategy_service = strategy_service_instance or strategy_service
        self.logger = logging.getLogger(__name__)

        # Phase 2.3: 새로운 BacktestValidator 사용
        self.backtest_validator = BacktestValidator(
            data_fetcher=self.data_fetcher,
            strategy_service=self.strategy_service
        )

    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """
        백테스트 요청 검증 (BacktestValidator로 위임)

        Args:
            request: BacktestRequest 객체

        Raises:
            ValidationError: 검증 실패 시
        """
        try:
            # Phase 2.3: BacktestValidator로 위임
            self.backtest_validator.validate_request(request)
            self.logger.info(f"백테스트 요청 검증 완료: {request.ticker}")

        except ValueError as ve:
            # BacktestValidator의 ValueError를 ValidationError로 변환
            self.logger.error(f"백테스트 요청 검증 실패: {str(ve)}")
            raise ValidationError(str(ve))
        except Exception as e:
            self.logger.error(f"백테스트 요청 검증 중 오류: {str(e)}")
            raise ValidationError(f"요청 검증 실패: {str(e)}")

    def create_fallback_stats(self, data: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """마지막 수단: 수동으로 기본 통계 생성"""
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
