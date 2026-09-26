"""백테스트 검증 서비스

백테스트 요청 검증을 BacktestValidator에 위임합니다.
"""
import logging

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


# 글로벌 인스턴스
validation_service = ValidationService()
