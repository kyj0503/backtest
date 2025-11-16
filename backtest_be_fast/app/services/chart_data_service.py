"""차트 데이터 생성 서비스

백테스트 결과를 Recharts용 형식으로 변환합니다.
OHLC, 자산 곡선, 기술 지표(SMA, RSI, Bollinger Bands, MACD, EMA), 거래 마커, 벤치마크 데이터를 생성합니다.
Strategy Pattern과 Factory Pattern을 사용합니다.
"""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import date
import pandas as pd
import numpy as np

from app.schemas.requests import BacktestRequest
from app.utils.type_converters import safe_float, safe_int
from app.schemas.responses import (
    BacktestResult, ChartDataResponse, ChartDataPoint,
    EquityPoint, TradeMarker, IndicatorData, BenchmarkPoint
)
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.services.indicators import indicator_factory
from app.core.exceptions import ValidationError


class ChartDataService:
    """차트 데이터 생성 전담 서비스"""

    # 전략명을 지표명으로 매핑
    STRATEGY_TO_INDICATOR_MAP = {
        'sma_crossover': 'SMA',
        'rsi_strategy': 'RSI',
        'bollinger_bands': 'Bollinger Bands',
        'macd_strategy': 'MACD',
        'ema_crossover': 'EMA',
    }

    def __init__(self, data_repository=None, strategy_service_instance=None):
        self.data_repository = data_repository
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service_instance or strategy_service
        self.logger = logging.getLogger(__name__)
    
    async def generate_chart_data(self, request: BacktestRequest, backtest_result: BacktestResult = None) -> ChartDataResponse:
        """Recharts용 차트 데이터 생성 (OHLC, 자산 곡선, 지표, 거래 마커, 벤치마크)"""
        try:
            # 전략 파라미터 검증 (전략이 buy_hold_strategy가 아닐 때만)
            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            if strategy_name != "buy_hold_strategy":
                try:
                    self.strategy_service.validate_strategy_params(
                        strategy_name, 
                        request.strategy_params or {}
                    )
                except ValueError as ve:
                    self.logger.error(f"전략 파라미터 검증 실패: {str(ve)}")
                    raise ValidationError(str(ve))
            
            # 데이터 가져오기
            self.logger.info("차트 데이터 생성 시작: %s", request.ticker)
            data = await self._get_price_data(
                request.ticker, request.start_date, request.end_date
            )
            self.logger.info("차트용 데이터 로드 완료: %s 행", len(data))
            
            # 1. OHLC 데이터 생성
            ohlc_data = self._generate_ohlc_data(data)
            self.logger.info(f"OHLC 데이터 생성 완료: {len(ohlc_data)} 포인트")
            
            # 2. 자산 곡선 데이터 생성 (Buy & Hold 기준)
            equity_data = self._generate_equity_data(data, request.initial_cash)
            self.logger.info(f"자산 곡선 데이터 생성 완료: {len(equity_data)} 포인트")
            
            # 3. 거래 마커 생성
            trade_log = backtest_result.trade_log if backtest_result else []
            trade_markers = self._generate_trade_markers(data, strategy_name, trade_log)
            self.logger.info(f"거래 마커 생성 완료: {len(trade_markers)} 개")
            
            # 4. 기술 지표 데이터 생성
            indicators = self._generate_indicators(data, strategy_name, request.strategy_params or {})
            self.logger.info(f"기술 지표 생성 완료: {len(indicators)} 개")
            
            # 5. 백테스트 통계 계산
            # 통계 정보 생성
            if backtest_result:
                # 실제 백테스트 결과를 사용
                backtest_stats = {
                    "total_return_pct": backtest_result.total_return_pct,
                    "sharpe_ratio": backtest_result.sharpe_ratio,
                    "max_drawdown_pct": backtest_result.max_drawdown_pct,
                    "total_trades": backtest_result.total_trades,
                    "win_rate_pct": backtest_result.win_rate_pct,
                    "profit_factor": backtest_result.profit_factor,
                    "final_equity": backtest_result.final_equity,
                    "volatility_pct": backtest_result.volatility_pct or 0.0,
                    "annualized_return_pct": backtest_result.annualized_return_pct,
                    "sortino_ratio": backtest_result.sortino_ratio or 0.0,
                    "calmar_ratio": backtest_result.calmar_ratio or 0.0
                }
            else:
                # 후보값으로 간단한 Buy & Hold 통계 계산
                backtest_stats = self._calculate_backtest_stats(data, request.initial_cash)

            # 6. 벤치마크가 지정된 경우 상대 성과 계산
            benchmark_ticker = getattr(request, 'benchmark_ticker', None)
            if benchmark_ticker:
                try:
                    bm_data = await self._get_price_data(
                        benchmark_ticker,
                        request.start_date,
                        request.end_date,
                    )
                    if bm_data is not None and not bm_data.empty:
                        bm_initial = float(bm_data['Close'].iloc[0])
                        bm_final = float(bm_data['Close'].iloc[-1])
                        bm_ret = ((bm_final / bm_initial) - 1) * 100
                        backtest_stats['benchmark_ticker'] = benchmark_ticker
                        backtest_stats['benchmark_total_return_pct'] = bm_ret
                        # 총수익률 대비 초과수익률(알파)
                        backtest_stats['alpha_vs_benchmark_pct'] = (
                            backtest_stats.get('total_return_pct', 0.0) - bm_ret
                        )
                except Exception as e:
                    self.logger.warning(f"벤치마크 계산 중 오류({benchmark_ticker}): {e}")

            # 7. 벤치마크 데이터 생성 (S&P 500, NASDAQ)
            sp500_benchmark = await self._generate_benchmark_data("^GSPC", request.start_date, request.end_date)
            nasdaq_benchmark = await self._generate_benchmark_data("^IXIC", request.start_date, request.end_date)

            return ChartDataResponse(
                ticker=request.ticker,
                strategy=strategy_name,
                start_date=request.start_date.strftime('%Y-%m-%d') if hasattr(request.start_date, 'strftime') else str(request.start_date),
                end_date=request.end_date.strftime('%Y-%m-%d') if hasattr(request.end_date, 'strftime') else str(request.end_date),
                ohlc_data=ohlc_data,
                equity_data=equity_data,
                trade_markers=trade_markers,
                indicators=indicators,
                sp500_benchmark=sp500_benchmark,
                nasdaq_benchmark=nasdaq_benchmark,
                summary_stats=backtest_stats
            )
            
        except Exception as e:
            self.logger.error(f"차트 데이터 생성 실패: {str(e)}")
            raise

    async def _get_price_data(self, ticker, start_date, end_date) -> pd.DataFrame:
        """캐시 우선 가격 데이터 조회"""
        if self.data_repository:
            data = await self.data_repository.get_stock_data(ticker, start_date, end_date)
        else:
            data = await asyncio.to_thread(
                self.data_fetcher.fetch_stock_data,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )

        if data is None or data.empty:
            raise ValidationError(f"'{ticker}' 종목의 가격 데이터를 찾을 수 없습니다.")

        return data

    async def _generate_benchmark_data(self, ticker: str, start_date, end_date) -> List[BenchmarkPoint]:
        """벤치마크 데이터 생성 (S&P 500, NASDAQ 등)"""
        try:
            data = await self._get_price_data(ticker, start_date, end_date)
            benchmark_data = []

            for idx, row in data.iterrows():
                benchmark_data.append(BenchmarkPoint(
                    date=idx.strftime('%Y-%m-%d'),
                    close=safe_float(row['Close'])
                ))

            self.logger.info(f"{ticker} 벤치마크 데이터 생성 완료: {len(benchmark_data)} 포인트")
            return benchmark_data

        except Exception as e:
            self.logger.warning(f"{ticker} 벤치마크 데이터 생성 실패: {e}")
            return []
    
    def _generate_ohlc_data(self, data: pd.DataFrame) -> List[ChartDataPoint]:
        """OHLC 데이터 생성"""
        ohlc_data = []
        for idx, row in data.iterrows():
            ohlc_data.append(ChartDataPoint(
                timestamp=idx.isoformat(),
                date=idx.strftime('%Y-%m-%d'),
                open=safe_float(row['Open']),
                high=safe_float(row['High']),
                low=safe_float(row['Low']),
                close=safe_float(row['Close']),
                volume=safe_int(row.get('Volume', 0))
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
    
    def _generate_trade_markers(self, data: pd.DataFrame, strategy: str, trade_log: List[Dict[str, Any]]) -> List[TradeMarker]:
        """거래 마커 생성"""
        markers: List[TradeMarker] = []

        if not trade_log:
            if strategy == "buy_hold_strategy" and not data.empty:
                first_date = data.index[0]
                first_price = float(data['Close'].iloc[0])
                markers.append(TradeMarker(
                    timestamp=first_date.isoformat(),
                    date=first_date.strftime('%Y-%m-%d'),
                    price=first_price,
                    type="entry",
                    side="buy",
                    size=1.0
                ))
            return markers

        trades_df = pd.DataFrame(trade_log)
        if trades_df.empty:
            return markers

        def _parse_side(direction_value: Any, entry: bool = True) -> str:
            if isinstance(direction_value, (int, float)):
                if direction_value == 0:
                    return 'buy' if entry else 'sell'
                return 'buy' if direction_value > 0 else 'sell'
            direction = str(direction_value).lower()
            if 'long' in direction:
                return 'buy' if entry else 'sell'
            if 'short' in direction:
                return 'sell' if entry else 'buy'
            return 'buy' if entry else 'sell'

        for _, trade in trades_df.iterrows():
            entry_time = trade.get('EntryTime') or trade.get('Entry Date') or trade.get('EntryTimestamp')
            exit_time = trade.get('ExitTime') or trade.get('Exit Date') or trade.get('ExitTimestamp')

            entry_price = trade.get('EntryPrice') or trade.get('Entry Price')
            exit_price = trade.get('ExitPrice') or trade.get('Exit Price')
            size = trade.get('Size') or trade.get('Size (contracts)') or 1.0
            direction_val = trade.get('Direction') or trade.get('Trade Type')

            try:
                if pd.notna(entry_time):
                    entry_timestamp = pd.to_datetime(entry_time)
                    markers.append(TradeMarker(
                        timestamp=entry_timestamp.isoformat(),
                        date=entry_timestamp.strftime('%Y-%m-%d'),
                        price=float(entry_price) if pd.notna(entry_price) else float(data['Close'].iloc[0]),
                        type="entry",
                        side=_parse_side(direction_val, entry=True),
                        size=float(size) if pd.notna(size) else 1.0
                    ))
            except Exception:
                pass

            try:
                if pd.notna(exit_time):
                    exit_timestamp = pd.to_datetime(exit_time)
                    pnl_pct = trade.get('PnL (%)') or trade.get('PnLPct') or trade.get('ReturnPct')
                    markers.append(TradeMarker(
                        timestamp=exit_timestamp.isoformat(),
                        date=exit_timestamp.strftime('%Y-%m-%d'),
                        price=float(exit_price) if pd.notna(exit_price) else float(data['Close'].iloc[-1]),
                        type="exit",
                        side=_parse_side(direction_val, entry=False),
                        size=float(size) if pd.notna(size) else 1.0,
                        pnl_pct=float(pnl_pct) if pnl_pct is not None and not pd.isna(pnl_pct) else None
                    ))
            except Exception:
                pass

        return markers
    
    def _generate_indicators(self, data: pd.DataFrame, strategy: str, strategy_params: Dict[str, Any]) -> List[IndicatorData]:
        """기술 지표 데이터 생성 (Strategy Pattern)"""
        indicators = []

        # 전략에 해당하는 지표명 조회
        indicator_name = self.STRATEGY_TO_INDICATOR_MAP.get(strategy)
        if not indicator_name:
            self.logger.debug(f"지표 없음: 전략 '{strategy}'에 해당하는 지표가 없습니다")
            return indicators

        try:
            indicator_strategy = indicator_factory.get_indicator(indicator_name)

            result_data = indicator_strategy.calculate(data, strategy_params)

            indicators = self._convert_indicator_results(result_data, indicator_name)

        except Exception as e:
            self.logger.error(f"지표 계산 실패 ({indicator_name}): {str(e)}")

        return indicators

    def _convert_indicator_results(self, result_data: pd.DataFrame, indicator_name: str) -> List[IndicatorData]:
        """지표 계산 결과를 IndicatorData 형식으로 변환"""
        indicators = []
        color_map = {
            'SMA': ['#8884d8', '#82ca9d'],
            'RSI': ['#EC4899', '#EF4444', '#10B981'],
            'Bollinger Bands': ['#8884d8', '#6B7280', '#6B7280'],
            'MACD': ['#8B5CF6', '#F59E0B'],
            'EMA': ['#8B5CF6', '#F59E0B'],
        }

        # 지표별로 컬럼 추출
        if indicator_name == 'SMA':
            self._extract_sma_lines(result_data, indicators, color_map['SMA'])
        elif indicator_name == 'RSI':
            self._extract_rsi_lines(result_data, indicators, color_map['RSI'])
        elif indicator_name == 'Bollinger Bands':
            self._extract_bollinger_lines(result_data, indicators, color_map['Bollinger Bands'])
        elif indicator_name == 'MACD':
            self._extract_macd_lines(result_data, indicators, color_map['MACD'])
        elif indicator_name == 'EMA':
            self._extract_ema_lines(result_data, indicators, color_map['EMA'])

        return indicators

    def _extract_sma_lines(self, result_data: pd.DataFrame, indicators: List[IndicatorData], colors: List[str]):
        """SMA 라인 추출"""
        sma_columns = [col for col in result_data.columns if col.startswith('SMA_')]
        for idx, col in enumerate(sorted(sma_columns)):
            line_data = []
            for date_idx, val in result_data[col].items():
                if not pd.isna(val):
                    line_data.append({
                        "timestamp": date_idx.isoformat(),
                        "date": date_idx.strftime('%Y-%m-%d'),
                        "value": safe_float(val)
                    })
            if line_data:
                indicators.append(IndicatorData(
                    name=col,
                    type="line",
                    color=colors[idx % len(colors)],
                    data=line_data
                ))

    def _extract_rsi_lines(self, result_data: pd.DataFrame, indicators: List[IndicatorData], colors: List[str]):
        """RSI 라인 추출"""
        rsi_columns = [col for col in result_data.columns if col.startswith('RSI_')]
        for idx, col in enumerate(rsi_columns):
            if col.endswith('OVERBOUGHT') or col.endswith('OVERSOLD'):
                # Reference lines: 모든 데이터 포인트에 값 포함
                line_data = []
                for date_idx in result_data.index:
                    val = result_data.loc[date_idx, col]
                    line_data.append({
                        "timestamp": date_idx.isoformat(),
                        "date": date_idx.strftime('%Y-%m-%d'),
                        "value": float(val)
                    })
            else:
                # RSI 라인: NaN 제거
                line_data = []
                for date_idx, val in result_data[col].items():
                    if not pd.isna(val):
                        line_data.append({
                            "timestamp": date_idx.isoformat(),
                            "date": date_idx.strftime('%Y-%m-%d'),
                            "value": float(val)
                        })

            if line_data:
                color_idx = 2 if 'OVERBOUGHT' in col else (0 if 'OVERSOLD' not in col else 1)
                indicators.append(IndicatorData(
                    name=col,
                    type="line",
                    color=colors[color_idx % len(colors)],
                    data=line_data
                ))

    def _extract_bollinger_lines(self, result_data: pd.DataFrame, indicators: List[IndicatorData], colors: List[str]):
        """Bollinger Bands 라인 추출"""
        bb_mapping = {
            'BB_MIDDLE': (colors[0], 0),
            'BB_UPPER': (colors[1], 1),
            'BB_LOWER': (colors[2], 2),
        }

        for col_name, (color, _) in bb_mapping.items():
            if col_name in result_data.columns:
                line_data = []
                for date_idx, val in result_data[col_name].items():
                    if not pd.isna(val):
                        line_data.append({
                            "timestamp": date_idx.isoformat(),
                            "date": date_idx.strftime('%Y-%m-%d'),
                            "value": float(val)
                        })
                if line_data:
                    indicators.append(IndicatorData(
                        name=col_name,
                        type="line",
                        color=color,
                        data=line_data
                    ))

    def _extract_macd_lines(self, result_data: pd.DataFrame, indicators: List[IndicatorData], colors: List[str]):
        """MACD 라인 추출"""
        macd_mapping = {
            'MACD': (colors[0], 0),
            'MACD_SIGNAL': (colors[1], 1),
            'MACD_HISTOGRAM': (colors[0], 0),
        }

        for col_name, (color, _) in macd_mapping.items():
            if col_name in result_data.columns:
                line_data = []
                for date_idx, val in result_data[col_name].items():
                    if not pd.isna(val):
                        line_data.append({
                            "timestamp": date_idx.isoformat(),
                            "date": date_idx.strftime('%Y-%m-%d'),
                            "value": float(val)
                        })
                if line_data:
                    indicators.append(IndicatorData(
                        name=col_name,
                        type="line",
                        color=color,
                        data=line_data
                    ))

    def _extract_ema_lines(self, result_data: pd.DataFrame, indicators: List[IndicatorData], colors: List[str]):
        """EMA 라인 추출"""
        ema_columns = [col for col in result_data.columns if col.startswith('EMA_')]
        for idx, col in enumerate(sorted(ema_columns)):
            line_data = []
            for date_idx, val in result_data[col].items():
                if not pd.isna(val):
                    line_data.append({
                        "timestamp": date_idx.isoformat(),
                        "date": date_idx.strftime('%Y-%m-%d'),
                        "value": safe_float(val)
                    })
            if line_data:
                indicators.append(IndicatorData(
                    name=col,
                    type="line",
                    color=colors[idx % len(colors)],
                    data=line_data
                ))

    def _calculate_backtest_stats(self, data: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """백테스트 통계 계산"""
        initial_price = float(data['Close'].iloc[0])
        final_price = float(data['Close'].iloc[-1])
        
        total_return_pct = ((final_price / initial_price) - 1) * 100
        final_equity = initial_cash * (final_price / initial_price)
        max_drawdown_pct = 0.0
        
        return {
            "total_return_pct": total_return_pct,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": max_drawdown_pct,
            "total_trades": 1,  # Buy & Hold은 1번 거래
            "win_rate_pct": 100.0 if total_return_pct > 0 else 0.0,
            "profit_factor": 1.0 if total_return_pct > 0 else 0.0,
            # 추가 정보
            "final_equity": final_equity,
            "volatility": float(data['Close'].pct_change().std() * 100) if len(data) > 1 else 0.0
        }


# 글로벌 인스턴스
chart_data_service = ChartDataService()
