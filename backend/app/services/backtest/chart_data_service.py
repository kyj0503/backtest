"""
차트 데이터 생성 서비스
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np

from app.models.requests import BacktestRequest
from app.models.responses import (
    BacktestResult, ChartDataResponse, ChartDataPoint, 
    EquityPoint, TradeMarker, IndicatorData
)
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.custom_exceptions import ValidationError


class ChartDataService:
    """차트 데이터 생성 전담 서비스"""
    
    def __init__(self):
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service
        self.logger = logging.getLogger(__name__)
    
    async def generate_chart_data(self, request: BacktestRequest, backtest_result: BacktestResult = None) -> ChartDataResponse:
        """
        백테스트 결과로부터 Recharts용 차트 데이터를 생성합니다.
        
        ★ 주요 금융 용어 설명:
        
        1. OHLC: Open(시가), High(고가), Low(저가), Close(종가)
           - 하루의 주가 움직임을 나타내는 4가지 기본 가격
        
        2. SMA (Simple Moving Average, 단순 이동평균):
           - 일정 기간의 주가 평균값으로 추세를 파악하는 지표
           - SMA_20 = 최근 20일간 종가의 평균
           - 주가가 SMA 위에 있으면 상승추세, 아래에 있으면 하락추세
        
        3. 드로우다운 (Drawdown):
           - 투자 포트폴리오가 최고점에서 얼마나 떨어졌는지 나타내는 지표
           - 예: 1000만원 → 800만원 = -20% 드로우다운
           - 투자 위험을 측정하는 중요한 지표
        
        4. Buy & Hold 전략:
           - 주식을 사서 장기간 보유하는 가장 단순한 투자 전략
           - 시장 타이밍을 맞추려 하지 않고 꾸준히 보유
        
        5. 수익률 (Return):
           - 투자 원금 대비 얼마나 수익을 냈는지의 비율
           - (현재가 - 매수가) / 매수가 × 100
        
        6. 승률 (Win Rate):
           - 전체 거래 중 수익을 낸 거래의 비율
           - 높을수록 좋지만 수익 크기도 함께 고려해야 함
        """
        try:
            # 전략 파라미터 검증 (전략이 buy_and_hold가 아닐 때만)
            if request.strategy != "buy_and_hold":
                try:
                    self.strategy_service.validate_strategy_params(
                        request.strategy, 
                        request.strategy_params or {}
                    )
                except ValueError as ve:
                    self.logger.error(f"전략 파라미터 검증 실패: {str(ve)}")
                    raise ValidationError(str(ve))
            
            # 데이터 가져오기
            print(f"차트 데이터 생성 시작: {request.ticker}")
            data = self.data_fetcher.get_stock_data(
                ticker=request.ticker,
                start_date=request.start_date,
                end_date=request.end_date
            )
            print(f"차트용 데이터 로드: {len(data)} 행")
            
            # 1. OHLC 데이터 생성
            ohlc_data = self._generate_ohlc_data(data)
            self.logger.info(f"OHLC 데이터 생성 완료: {len(ohlc_data)} 포인트")
            
            # 2. 자산 곡선 데이터 생성 (Buy & Hold 기준)
            equity_data = self._generate_equity_data(data, request.initial_cash)
            self.logger.info(f"자산 곡선 데이터 생성 완료: {len(equity_data)} 포인트")
            
            # 3. 거래 마커 생성
            trade_markers = self._generate_trade_markers(data, request.strategy)
            self.logger.info(f"거래 마커 생성 완료: {len(trade_markers)} 개")
            
            # 4. 기술 지표 데이터 생성
            indicators = self._generate_indicators(data, request.strategy, request.strategy_params or {})
            self.logger.info(f"기술 지표 생성 완료: {len(indicators)} 개")
            
            # 5. 백테스트 통계 계산
            backtest_stats = self._calculate_backtest_stats(data, request.initial_cash)
            
            return ChartDataResponse(
                ticker=request.ticker,
                ohlc_data=ohlc_data,
                equity_data=equity_data,
                trade_markers=trade_markers,
                indicators=indicators,
                backtest_stats=backtest_stats
            )
            
        except Exception as e:
            self.logger.error(f"차트 데이터 생성 실패: {str(e)}")
            raise
    
    def _generate_ohlc_data(self, data: pd.DataFrame) -> List[ChartDataPoint]:
        """OHLC 데이터 생성"""
        ohlc_data = []
        for idx, row in data.iterrows():
            ohlc_data.append(ChartDataPoint(
                timestamp=idx.isoformat(),
                date=idx.strftime('%Y-%m-%d'),
                open=self.safe_float(row['Open']),
                high=self.safe_float(row['High']),
                low=self.safe_float(row['Low']),
                close=self.safe_float(row['Close']),
                volume=self.safe_int(row.get('Volume', 0))
            ))
        return ohlc_data
    
    def _generate_equity_data(self, data: pd.DataFrame, initial_cash: float) -> List[EquityPoint]:
        """자산 곡선 데이터 생성 (Buy & Hold 기준)"""
        equity_data = []
        initial_price = float(data['Close'].iloc[0])
        initial_equity = initial_cash
        max_price_so_far = initial_price
        
        for i, (idx, row) in enumerate(data.iterrows()):
            current_price = float(row['Close'])
            equity = initial_equity * (current_price / initial_price)
            return_pct = ((current_price / initial_price) - 1) * 100
            
            # 드로우다운 계산
            max_price_so_far = max(max_price_so_far, current_price)
            max_return_so_far = ((max_price_so_far / initial_price) - 1) * 100
            drawdown_pct = return_pct - max_return_so_far
            
            equity_data.append(EquityPoint(
                timestamp=idx.isoformat(),
                date=idx.strftime('%Y-%m-%d'),
                equity=equity,
                return_pct=return_pct,
                drawdown_pct=drawdown_pct
            ))
        
        return equity_data
    
    def _generate_trade_markers(self, data: pd.DataFrame, strategy: str) -> List[TradeMarker]:
        """거래 마커 생성"""
        if strategy == "buy_and_hold":
            # Buy & Hold는 첫날에 매수만
            first_date = data.index[0]
            first_price = float(data['Close'].iloc[0])
            
            return [TradeMarker(
                timestamp=first_date.isoformat(),
                date=first_date.strftime('%Y-%m-%d'),
                price=first_price,
                type="buy",
                size=1.0,
                reason="Buy & Hold 초기 매수"
            )]
        else:
            # 다른 전략들은 임시로 빈 리스트 반환 (추후 백테스트 결과에서 추출)
            return []
    
    def _generate_indicators(self, data: pd.DataFrame, strategy: str, strategy_params: Dict[str, Any]) -> List[IndicatorData]:
        """기술 지표 데이터 생성"""
        indicators = []
        
        if strategy == "sma_crossover":
            indicators.extend(self._generate_sma_indicators(data, strategy_params))
        elif strategy == "rsi_strategy":
            indicators.extend(self._generate_rsi_indicators(data, strategy_params))
        elif strategy == "bollinger_bands":
            indicators.extend(self._generate_bollinger_indicators(data, strategy_params))
        elif strategy == "macd_strategy":
            indicators.extend(self._generate_macd_indicators(data, strategy_params))
        
        return indicators
    
    def _generate_sma_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> List[IndicatorData]:
        """SMA 지표 생성"""
        indicators = []
        short_window = params.get('short_window', 10)
        long_window = params.get('long_window', 20)
        
        # 단기 SMA
        sma_short = data['Close'].rolling(window=short_window).mean()
        short_data = []
        for idx, sma_value in sma_short.items():
            if not pd.isna(sma_value):
                short_data.append({
                    "timestamp": idx.isoformat(),
                    "date": idx.strftime('%Y-%m-%d'),
                    "value": self.safe_float(sma_value)
                })
        
        if short_data:
            indicators.append(IndicatorData(
                name=f"SMA_{short_window}",
                type="line",
                color="#8884d8",
                data=short_data
            ))
        
        # 장기 SMA
        sma_long = data['Close'].rolling(window=long_window).mean()
        long_data = []
        for idx, sma_value in sma_long.items():
            if not pd.isna(sma_value):
                long_data.append({
                    "timestamp": idx.isoformat(),
                    "date": idx.strftime('%Y-%m-%d'),
                    "value": self.safe_float(sma_value)
                })
        
        if long_data:
            indicators.append(IndicatorData(
                name=f"SMA_{long_window}",
                type="line",
                color="#82ca9d",
                data=long_data
            ))
        
        return indicators
    
    def _generate_rsi_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> List[IndicatorData]:
        """RSI 지표 생성"""
        # RSI 구현 로직은 복잡하므로 추후 구현
        return []
    
    def _generate_bollinger_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> List[IndicatorData]:
        """볼린저 밴드 지표 생성"""
        # 볼린저 밴드 구현 로직은 복잡하므로 추후 구현
        return []
    
    def _generate_macd_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> List[IndicatorData]:
        """MACD 지표 생성"""
        # MACD 구현 로직은 복잡하므로 추후 구현
        return []
    
    def _calculate_backtest_stats(self, data: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """백테스트 통계 계산"""
        initial_price = float(data['Close'].iloc[0])
        final_price = float(data['Close'].iloc[-1])
        
        total_return = ((final_price / initial_price) - 1) * 100
        final_equity = initial_cash * (final_price / initial_price)
        
        return {
            "total_trades": 1,  # Buy & Hold은 1번 거래
            "win_rate": 100.0 if total_return > 0 else 0.0,
            "total_return": total_return,
            "final_equity": final_equity,
            "max_drawdown": 0.0,  # 단순화
            "sharpe_ratio": 0.0,  # 단순화
            "volatility": float(data['Close'].pct_change().std() * 100) if len(data) > 1 else 0.0
        }
    
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


# 글로벌 인스턴스
chart_data_service = ChartDataService()
