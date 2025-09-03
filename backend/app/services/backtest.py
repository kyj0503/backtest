import yfinance as yf
import pandas as pd
import warnings
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple, Generator
from backtesting import Backtest
from requests.exceptions import RequestException
import time
from datetime import datetime, timedelta
import random
import numpy as np
import asyncio

from app.core.exceptions import BacktestError
from app.core.config import settings
from app.utils.serializers import recursive_serialize
from strategies.sma_cross import SmaCross
from app.models.schemas import BacktestRequest

class BacktestService:

    @staticmethod
    @contextmanager
    def capture_warnings() -> Generator[List[str], None, None]:
        """경고 메시지를 캡처하는 컨텍스트 매니저"""
        warning_messages = []
        original_handler = warnings.showwarning
        
        def warning_handler(message, category, filename, lineno, file=None, line=None):
            warning_messages.append(str(message))
        
        warnings.showwarning = warning_handler
        try:
            yield warning_messages
        finally:
            warnings.showwarning = original_handler

    @staticmethod
    def get_retry_delay(attempt: int) -> float:
        """지수 백오프와 지터를 적용한 재시도 대기 시간 계산"""
        delay = min(BacktestService.BASE_DELAY * (2 ** attempt), BacktestService.MAX_DELAY)
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter

    @staticmethod
    def download_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """주식 데이터 다운로드 (캐시 시스템 적용)"""
        # 캐시에서 데이터 조회 시도
        # 캐시에서 데이터 조회 시도
        print(f"Downloading data for {symbol} from yfinance")
        
        # 캐시에 없는 경우 yfinance에서 다운로드
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start > datetime.now():
            raise BacktestError("시작 날짜는 현재 날짜보다 이후일 수 없습니다.", "INVALID_DATE")
        
        if end > datetime.now():
            end = datetime.now()
            end_date = end.strftime('%Y-%m-%d')
        
        last_error = None
        for attempt in range(BacktestService.MAX_RETRIES):
            try:
                if attempt > 0:
                    period_days = (end - start).days
                    if period_days > 30:
                        adjusted_end = start + timedelta(days=period_days // 2)
                        print(f"Retry {attempt + 1}/{BacktestService.MAX_RETRIES}: "
                              f"Downloading {symbol} data with shorter period...")
                        data = yf.download(
                            symbol,
                            start=start_date,
                            end=adjusted_end.strftime('%Y-%m-%d'),
                            progress=False,
                            interval="1d"
                        )
                    else:
                        data = yf.download(
                            symbol,
                            start=start_date,
                            end=end_date,
                            progress=False,
                            interval="1d"
                        )
                else:
                    data = yf.download(
                        symbol,
                        start=start_date,
                        end=end_date,
                        progress=False,
                        interval="1d"
                    )
                
                if not data.empty:
                    if len(data) >= BacktestService.MIN_DATA_POINTS:
                        # 데이터를 캐시에 저장
                        print(f"Data for {symbol} downloaded successfully.")
                        return data
                    elif attempt < BacktestService.MAX_RETRIES - 1:
                        print(f"Data points insufficient ({len(data)}), retrying...")
                        continue
                    else:
                        raise BacktestError(
                            f"충분한 데이터 포인트를 얻을 수 없습니다. (현재: {len(data)}개, 필요: {BacktestService.MIN_DATA_POINTS}개)",
                            "INSUFFICIENT_DATA"
                        )
                    
            except Exception as e:
                last_error = e
                if "Too Many Requests" in str(e):
                    if attempt < BacktestService.MAX_RETRIES - 1:
                        delay = BacktestService.get_retry_delay(attempt)
                        print(f"Rate limit hit, waiting {delay:.1f} seconds...")
                        time.sleep(delay)
                        continue
                elif "Symbol may be delisted" in str(e):
                    raise BacktestError(f"'{symbol}' 종목이 상장폐지되었거나 존재하지 않습니다.", "INVALID_SYMBOL")
                raise BacktestError(f"데이터 다운로드 중 오류 발생: {str(e)}", "DOWNLOAD_ERROR")
        
        if last_error:
            if "Too Many Requests" in str(last_error):
                raise BacktestError(
                    "yfinance API 요청 제한에 도달했습니다. 30초 후 다시 시도해주세요.",
                    "RATE_LIMIT_ERROR"
                )
            raise BacktestError(f"데이터 다운로드 중 오류 발생: {str(last_error)}", "DOWNLOAD_ERROR")
        
        raise BacktestError(f"'{symbol}' 종목에 대한 데이터를 가져올 수 없습니다.", "NO_DATA")

    @staticmethod
    def format_response(stats: Any, warning_messages: List[str]) -> Dict[str, Any]:
        """백테스트 결과 포맷팅"""
        # 기본 통계 데이터
        stats_dict = stats._asdict() if hasattr(stats, '_asdict') else dict(stats)
        
        # 거래 데이터 추가
        if hasattr(stats, '_trades'):
            trades_df = stats._trades
            trades_dict = {
                'trades': trades_df.to_dict('records') if not trades_df.empty else [],
                'total_trades': len(trades_df),
                'win_rate': stats_dict.get('Win Rate [%]', 0),
                'profit_factor': stats_dict.get('Profit Factor', 0),
                'expectancy': stats_dict.get('Expectancy [%]', 0)
            }
            stats_dict['trades'] = trades_dict
        
        # 자본금 곡선 데이터 추가
        if hasattr(stats, '_equity_curve'):
            equity_df = stats._equity_curve
            equity_dict = {
                'equity_curve': equity_df['Equity'].to_dict(),
                'drawdown': equity_df['DrawdownPct'].to_dict()
            }
            stats_dict['equity'] = equity_dict
        
        response = {
            "status": "success",
            "data": recursive_serialize(stats_dict)
        }
        
        if warning_messages:
            response["warnings"] = warning_messages
            
        return response

    @staticmethod
    def run_backtest(
        symbol: str,
        start_date: str,
        end_date: str,
        cash: float,
        commission: float,
        strategy_params: dict
    ) -> Dict[str, Any]:
        """백테스트 실행"""
        try:
            # 데이터 다운로드 및 검증
            data = BacktestService.download_data(symbol, start_date, end_date)
            BacktestService.validate_data(data, symbol)
            data = BacktestService.prepare_data(data)

            # 전략 파라미터 설정
            strategy_class = SmaCross
            if strategy_params:
                # 클래스 변수 업데이트
                for key, value in strategy_params.items():
                    setattr(strategy_class, key, value)

            # 백테스트 실행 및 결과 처리
            with BacktestService.capture_warnings() as warning_messages:
                bt = Backtest(
                    data,
                    strategy_class,
                    cash=cash,
                    commission=commission,
                    trade_on_close=False,  # 다음 봉 시가에 거래
                    exclusive_orders=True  # 중복 주문 방지
                )
                stats = bt.run()
                return BacktestService.format_response(stats, warning_messages)

        except BacktestError:
            raise
        except Exception as e:
            raise BacktestError(f"예상치 못한 오류가 발생했습니다: {str(e)}", "UNKNOWN_ERROR")

    @staticmethod
    def safe_float(value):
        """안전하게 float 값으로 변환"""
        if isinstance(value, (np.ndarray, list)):
            return float(value[0]) if len(value) > 0 else 0.0
        return float(value)
    
    @staticmethod
    def safe_int(value):
        """안전하게 int 값으로 변환"""
        if isinstance(value, (np.ndarray, list)):
            return int(value[0]) if len(value) > 0 else 0
        return int(value)

    async def run_backtest(self, request: BacktestRequest) -> Dict:
        """
        백테스트를 실행합니다.
        
        Parameters
        ----------
        request : BacktestRequest
            백테스트 요청 파라미터
            
        Returns
        -------
        Dict
            백테스트 결과
        """
        try:
            # 데이터 다운로드
            data = await self.download_data(
                request.symbol,
                request.start_date,
                request.end_date
            )
            
            # 전략 클래스 설정
            SmaCross.sma_short = request.strategy.sma_short
            SmaCross.sma_long = request.strategy.sma_long
            SmaCross.position_size = request.strategy.position_size
            
            # 백테스트 실행
            from backtesting import Backtest
            bt = Backtest(
                data,
                SmaCross,
                cash=request.cash,
                commission=request.commission,
                trade_on_close=True
            )
            
            # 결과 계산
            result = bt.run()
            
            # 거래 데이터 처리
            trades = []
            if hasattr(result, '_trades') and result._trades is not None:
                for trade in result._trades:
                    if hasattr(trade, 'size'):
                        try:
                            trade_data = {
                                "Size": abs(self.safe_float(trade.size)),
                                "EntryBar": self.safe_int(trade.entry_bar),
                                "ExitBar": self.safe_int(trade.exit_bar),
                                "EntryPrice": self.safe_float(trade.entry_price),
                                "ExitPrice": self.safe_float(trade.exit_price),
                                "PnL": self.safe_float(trade.pl),
                                "ReturnPct": self.safe_float(trade.pl_pct),
                                "EntryTime": trade.entry_time.strftime("%Y-%m-%d") if hasattr(trade.entry_time, 'strftime') else str(trade.entry_time),
                                "ExitTime": trade.exit_time.strftime("%Y-%m-%d") if hasattr(trade.exit_time, 'strftime') else str(trade.exit_time),
                                "Duration": str(trade.exit_time - trade.entry_time) if hasattr(trade, 'exit_time') and hasattr(trade, 'entry_time') else "N/A"
                            }
                            trades.append(trade_data)
                        except (ValueError, TypeError, IndexError) as e:
                            print(f"Warning: Skipping trade due to conversion error: {str(e)}")
                            continue
            
            # 결과 포맷팅
            try:
                response_data = {
                    "status": "success",
                    "data": {
                        "Start": result["Start"].strftime("%Y-%m-%d") if hasattr(result["Start"], 'strftime') else str(result["Start"]),
                        "End": result["End"].strftime("%Y-%m-%d") if hasattr(result["End"], 'strftime') else str(result["End"]),
                        "Duration": str(result["Duration"]),
                        "Exposure Time [%]": self.safe_float(result["Exposure Time [%]"]),
                        "Equity Final [$]": self.safe_float(result["Equity Final [$]"]),
                        "Equity Peak [$]": self.safe_float(result["Equity Peak [$]"]),
                        "Return [%]": self.safe_float(result["Return [%]"]),
                        "Buy & Hold Return [%]": self.safe_float(result["Buy & Hold Return [%]"]),
                        "Max. Drawdown [%]": self.safe_float(result["Max. Drawdown [%]"]),
                        "Avg. Drawdown [%]": self.safe_float(result["Avg. Drawdown [%]"]),
                        "Max. Drawdown Duration": str(result["Max. Drawdown Duration"]),
                        "Avg. Drawdown Duration": str(result["Avg. Drawdown Duration"]),
                        "# Trades": self.safe_int(result["# Trades"]),
                        "Win Rate [%]": self.safe_float(result["Win Rate [%]"]),
                        "Best Trade [%]": self.safe_float(result["Best Trade [%]"]),
                        "Worst Trade [%]": self.safe_float(result["Worst Trade [%]"]),
                        "Avg. Trade [%]": self.safe_float(result["Avg. Trade [%]"]),
                        "Max. Trade Duration": str(result["Max. Trade Duration"]),
                        "Avg. Trade Duration": str(result["Avg. Trade Duration"]),
                        "Profit Factor": self.safe_float(result["Profit Factor"]),
                        "Expectancy [%]": self.safe_float(result["Expectancy [%]"]),
                        "trades": {
                            "trades": trades,
                            "total_trades": self.safe_int(result["# Trades"]),
                            "win_rate": self.safe_float(result["Win Rate [%]"]),
                            "profit_factor": self.safe_float(result["Profit Factor"]),
                            "expectancy": self.safe_float(result["Expectancy [%]"])
                        }
                    }
                }
                
                # 자본금 곡선 데이터 처리
                if hasattr(result, "_equity_curve") and hasattr(result, "_drawdown"):
                    equity_curve = {}
                    drawdown = {}
                    
                    for date, value in zip(result["_equity_curve"].index, result["_equity_curve"].values):
                        try:
                            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
                            equity_curve[date_str] = self.safe_float(value)
                        except (ValueError, TypeError, IndexError) as e:
                            print(f"Warning: Skipping equity curve data point due to conversion error: {str(e)}")
                            continue
                    
                    for date, value in zip(result["_drawdown"].index, result["_drawdown"].values):
                        try:
                            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
                            drawdown[date_str] = self.safe_float(value)
                        except (ValueError, TypeError, IndexError) as e:
                            print(f"Warning: Skipping drawdown data point due to conversion error: {str(e)}")
                            continue
                    
                    response_data["data"]["equity"] = {
                        "equity_curve": equity_curve,
                        "drawdown": drawdown
                    }
                
                return response_data
                
            except Exception as e:
                print(f"Error formatting response: {str(e)}")
                raise BacktestError(f"결과 데이터 처리 중 오류 발생: {str(e)}", "DATA_PROCESSING_ERROR")
            
        except Exception as e:
            raise BacktestError(str(e), "BACKTEST_ERROR")

    async def download_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        max_retries: int = 5,
        base_delay: int = 5,
        max_delay: int = 30
    ) -> pd.DataFrame:
        """
        주식 데이터를 다운로드합니다.
        
        Parameters
        ----------
        symbol : str
            주식 심볼
        start_date : str
            시작 날짜 (YYYY-MM-DD)
        end_date : str
            종료 날짜 (YYYY-MM-DD)
        max_retries : int, optional
            최대 재시도 횟수 (기본값: 5)
        base_delay : int, optional
            기본 대기 시간(초) (기본값: 5)
        max_delay : int, optional
            최대 대기 시간(초) (기본값: 30)
            
        Returns
        -------
        pd.DataFrame
            OHLCV 데이터 (컬럼명: Open, High, Low, Close, Volume)
        """
        # 날짜 검증
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if end < start:
                raise BacktestError(
                    "종료 날짜는 시작 날짜보다 이후여야 합니다.",
                    "INVALID_DATE_RANGE"
                )
            if (end - start).days > 365 * 5:  # 5년 제한
                raise BacktestError(
                    "백테스트 기간은 최대 5년으로 제한됩니다.",
                    "INVALID_DATE_RANGE"
                )
        except ValueError:
            raise BacktestError(
                "날짜는 YYYY-MM-DD 형식이어야 합니다.",
                "INVALID_DATE_FORMAT"
            )
        
        # 데이터 다운로드 시도
        for attempt in range(max_retries):
            try:
                # yfinance로 데이터 다운로드
                ticker = yf.Ticker(symbol)
                hist = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval="1d"
                )
                
                if hist.empty:
                    raise BacktestError(
                        f"'{symbol}' 종목에 대한 데이터가 존재하지 않습니다.",
                        "NO_DATA"
                    )
                
                # 데이터 검증
                if len(hist) < 50:  # 최소 50일 데이터 필요
                    raise BacktestError(
                        f"'{symbol}' 종목의 데이터가 충분하지 않습니다. (최소 50일 필요)",
                        "INSUFFICIENT_DATA"
                    )
                
                # 컬럼명 표준화 (Backtesting.py 요구사항에 맞춤)
                hist.columns = [col.capitalize() for col in hist.columns]
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # Volume이 없는 경우 0으로 채우기
                if 'Volume' not in hist.columns:
                    hist['Volume'] = 0
                
                # 필요한 컬럼만 선택하고 순서 맞추기
                hist = hist[required_columns].copy()
                
                # 결측치 처리 (deprecated된 method 파라미터 대신 ffill/bfill 사용)
                hist = hist.ffill().bfill()
                
                return hist
                
            except Exception as e:
                if "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        # 지수 백오프와 지터를 적용한 대기 시간 계산
                        delay = min(base_delay * (2 ** attempt) + np.random.uniform(0, 1), max_delay)
                        await asyncio.sleep(delay)
                        # 종료 날짜를 하루 앞당김
                        end = end - timedelta(days=1)
                        end_date = end.strftime('%Y-%m-%d')
                        continue
                    else:
                        raise BacktestError(
                            "데이터 다운로드 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.",
                            "RATE_LIMIT_ERROR"
                        )
                elif "Symbol may be delisted" in str(e):
                    raise BacktestError(
                        f"'{symbol}' 종목이 상장폐지되었거나 존재하지 않습니다.",
                        "INVALID_SYMBOL"
                    )
                else:
                    raise BacktestError(
                        f"데이터 다운로드 중 오류 발생: {str(e)}",
                        "DATA_FETCH_ERROR"
                    )
        
        raise BacktestError(
            "데이터를 다운로드할 수 없습니다.",
            "DATA_FETCH_ERROR"
        ) 