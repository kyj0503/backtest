"""
백테스트 검증 서비스

**역할**:
- 백테스트 요청 데이터의 유효성 검증
- 데이터 가용성 확인
- 전략 파라미터 검증

**주요 기능**:
1. validate_backtest_request(): 백테스트 요청 전체 검증
   - 날짜 범위 유효성
   - 종목 심볼 존재 여부
   - 전략 파라미터 유효성
2. check_data_availability(): 데이터 조회 가능 여부 확인
3. validate_date_range(): 날짜 범위 검증

**검증 규칙**:
- 시작일 < 종료일
- 날짜 포맷: YYYY-MM-DD
- 종목 데이터 존재 확인
- 전략별 파라미터 범위 검증

**의존성**:
- app/repositories/data_repository.py: 데이터 조회
- app/services/strategy_service.py: 전략 검증
- app/core/exceptions.py: 검증 예외

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (검증 호출)
- Backend: app/services/backtest_service.py (검증 후 실행)

**사용 패턴**:
- 백테스트 실행 전 요청 검증
- 조기 에러 감지로 불필요한 연산 방지
"""
import logging
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, Optional

from app.schemas.requests import BacktestRequest
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.exceptions import ValidationError
from app.repositories.data_repository import data_repository


class ValidationService:
    """백테스트 요청 검증 및 유틸리티 전담 서비스"""
    
    def __init__(self, data_repository_instance=None):
        self.data_repository = data_repository_instance or data_repository
        self.data_fetcher = data_fetcher
        self.logger = logging.getLogger(__name__)
    
    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 검증"""
        try:
            # 1. 티커 검증
            if not self.data_fetcher.validate_ticker(request.ticker):
                raise ValidationError(f"유효하지 않은 티커: {request.ticker}")
            
            # 2. 날짜 검증
            if request.start_date >= request.end_date:
                raise ValidationError("시작 날짜는 종료 날짜보다 빨라야 합니다")
            
            # 3. 현금 검증
            if request.initial_cash <= 0:
                raise ValidationError("초기 현금은 0보다 커야 합니다")
            
            # 4. 전략 검증
            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            if strategy_name not in strategy_service.get_all_strategies():
                raise ValidationError(f"지원하지 않는 전략: {request.strategy}")
            
            # 5. 전략 파라미터 검증
            if request.strategy_params:
                try:
                    strategy_service.validate_strategy_params(
                        strategy_name, 
                        request.strategy_params
                    )
                except ValueError as ve:
                    raise ValidationError(f"전략 파라미터 오류: {str(ve)}")
            
            self.logger.info(f"백테스트 요청 검증 완료: {request.ticker}")
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"백테스트 요청 검증 중 오류: {str(e)}")
            raise ValidationError(f"요청 검증 실패: {str(e)}")
    
    def safe_float(self, value, default: float = 0.0) -> float:
        """안전한 float 변환"""
        try:
            if pd.isna(value) or value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def safe_int(self, value, default: int = 0) -> int:
        """안전한 int 변환"""
        try:
            if pd.isna(value) or value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def safe_timedelta_to_days(self, timedelta):
        """Timedelta를 일수로 변환"""
        return timedelta.days if isinstance(timedelta, pd.Timedelta) else 0
    
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
