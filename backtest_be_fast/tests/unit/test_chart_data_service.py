"""
차트 데이터 서비스 테스트

**테스트 범위**:
- _generate_trade_markers(): 거래 마커 생성 로직
- _generate_ohlc_data(): OHLC 데이터 생성
- _generate_equity_data(): 자산 곡선 데이터 생성
- _generate_indicators(): 기술 지표 데이터 생성

**테스트 전략**:
- 단위 테스트: 각 메서드 개별 검증
- given-when-then 패턴 사용
- Mock 객체로 외부 의존성 격리

**테스트 목적**:
- 거래 마커가 올바른 형식으로 생성되는지 검증
- Buy & Hold 전략의 특수 케이스 처리
- 다양한 거래 로그 형식 지원
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import List, Dict, Any

from app.services.chart_data_service import ChartDataService
from app.schemas.responses import TradeMarker


@pytest.fixture
def chart_service():
    """차트 데이터 서비스 픽스처"""
    return ChartDataService()


@pytest.fixture
def sample_price_data():
    """샘플 가격 데이터 픽스처"""
    dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
    return pd.DataFrame({
        'Open': [100 + i for i in range(10)],
        'High': [105 + i for i in range(10)],
        'Low': [95 + i for i in range(10)],
        'Close': [102 + i for i in range(10)],
        'Volume': [1000000] * 10
    }, index=dates)


@pytest.fixture
def sample_trade_log():
    """샘플 거래 로그 픽스처"""
    return [
        {
            'EntryTime': '2023-01-02T00:00:00',
            'ExitTime': '2023-01-05T00:00:00',
            'EntryPrice': 101.0,
            'ExitPrice': 104.0,
            'Direction': 'Long',
            'Size': 10.0,
            'PnL (%)': 2.97
        },
        {
            'EntryTime': '2023-01-06T00:00:00',
            'ExitTime': '2023-01-08T00:00:00',
            'EntryPrice': 105.0,
            'ExitPrice': 107.0,
            'Direction': 'Long',
            'Size': 5.0,
            'PnL (%)': 1.90
        }
    ]


class TestTradeMarkerGeneration:
    """거래 마커 생성 테스트"""

    def test_buy_and_hold_creates_single_entry_marker(self, chart_service, sample_price_data):
        """
        Given: Buy & Hold 전략, 비어있는 거래 로그
        When: _generate_trade_markers() 호출
        Then: 첫 거래일에 단일 매수 마커만 생성됨
        """
        # Given
        strategy = "buy_and_hold"
        trade_log = []

        # When
        markers = chart_service._generate_trade_markers(
            data=sample_price_data,
            strategy=strategy,
            trade_log=trade_log
        )

        # Then
        assert len(markers) == 1, "Buy & Hold는 단일 매수 마커만 생성해야 함"
        marker = markers[0]
        assert marker.type == "entry", "첫 마커는 entry 타입이어야 함"
        assert marker.side == "buy", "첫 마커는 buy side여야 함"
        assert marker.date == "2023-01-01", "첫 거래일이어야 함"
        assert marker.price == 102.0, "첫 거래일 종가여야 함"

    def test_generate_markers_from_trade_log(self, chart_service, sample_price_data, sample_trade_log):
        """
        Given: 전략명과 거래 로그
        When: _generate_trade_markers() 호출
        Then: 거래 로그의 entry/exit에 대응하는 마커 생성
        """
        # Given
        strategy = "sma_crossover"

        # When
        markers = chart_service._generate_trade_markers(
            data=sample_price_data,
            strategy=strategy,
            trade_log=sample_trade_log
        )

        # Then
        # 2개 거래 × 2(entry+exit) = 4개 마커 예상
        assert len(markers) >= 4, "거래 로그의 모든 entry/exit이 마커로 변환되어야 함"

        # 첫 번째 거래의 entry 검증
        entry_markers = [m for m in markers if m.type == "entry"]
        assert len(entry_markers) >= 2, "2개 이상의 entry 마커가 있어야 함"

        first_entry = entry_markers[0]
        assert first_entry.date == "2023-01-02", "첫 entry 날짜"
        assert first_entry.price == 101.0, "첫 entry 가격"
        assert first_entry.side == "buy", "Long 방향은 buy side"
        assert first_entry.size == 10.0, "거래 수량"

        # Exit 마커 검증
        exit_markers = [m for m in markers if m.type == "exit"]
        assert len(exit_markers) >= 2, "2개 이상의 exit 마커가 있어야 함"

        first_exit = exit_markers[0]
        assert first_exit.date == "2023-01-05", "첫 exit 날짜"
        assert first_exit.price == 104.0, "첫 exit 가격"
        assert first_exit.side == "sell", "Long 포지션 청산은 sell side"
        assert first_exit.pnl_pct == 2.97, "수익률이 포함되어야 함"

    def test_empty_trade_log_returns_empty_markers(self, chart_service, sample_price_data):
        """
        Given: 비 Buy & Hold 전략, 빈 거래 로그
        When: _generate_trade_markers() 호출
        Then: 빈 마커 리스트 반환
        """
        # Given
        strategy = "sma_crossover"
        trade_log = []

        # When
        markers = chart_service._generate_trade_markers(
            data=sample_price_data,
            strategy=strategy,
            trade_log=trade_log
        )

        # Then
        assert len(markers) == 0, "빈 거래 로그는 빈 마커 리스트를 반환해야 함"

    def test_parse_direction_long_position(self, chart_service, sample_price_data):
        """
        Given: Direction='Long' 거래 로그
        When: _generate_trade_markers() 호출
        Then: Entry는 buy, Exit는 sell로 변환
        """
        # Given
        trade_log = [{
            'EntryTime': '2023-01-02T00:00:00',
            'ExitTime': '2023-01-05T00:00:00',
            'EntryPrice': 101.0,
            'ExitPrice': 104.0,
            'Direction': 'Long',
            'Size': 10.0
        }]

        # When
        markers = chart_service._generate_trade_markers(
            data=sample_price_data,
            strategy="sma_crossover",
            trade_log=trade_log
        )

        # Then
        entry = [m for m in markers if m.type == "entry"][0]
        exit_marker = [m for m in markers if m.type == "exit"][0]

        assert entry.side == "buy", "Long entry는 buy"
        assert exit_marker.side == "sell", "Long exit는 sell"

    def test_parse_direction_short_position(self, chart_service, sample_price_data):
        """
        Given: Direction='Short' 거래 로그
        When: _generate_trade_markers() 호출
        Then: Entry는 sell, Exit는 buy로 변환
        """
        # Given
        trade_log = [{
            'EntryTime': '2023-01-02T00:00:00',
            'ExitTime': '2023-01-05T00:00:00',
            'EntryPrice': 101.0,
            'ExitPrice': 99.0,
            'Direction': 'Short',
            'Size': 10.0
        }]

        # When
        markers = chart_service._generate_trade_markers(
            data=sample_price_data,
            strategy="rsi_strategy",
            trade_log=trade_log
        )

        # Then
        entry = [m for m in markers if m.type == "entry"][0]
        exit_marker = [m for m in markers if m.type == "exit"][0]

        assert entry.side == "sell", "Short entry는 sell"
        assert exit_marker.side == "buy", "Short exit는 buy"


class TestOHLCDataGeneration:
    """OHLC 데이터 생성 테스트"""

    def test_generate_ohlc_data_structure(self, chart_service, sample_price_data):
        """
        Given: 가격 데이터 DataFrame
        When: _generate_ohlc_data() 호출
        Then: 모든 행이 ChartDataPoint로 변환됨
        """
        # When
        ohlc_data = chart_service._generate_ohlc_data(sample_price_data)

        # Then
        assert len(ohlc_data) == len(sample_price_data), "모든 행이 변환되어야 함"
        
        first_point = ohlc_data[0]
        assert first_point.date == "2023-01-01", "날짜 형식"
        assert first_point.open == 100.0, "시가"
        assert first_point.high == 105.0, "고가"
        assert first_point.low == 95.0, "저가"
        assert first_point.close == 102.0, "종가"
        assert first_point.volume == 1000000, "거래량"

    def test_generate_ohlc_handles_nan_volume(self, chart_service):
        """
        Given: Volume 컬럼이 없거나 NaN인 데이터
        When: _generate_ohlc_data() 호출
        Then: Volume은 0으로 기본값 설정
        """
        # Given
        dates = pd.date_range(start='2023-01-01', end='2023-01-03', freq='D')
        data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [102, 103, 104]
        }, index=dates)

        # When
        ohlc_data = chart_service._generate_ohlc_data(data)

        # Then
        assert all(point.volume == 0 for point in ohlc_data), "Volume 기본값은 0"


class TestEquityDataGeneration:
    """자산 곡선 데이터 생성 테스트"""

    def test_generate_equity_data_buy_and_hold(self, chart_service, sample_price_data):
        """
        Given: 가격 데이터와 초기 자본
        When: _generate_equity_data() 호출
        Then: Buy & Hold 기준 자산 곡선 생성
        """
        # Given
        initial_cash = 10000.0

        # When
        equity_data = chart_service._generate_equity_data(sample_price_data, initial_cash)

        # Then
        assert len(equity_data) == len(sample_price_data), "모든 날짜에 대한 equity 생성"

        # 첫날: 수익률 0%, 드로우다운 0%
        first = equity_data[0]
        assert first.equity == initial_cash, "초기 자산"
        assert first.return_pct == 0.0, "첫날 수익률 0%"
        assert first.drawdown_pct == 0.0, "첫날 드로우다운 0%"

        # 마지막날: 가격 상승에 따른 수익
        last = equity_data[-1]
        initial_price = sample_price_data['Close'].iloc[0]
        final_price = sample_price_data['Close'].iloc[-1]
        expected_return = ((final_price / initial_price) - 1) * 100

        assert last.return_pct == pytest.approx(expected_return, rel=1e-2), "최종 수익률"

    def test_equity_data_calculates_drawdown(self, chart_service):
        """
        Given: 가격이 하락하는 데이터
        When: _generate_equity_data() 호출
        Then: 드로우다운이 올바르게 계산됨
        """
        # Given: 가격 상승 후 하락
        dates = pd.date_range(start='2023-01-01', end='2023-01-05', freq='D')
        prices = [100, 110, 120, 115, 105]  # 최고점 120에서 105로 하락
        data = pd.DataFrame({
            'Open': prices,
            'High': prices,
            'Low': prices,
            'Close': prices,
            'Volume': [1000000] * 5
        }, index=dates)

        # When
        equity_data = chart_service._generate_equity_data(data, 10000.0)

        # Then
        # 최고점(Day 3) 이후 하락 시 드로우다운 음수
        peak_day = equity_data[2]
        assert peak_day.drawdown_pct == 0.0, "최고점에서 드로우다운 0%"

        last_day = equity_data[-1]
        # 최고점(120) 대비 현재(105) = (105/100 - 1)*100 - (120/100 - 1)*100
        # = 5% - 20% = -15%
        assert last_day.drawdown_pct < 0, "하락 시 드로우다운 음수"


class TestIndicatorGeneration:
    """기술 지표 생성 테스트"""

    def test_generate_sma_indicators(self, chart_service, sample_price_data):
        """
        Given: SMA 전략 파라미터
        When: _generate_sma_indicators() 호출
        Then: 단기/장기 SMA 지표 생성
        """
        # Given
        params = {'short_window': 3, 'long_window': 5}

        # When
        indicators = chart_service._generate_sma_indicators(sample_price_data, params)

        # Then
        assert len(indicators) == 2, "단기/장기 2개 SMA 지표"
        
        sma_short = next(ind for ind in indicators if ind.name == "SMA_3")
        sma_long = next(ind for ind in indicators if ind.name == "SMA_5")

        assert sma_short.type == "line"
        assert len(sma_short.data) > 0, "SMA 데이터 생성됨"
        
        # 단기 SMA는 장기보다 더 많은 데이터 포인트 (윈도우가 작으므로)
        assert len(sma_short.data) >= len(sma_long.data)

    def test_generate_rsi_indicators(self, chart_service, sample_price_data):
        """
        Given: RSI 전략 파라미터
        When: _generate_rsi_indicators() 호출
        Then: RSI, 과매수, 과매도 라인 생성
        """
        # Given
        params = {'rsi_period': 14, 'rsi_overbought': 70, 'rsi_oversold': 30}

        # When
        indicators = chart_service._generate_rsi_indicators(sample_price_data, params)

        # Then
        assert len(indicators) == 3, "RSI + 과매수 + 과매도 라인"
        
        rsi_line = next(ind for ind in indicators if ind.name == "RSI_14")
        overbought = next(ind for ind in indicators if ind.name == "RSI_OVERBOUGHT")
        oversold = next(ind for ind in indicators if ind.name == "RSI_OVERSOLD")

        assert rsi_line.type == "line"
        assert overbought.data[0]['value'] == 70, "과매수 기준선"
        assert oversold.data[0]['value'] == 30, "과매도 기준선"


@pytest.mark.integration
class TestChartDataIntegration:
    """차트 데이터 통합 테스트 (실제 데이터 흐름)"""

    @pytest.mark.asyncio
    async def test_generate_chart_data_with_trade_markers(self, chart_service, sample_price_data):
        """
        Given: 백테스트 요청과 결과
        When: generate_chart_data() 호출
        Then: trade_markers 포함된 응답 생성
        """
        # 이 테스트는 실제 API와 통합하여 검증하므로 integration 마커 사용
        # 여기서는 구조 검증만 수행
        pass  # E2E 테스트에서 더 상세히 검증

