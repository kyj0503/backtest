"""
Bollinger Bands 전략 요구사항 기반 테스트 (Black-box Testing)

**테스트 전략**:
- **명세 기반 테스트 (Specification-based Testing)**: `requirements.md`의 REQ-BB-xx 항목 검증
- **동등 분할 (Equivalence Partitioning)**: 매수/매도/대기 구간 분할
- **경계값 분석 (Boundary Value Analysis)**: 밴드 경계선(±epsilon)에서의 동작 검증
"""
import pytest
import pandas as pd
import numpy as np
from backtesting import Backtest
from app.strategies.bollinger_strategy import BollingerBandsStrategy

class TestBollingerBandsRequirements:
    """
    [REQ-BB-01 ~ REQ-BB-09] 볼린저 밴드 전략 요구사항 검증
    """

    def create_fixture_data(self, price_pattern: list) -> pd.DataFrame:
        """테스트용 OHLC 데이터 생성 헬퍼"""
        dates = pd.date_range(start='2024-01-01', periods=len(price_pattern), freq='D')
        prices = np.array(price_pattern, dtype=float)
        return pd.DataFrame({
            'Open': prices,
            'High': prices * 1.001,  # 고가/저가 폭을 좁게 설정하여 종가 위주 테스트
            'Low': prices * 0.999,
            'Close': prices,
            'Volume': [1000] * len(prices)
        }, index=dates)

    @pytest.fixture
    def standard_setup(self):
        """기본 설정: 20일 이동평균, 승수 2, 초기자금 10,000"""
        return {
            'period': 20,
            'std_dev': 2,
            'cash': 10000
        }

    # ============================================================================
    # REQ-BB-05 (매수 진입): 주가 < 하단 밴드
    # ============================================================================
    @pytest.mark.parametrize("price_offset, expected_trade", [
        # [경계값 분석] 하단 밴드 기준
        (-0.01, True),   # 하단 밴드보다 0.01 낮음 -> 매수 (Valid Partition)
        (0.00,  False),  # 하단 밴드와 같음 -> 대기 (Boundary)
        (0.01,  False),  # 하단 밴드보다 0.01 높음 -> 대기 (Invalid Partition)
    ])
    def test_req_bb_05_buy_signal_boundary(self, standard_setup, price_offset, expected_trade):
        """
        [REQ-BB-05] 하단 밴드 경계값 분석
        Given: 20일간 일정하여 밴드가 고정된 상태
        When: 21일차 가격이 (하단 밴드 + offset)일 때
        Then: 하단 밴드 미만일 경우에만 매수 발생
        """
        # 1. 고정 가격으로 밴드 형성 (Mean=100, Std=0인 상태를 피하기 위해 약간의 진동을 줌)
        # Std가 0이면 밴드폭이 0이 되므로, 의도적으로 Std를 만듦
        # [100, 102, 100, 102...] -> Mean=101, Std=1
        base_prices = [100, 102] * 10  # 20일 데이터
        
        # 2. 마지막 시점(20일차) 기준 계산 예상
        # Mean = 101
        # Std ≈ 1.0 (ddof=1 기준 계산 시 약간 다를 수 있음, pandas default는 ddof=1)
        # Pandas Std 계산: [100, 102] 반복 시 Std=1.0259... 이나, 계산 편의를 위해 시뮬레이션 활용
        
        # 정확한 제어를 위해, 백테스트 엔진을 돌려서 직전 밴드를 확인하는 대신
        # '거의 고정된 밴드'를 가정하고 상대적인 움직임을 테스트하기보다
        # 명확하게 하락 돌파 시나리오를 구성.
        
        # 전략: 20일간 100으로 유지 -> Std=0 -> Band=100
        # 이 경우 99.99 매수, 100.00 대기?
        # Std=0 일 때의 예외처리가 있을 수 있으므로, 약간의 변동성 주입
        # 19일간 100, 1일간 104 -> 평균 소폭 상승, Std 발생
        
        prices = [100] * 19 + [104] # 20일차
        # 20일차 Close=104.
        # Mean(20) = (1900 + 104) / 20 = 100.2
        # Std(20) 계산 ... 복잡함.
        
        # 대안: 이미 계산 로직(Req-BB-01~04)은 신뢰한다고 가정(혹은 별도 검증).
        # 여기서는 "하단 밴드 값"을 동적으로 구해서, 그 값 기준으로 마지막 틱을 조작해야 함.
        # 하지만 Backtest 라이브러리는 데이터를 한 번에 넣어야 하므로,
        # '미리 계산된 밴드값'을 알기 어렵다.
        
        # 해결책: 극단적으로 단순한 데이터 사용 (모두 100) -> Band=100 (폭 0)
        # Std Dev가 0일 때 밴드 폭 0.
        # Lower Band = 100.
        # Case 1: 99.99 (Lower보다 작음) -> 매수?
        # Case 2: 100.00 (Lower와 같음) -> 대기?
        
        setup_data = [100] * 20
        test_price = 100 + price_offset
        full_data = setup_data + [test_price] # 21번째 데이터가 테스트 대상
        
        df = self.create_fixture_data(full_data)
        bt = Backtest(df, BollingerBandsStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(period=20, std_dev=2)
        
        if expected_trade:
            # 매수가 일어났다면 Trades가 1개 이상이어야 함
            assert len(stats['_trades']) > 0, f"Offset {price_offset}: 매수했어야 함 (Price={test_price})"
        else:
            assert len(stats['_trades']) == 0, f"Offset {price_offset}: 매수하지 말았어야 함 (Price={test_price})"

    # ============================================================================
    # REQ-BB-06 (매도 청산): 주가 > 상단 밴드
    # ============================================================================
    @pytest.mark.parametrize("price_offset, expected_exit", [
        # [경계값 분석] 상단 밴드 기준 (보유 중 가정)
        (0.01, True),   # 상단 밴드 초과 -> 매도
        (0.00, False),  # 상단 밴드 도달 -> 유지 (초과 조건이므로)
        (-0.01, False), # 상단 밴드 미만 -> 유지
    ])
    def test_req_bb_06_sell_signal_boundary(self, standard_setup, price_offset, expected_exit):
        """
        [REQ-BB-06] 상단 밴드 경계값 분석 (청산)
        Given: 포지션 보유 상태 (강제 주입 혹은 매수 유도)
        When: 가격이 상단 밴드 근처로 이동
        Then: 상단 밴드 초과 시에만 청산
        """
        # 1. 매수 유도: 100 -> 90 (하단 돌파, 매수) -> 100 (회귀)
        # 2. 밴드 형성: 100으로 안정화
        # 3. 테스트: 상단 밴드(100) 기준 Offset
        
        # 데이터 구성:
        pre_data = [100] * 20          # 밴드 100, Std 0
        buy_trigger = [90]             # 하단(100) 하향 돌파 -> 매수
        stability = [100] * 5          # 밴드 다시 100으로 안정화 (Std 0에 수렴)
        
        # 테스트 시점
        test_price = 100 + price_offset
        
        full_data = pre_data + buy_trigger + stability + [test_price]
        df = self.create_fixture_data(full_data)
        
        bt = Backtest(df, BollingerBandsStrategy, cash=standard_setup['cash'], commission=0)
        stats = bt.run(period=5, std_dev=2) # period 짧게 하여 빠르게 반영
        
        trades = stats['_trades']
        
        # 먼저 진입 거래가 있었는지 확인
        assert len(trades) > 0, "테스트 전제 실패: 매수가 발생하지 않음"
        
        # 마지막 거래가 매도(Exit) 되었는지 확인
        # ExitTime이 존재하면 매도된 것
        last_trade = trades.iloc[-1]
        
        if expected_exit:
            assert pd.notna(last_trade['ExitTime']), f"Offset {price_offset}: 청산되지 않음"
        else:
            # 아직 보유 중이어야 함 (ExitTime이 NaT 혹은 마지막 봉이 아님)
            # 여기서는 마지막 봉에서 청산 여부를 보므로, ExitTime이 있더라도 그게 테스트 봉이어야 함
            # 혹은 간단히 Trade가 닫혔는지 확인
            # 만약 닫혔다면, 그게 이번 테스트 캔들 때문인지 확인 필요하지만
            # stability 구간(100)은 상단(100)과 같아서 매도 안함(False case).
            # 따라서 닫혀있으면 이번 캔들 때문일 것임.
            
            # 주의: stability 구간이 상단밴드(100)와 같음.
            # 로직상 ">" 인지 ">=" 인지 중요. REQ는 ">" (초과).
            # 따라서 100일때는 안 팔려야 함.
             assert pd.isna(last_trade['ExitTime']), f"Offset {price_offset}: 의도치 않게 청산됨"


    # ============================================================================
    # REQ-BB-08 (데이터 부족): N개 미만
    # ============================================================================
    def test_req_bb_08_insufficient_data(self):
        """
        [REQ-BB-08] 데이터 부족 시 신호 미발생 확인
        Given: 데이터 개수 < Period
        When: 전략 실행
        Then: 거래 0건
        """
        data = [100, 90, 80, 70] # 4개
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BollingerBandsStrategy, cash=10000, commission=0)
        stats = bt.run(period=20, std_dev=2) # Period 20
        
        assert len(stats['_trades']) == 0

    # ============================================================================
    # REQ-BB-07 (중심선 청산): 이익 실현
    # ============================================================================
    def test_req_bb_07_exit_at_sma(self):
        """
        [REQ-BB-07] 중심선(SMA) 복귀 시 청산 (이익 실현)
        Given: 하단 매수 후
        When: 가격이 SMA 위로 올라옴 (상단 밴드까지는 안 감)
        Then: 청산 발생
        """
        # 1. 100 유지 (SMA=100)
        # 2. 90 급락 (매수)
        # 3. 101 회복 (SMA=약 99~100 사이일 것, 101이면 확실히 SMA 위)
        #    단, 상단 밴드보다는 아래여야 함.
        #    Std가 커졌으므로 상단은 110 넘을 것임.
        
        # 데이터가 너무 짧으면 indicator 계산이 안 될 수 있음.
        # period=5로 단축
        
        # 0~4 (100) -> SMA=100
        # 5 (90) -> SMA=(400+90)/5=98.  Low(90) < Band(100-2*0=100) -> Buy? 
        #   (Std=0 구간이라 Band=SMA=100 이었을 것. 직전 봉 기준이면.)
        #   Backtesting.py는 현재 봉(Close) < Band 등은 확인 가능.
        
        data = [100]*20 + [90] + [101]
        df = self.create_fixture_data(data)
        
        bt = Backtest(df, BollingerBandsStrategy, cash=10000, commission=0)
        stats = bt.run(period=10, std_dev=2)
        
        trades = stats['_trades']
        assert len(trades) > 0
        assert pd.notna(trades.iloc[-1]['ExitTime']) # 청산됨
