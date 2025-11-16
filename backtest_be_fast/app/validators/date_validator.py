"""
날짜 검증 로직

**역할**:
- 날짜 범위 유효성 검증
- 백테스트 기간 제한 검증
- 미래 날짜 검증

**주요 기능**:
1. validate_date_range(): 시작일과 종료일 범위 검증
2. validate_not_future(): 미래 날짜 검증
3. validate_business_days(): 영업일 기준 최소 데이터 검증

**검증 규칙**:
- 시작일 < 종료일
- 미래 날짜 불가
- 최소/최대 백테스트 기간 제한
- 최소 영업일 수 확인

**사용 예**:
```python
from app.validators.date_validator import DateValidator

validator = DateValidator()
validator.validate_date_range(start_date, end_date, min_days=30)
validator.validate_not_future(end_date)
```
"""
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class DateValidator:
    """날짜 검증 전담 클래스"""

    @staticmethod
    def validate_date_range(
        start_date: date,
        end_date: date,
        min_days: int = 30,
        max_days: int = 3650
    ) -> None:
        """
        날짜 범위 검증

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            min_days: 최소 기간 (일)
            max_days: 최대 기간 (일)

        Raises:
            ValueError: 날짜 범위가 유효하지 않은 경우

        Examples:
            >>> from datetime import date
            >>> validator = DateValidator()
            >>> validator.validate_date_range(
            ...     date(2023, 1, 1),
            ...     date(2023, 12, 31)
            ... )
        """
        if not isinstance(start_date, date):
            raise ValueError(f"시작일이 date 타입이 아닙니다: {type(start_date)}")

        if not isinstance(end_date, date):
            raise ValueError(f"종료일이 date 타입이 아닙니다: {type(end_date)}")

        if end_date <= start_date:
            raise ValueError(
                f"종료일({end_date})은 시작일({start_date})보다 이후여야 합니다"
            )

        delta = (end_date - start_date).days

        if delta < min_days:
            raise ValueError(
                f"백테스트 기간이 너무 짧습니다: {delta}일 (최소 {min_days}일 필요)"
            )

        if delta > max_days:
            raise ValueError(
                f"백테스트 기간이 너무 깁니다: {delta}일 (최대 {max_days}일 허용)"
            )

        logger.debug(f"날짜 범위 검증 통과: {start_date} ~ {end_date} ({delta}일)")

    @staticmethod
    def validate_not_future(target_date: date) -> None:
        """
        미래 날짜가 아닌지 검증

        Args:
            target_date: 검증할 날짜

        Raises:
            ValueError: 미래 날짜인 경우

        Examples:
            >>> from datetime import date
            >>> validator = DateValidator()
            >>> validator.validate_not_future(date(2023, 1, 1))  # OK
            >>> validator.validate_not_future(date(2030, 1, 1))  # ValueError
        """
        today = date.today()
        if target_date > today:
            raise ValueError(
                f"미래 날짜는 사용할 수 없습니다: {target_date} (오늘: {today})"
            )

        logger.debug(f"미래 날짜 검증 통과: {target_date}")

    @staticmethod
    def validate_business_days(
        start_date: date,
        end_date: date,
        min_business_days: int = 20
    ) -> None:
        """
        최소 영업일 수 검증 (간이 계산)

        주말을 제외한 대략적인 영업일 수를 계산합니다.
        정확한 휴일 계산은 하지 않고 주말만 제외합니다.

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            min_business_days: 최소 영업일 수

        Raises:
            ValueError: 영업일 수가 부족한 경우

        Examples:
            >>> from datetime import date
            >>> validator = DateValidator()
            >>> validator.validate_business_days(
            ...     date(2023, 1, 1),
            ...     date(2023, 3, 1),
            ...     min_business_days=30
            ... )
        """
        total_days = (end_date - start_date).days
        # 대략적인 영업일 계산: 전체 일수 * (5/7)
        estimated_business_days = int(total_days * 5 / 7)

        if estimated_business_days < min_business_days:
            raise ValueError(
                f"백테스트를 위한 영업일이 부족합니다: "
                f"약 {estimated_business_days}일 (최소 {min_business_days}일 필요)"
            )

        logger.debug(f"영업일 수 검증 통과: 약 {estimated_business_days}일")
