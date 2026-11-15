"""DcaCalculator(표시용 DCA 계산기) 단위 테스트 (P1-12).

주의: 이 계산기는 시뮬레이션 엔진(portfolio_dca_manager.py)과는 별개의
"표시용" 경로다 -- TODO.md P2-13에 이미 "한 응답에 DCA 실행 모델 2개"로
문서화된 기존 이슈이며, 이 파일은 그 불일치를 새로 다루지 않는다. 여기서는
DcaCalculator 자체의 계약(수량/평균단가/수익률 계산, 빈 데이터·주기
소진·미지의 주기 처리)만 검증한다. 지금까지 이 파일을 직접 임포트하는
테스트가 없었다.
"""
import pandas as pd
import pytest

from app.services.dca_calculator import DcaCalculator

pytestmark = pytest.mark.unit


class TestCalculateDcaSharesAndReturn:
    def test_three_periods_hand_derived_shares_and_return(self):
        """시작일(2024-01-01, 1월의 첫 번째 월요일)부터 monthly_1 주기로 3회.
        데이터를 각 회차가 정확히 매칭되는 날짜(그 달의 첫 번째 월요일:
        1/1, 2/5, 3/4)에만 두어 매수가만 결정론적으로 고정했다.

        손으로 계산:
          회차0: $1000 / $100 = 10.0주
          회차1: $1000 / $120 = 8.333333...주
          회차2: $1000 / $90  = 11.111111...주
          총 주식수 = 29.444444444444446
          평균단가 = 3000 / 29.444444444444446 = 101.88679245283018
          종가(마지막 행) = 90 -> 수익률 = (90/101.88679... - 1)*100 = -11.666666666666659%
        (계산기로 검증한 값.)
        """
        df = pd.DataFrame(
            {'Close': [100.0, 120.0, 90.0]},
            index=pd.to_datetime(['2024-01-01', '2024-02-05', '2024-03-04']),
        )

        total_shares, average_price, return_rate, trade_log = DcaCalculator.calculate_dca_shares_and_return(
            df=df, period_amount=1000.0, dca_periods=3,
            start_date='2024-01-01', frequency='monthly_1',
        )

        assert total_shares == pytest.approx(29.444444444444446)
        assert average_price == pytest.approx(101.88679245283018)
        assert return_rate == pytest.approx(-11.666666666666659)
        assert len(trade_log) == 3
        assert trade_log[0]['EntryPrice'] == pytest.approx(100.0)
        assert trade_log[0]['Size'] == pytest.approx(10.0)
        assert trade_log[0]['Type'] == 'BUY'
        assert trade_log[0]['ExitTime'] is None
        assert trade_log[1]['EntryPrice'] == pytest.approx(120.0)
        assert trade_log[2]['EntryPrice'] == pytest.approx(90.0)

    def test_empty_dataframe_returns_zeroes(self):
        df = pd.DataFrame({'Close': []})
        df.index = pd.to_datetime(df.index)

        result = DcaCalculator.calculate_dca_shares_and_return(
            df=df, period_amount=1000.0, dca_periods=3,
            start_date='2024-01-01', frequency='monthly_1',
        )

        assert result == (0, 0, 0, [])

    def test_zero_periods_returns_zeroes(self):
        df = pd.DataFrame({'Close': [100.0]}, index=pd.to_datetime(['2024-01-01']))

        result = DcaCalculator.calculate_dca_shares_and_return(
            df=df, period_amount=1000.0, dca_periods=0,
            start_date='2024-01-01', frequency='monthly_1',
        )

        assert result == (0, 0, 0, [])

    def test_all_investment_dates_after_available_data_returns_zeroes(self):
        """데이터가 모든 투자 예정일보다 과거에서 끝나버리면(예: 시작일을
        데이터의 마지막 날짜보다 미래로 설정) 어떤 회차도 매수되지 않는다."""
        df = pd.DataFrame({'Close': [100.0]}, index=pd.to_datetime(['2023-01-01']))

        result = DcaCalculator.calculate_dca_shares_and_return(
            df=df, period_amount=1000.0, dca_periods=2,
            start_date='2024-01-01', frequency='monthly_1',
        )

        assert result == (0, 0, 0, [])

    def test_unknown_frequency_falls_back_to_monthly_1_silently(self):
        """스키마 검증(FREQUENCY_MAP 멤버십)을 우회해서 이 함수가 직접
        호출되면, 미지의 frequency 문자열은 예외 없이 monthly_1로 조용히
        대체된다 (경고 로그만 남김)."""
        df = pd.DataFrame(
            {'Close': [100.0, 120.0, 90.0]},
            index=pd.to_datetime(['2024-01-01', '2024-02-05', '2024-03-04']),
        )

        fallback_result = DcaCalculator.calculate_dca_shares_and_return(
            df=df, period_amount=1000.0, dca_periods=3,
            start_date='2024-01-01', frequency='not_a_real_frequency',
        )
        explicit_result = DcaCalculator.calculate_dca_shares_and_return(
            df=df, period_amount=1000.0, dca_periods=3,
            start_date='2024-01-01', frequency='monthly_1',
        )

        assert fallback_result[0] == pytest.approx(explicit_result[0])
        assert fallback_result[2] == pytest.approx(explicit_result[2])
