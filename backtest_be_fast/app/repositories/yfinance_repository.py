"""yfinance 데이터 MySQL 저장 리포지토리

yfinance API로 수집한 주가 데이터를 MySQL DB에 저장하고 조회합니다.
DB 우선 조회 전략으로 외부 API 호출을 최소화합니다.
"""
import json
import logging
import time
import email.utils
from typing import Optional, Union, List, Dict, Any, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
import pandas as pd
from datetime import datetime, date, timedelta
from app.utils.data_fetcher import data_fetcher
from app.services.database.connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class YFinanceRepository:
    """
    yfinance 데이터베이스 리포지토리 클래스
    """
    
    def __init__(self):
        self.logger = logger
        self.data_fetcher = data_fetcher

    def _get_engine(self) -> Engine:
        """
        데이터베이스 Engine을 가져옵니다.
        """
        return DatabaseConnectionManager.get_engine()

    def _retry_on_deadlock(self, func, max_retries=3, delay=1.0, *args, **kwargs):
        """
        데드락 또는 일시적 DB 에러 발생 시 재시도하는 헬퍼
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                # Deadlock found when trying to get lock; try restarting transaction
                if '1213' in str(e) or 'Deadlock' in str(e) or 'Lock wait timeout' in str(e):
                    self.logger.warning(f"DB Deadlock/Timeout detected (Attempt {attempt+1}/{max_retries}): {e}")
                    last_error = e
                    time.sleep(delay * (attempt + 1))  # Exponential backoff-ish
                else:
                    raise e
            except Exception as e:
                raise e
        
        self.logger.error(f"DB Operation failed after {max_retries} attempts: {last_error}")
        if last_error:
            raise last_error
        raise RuntimeError(f"DB Operation failed after {max_retries} attempts, but no exception was captured.")

    def _save_stock_metadata(self, conn, ticker: str) -> int:
        """stocks 테이블에 메타데이터 저장 (Upsert)"""
        # ensure stock exists
        info = {}
        try:
            info = self.data_fetcher.fetch_ticker_info(ticker)
        except Exception:
            self.logger.warning(f"{ticker} info 조회 실패/누락, 기본값으로 진행")
        
        # DB에서 기존 last_handled_split 보존
        existing_split = None
        try:
            existing_row = conn.execute(text("SELECT info_json FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
            if existing_row and existing_row[0]:
                existing_json = json.loads(existing_row[0])
                existing_split = existing_json.get('last_handled_split')
        except Exception as e:
            self.logger.debug(f"Failed to fetch existing last_handled_split for {ticker}: {e}")
        
        # 기존 last_handled_split을 새 info에 추가 (덮어쓰지 않도록)
        if existing_split and 'last_handled_split' not in info:
            info['last_handled_split'] = existing_split

        # 분할 정보 추출
        last_split_date_str = info.get('last_split_date')
        last_split_ratio = info.get('last_split_ratio')
        splits_updated_at = datetime.utcnow()

        # insert or update stocks
        insert_stock = text(
            """
            INSERT INTO stocks (
                ticker, name, exchange, sector, industry, summary, info_json, last_info_update,
                last_split_date, last_split_ratio, splits_updated_at
            )
            VALUES (
                :ticker, :name, :exchange, :sector, :industry, :summary, :info_json, :now,
                :last_split_date, :last_split_ratio, :splits_updated_at
            )
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                exchange=VALUES(exchange),
                sector=VALUES(sector),
                industry=VALUES(industry),
                summary=VALUES(summary),
                info_json=VALUES(info_json),
                last_info_update=VALUES(last_info_update),
                last_split_date=VALUES(last_split_date),
                last_split_ratio=VALUES(last_split_ratio),
                splits_updated_at=VALUES(splits_updated_at)
            """
        )
        now = datetime.utcnow()
        conn.execute(insert_stock, {
            "ticker": ticker,
            "name": info.get("company_name"),
            "exchange": info.get("exchange"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "summary": None,
            "info_json": json.dumps(info),
            "now": now,
            "last_split_date": last_split_date_str,
            "last_split_ratio": last_split_ratio,
            "splits_updated_at": splits_updated_at
        })
        
        # Return stock_id for chaining
        stock_id_row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
        if not stock_id_row:
            raise RuntimeError(f"{ticker} stock_id 생성/조회 실패")
        return stock_id_row[0]

    def _save_daily_prices(self, conn, stock_id: int, df: pd.DataFrame) -> int:
        """daily_prices 테이블에 가격 데이터 배치 저장 (Upsert)"""
        rows = []
        df_proc = df.copy()
        
        # Date 컬럼 처리
        if 'Date' in df_proc.columns:
            df_proc['date'] = pd.to_datetime(df_proc['Date']).dt.date
        else:
            df_proc = df_proc.reset_index()
            # index 이름이 없거나 Date가 아닐 수 있으므로 첫번째 컬럼을 날짜로 가정
            df_proc['date'] = pd.to_datetime(df_proc.iloc[:, 0]).dt.date

        for _, r in df_proc.iterrows():
            o = None if pd.isna(r.get('Open')) else float(r.get('Open'))
            h = None if pd.isna(r.get('High')) else float(r.get('High'))
            l = None if pd.isna(r.get('Low')) else float(r.get('Low'))
            c = None if pd.isna(r.get('Close')) else float(r.get('Close'))
            
            ac = None
            for col in ['Adj Close', 'AdjClose', 'Adj_Close']:
                if col in r:
                    val = r.get(col)
                    if not pd.isna(val):
                        ac = float(val)
                        break
            
            vol = 0 if pd.isna(r.get('Volume')) else int(r.get('Volume'))
            
            rows.append({
                'stock_id': stock_id,
                'date': r['date'].isoformat(),
                'open': o,
                'high': h,
                'low': l,
                'close': c,
                'adj_close': ac,
                'volume': vol
            })

        if rows:
            insert_stmt = text(
                """
                INSERT INTO daily_prices (stock_id, date, open, high, low, close, adj_close, volume)
                VALUES (:stock_id, :date, :open, :high, :low, :close, :adj_close, :volume)
                ON DUPLICATE KEY UPDATE 
                    open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close), 
                    adj_close=VALUES(adj_close), volume=VALUES(volume)
                """
            )
            chunk_size = 500
            for i in range(0, len(rows), chunk_size):
                batch = rows[i:i+chunk_size]
                conn.execute(insert_stmt, batch)
                
        return len(rows)

    def save_ticker_data(self, ticker: str, df: pd.DataFrame) -> int:
        """stocks 테이블에 티커 등록 및 daily_prices에 행을 upsert 합니다."""
        def _transactional_save():
            engine = self._get_engine()
            with engine.begin() as conn:  # Context manager handles commit/rollback automatically
                # 1. Metadata 저장
                stock_id = self._save_stock_metadata(conn, ticker)
                
                # 2. Price 저장
                saved_count = self._save_daily_prices(conn, stock_id, df)
                return saved_count

        try:
            # Retry logic apply
            return self._retry_on_deadlock(_transactional_save)
        except Exception as e:
            self.logger.exception(f"save_ticker_data 실패: {ticker}")
            raise

    def load_ticker_data(self, ticker: str, start_date: Optional[Union[str, date]] = None, end_date: Optional[Union[str, date]] = None, max_retries: int = 3, retry_delay: float = 2.0) -> pd.DataFrame:
        """DB에서 ticker의 daily_prices를 조회해 pandas DataFrame으로 반환합니다."""
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"[시도 {attempt}/{max_retries}] {ticker} 데이터 로드 중... ({start_date} ~ {end_date})")
                
                # 실제 데이터 로드 로직
                df = self._load_ticker_data_internal(ticker, start_date, end_date)
                
                if df is not None and not df.empty:
                    self.logger.info(f"[성공] {ticker} 데이터 로드 완료: {len(df)}행 (시도 {attempt}회)")
                    return df
                else:
                    self.logger.warning(f"[시도 {attempt}/{max_retries}] {ticker} 데이터가 비어있음")
                    last_exception = ValueError(f"{ticker} 데이터가 비어있습니다")
                    
            except Exception as e:
                self.logger.warning(f"[시도 {attempt}/{max_retries}] {ticker} 데이터 로드 실패: {str(e)}")
                last_exception = e
            
            # 마지막 시도가 아니면 대기 후 재시도
            if attempt < max_retries:
                wait_time = retry_delay * attempt  # 점진적 증가 (2초, 4초, 6초...)
                self.logger.info(f"[재시도 대기] {wait_time}초 후 {ticker} 데이터 재시도...")
                time.sleep(wait_time)
        
        # 모든 재시도 실패
        error_msg = f"[실패] {ticker} 데이터 로드 실패 (총 {max_retries}회 시도)"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        self.logger.error(error_msg)
        raise ValueError(error_msg)

    def _update_ticker_info(self, ticker: str, stock_id: int, info: dict) -> None:
        """stocks 테이블의 info_json을 업데이트합니다 (쓰기 전용)."""
        engine = self._get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE stocks SET info_json = :info WHERE id = :id"),
                {"info": json.dumps(info), "id": stock_id}
            )

    def get_ticker_info_from_db(self, ticker: str) -> Dict[str, Any]:
        """
        DB에서 티커의 메타데이터 조회
        """
        engine = self._get_engine()
        default_info = {
            'symbol': ticker.upper(),
            'currency': 'USD',
            'company_name': ticker.upper(),
            'exchange': 'Unknown',
            'first_trade_date': None
        }
        try:
            ticker = ticker.upper()
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT id, info_json FROM stocks WHERE ticker = :t"),
                    {"t": ticker}
                ).fetchone()

                if row and row[1]:
                    try:
                        stock_id = row[0]
                        info = json.loads(row[1])

                        # 상장일이 없으면 Yahoo Finance에서 가져와 업데이트
                        if not info.get('first_trade_date'):
                            self.logger.info(f"{ticker}: DB에 상장일 없음 - Yahoo Finance에서 조회")
                            try:
                                fresh_info = self.data_fetcher.fetch_ticker_info(ticker)
                                if fresh_info.get('first_trade_date'):
                                    info['first_trade_date'] = fresh_info['first_trade_date']
                                    self._update_ticker_info(ticker, stock_id, info)
                                    self.logger.info(f"{ticker}: 상장일 업데이트 완료 - {info['first_trade_date']}")
                            except Exception as e:
                                self.logger.warning(f"{ticker}: 상장일 조회 실패 - {e}")

                        return {
                            'symbol': ticker,
                            'currency': info.get('currency', 'USD'),
                            'company_name': info.get('company_name', ticker),
                            'exchange': info.get('exchange', 'Unknown'),
                            'first_trade_date': info.get('first_trade_date', None)
                        }
                    except Exception as e:
                        self.logger.warning(f"info_json 파싱 실패: {ticker} - {e}")

                return default_info
        except Exception as e:
            self.logger.error(f"티커 정보 조회 실패: {ticker} - {e}")
            return default_info

    def get_ticker_info_batch_from_db(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        DB에서 여러 티커의 메타데이터를 배치로 조회 (N+1 쿼리 최적화)
        """
        if not tickers:
            return {}

        engine = self._get_engine()
        try:
            # 대문자로 변환
            upper_tickers = [t.upper() for t in tickers]

            with engine.connect() as conn:
                # IN 절을 사용한 배치 조회
                placeholders = ', '.join([f':t{i}' for i in range(len(upper_tickers))])
                query = text(f"SELECT ticker, info_json FROM stocks WHERE ticker IN ({placeholders})")
                params = {f't{i}': ticker for i, ticker in enumerate(upper_tickers)}

                rows = conn.execute(query, params).fetchall()

            # 결과를 딕셔너리로 변환
            result = {}
            found_tickers = set()
            missing_listing_dates = []

            for row in rows:
                ticker = row[0]
                found_tickers.add(ticker)

                if row[1]:
                    try:
                        info = json.loads(row[1])
                        first_trade_date = info.get('first_trade_date', None)

                        # 상장일이 없으면 경고 리스트에 추가
                        if not first_trade_date:
                            missing_listing_dates.append(ticker)

                        result[ticker] = {
                            'symbol': ticker,
                            'currency': info.get('currency', 'USD'),
                            'company_name': info.get('company_name', ticker),
                            'exchange': info.get('exchange', 'Unknown'),
                            'first_trade_date': first_trade_date
                        }
                    except Exception as e:
                        self.logger.warning(f"info_json 파싱 실패: {ticker} - {e}")
                        result[ticker] = {
                            'symbol': ticker,
                            'currency': 'USD',
                            'company_name': ticker,
                            'exchange': 'Unknown',
                            'first_trade_date': None
                        }
                else:
                    result[ticker] = {
                        'symbol': ticker,
                        'currency': 'USD',
                        'company_name': ticker,
                        'exchange': 'Unknown',
                        'first_trade_date': None
                    }

            # 상장일이 없는 종목이 있으면 경고
            if missing_listing_dates:
                self.logger.warning(
                    f"상장일 정보가 없는 종목: {', '.join(missing_listing_dates)}. "
                    f"'docker exec -it backtest-be-fast-dev python scripts/update_ticker_listing_dates.py' "
                    f"실행으로 업데이트할 수 있습니다."
                )

            # DB에 없는 티커들은 기본값 추가
            for ticker in upper_tickers:
                if ticker not in found_tickers:
                    result[ticker] = {
                        'symbol': ticker,
                        'currency': 'USD',
                        'company_name': ticker,
                        'exchange': 'Unknown',
                        'first_trade_date': None
                    }

            return result

        except Exception as e:
            self.logger.error(f"배치 티커 정보 조회 실패: {e}")
            # 실패 시 기본값으로 채운 딕셔너리 반환
            return {
                ticker.upper(): {
                    'symbol': ticker.upper(),
                    'currency': 'USD',
                    'company_name': ticker.upper(),
                    'exchange': 'Unknown'
                }
                for ticker in tickers
            }

    def _normalize_date_params(self, start_date: Optional[Union[str, date, datetime, pd.Timestamp]], end_date: Optional[Union[str, date, datetime, pd.Timestamp]]) -> Tuple[date, date]:
        """
        날짜 매개변수를 정규화하고 기본값을 설정합니다.
        """
        def _to_date(d):
            """다양한 날짜 형식을 date 객체로 변환"""
            if d is None:
                return None
            if isinstance(d, str):
                return datetime.strptime(d, "%Y-%m-%d").date()
            if isinstance(d, (pd.Timestamp, datetime)):
                return pd.to_datetime(d).date()
            if isinstance(d, date):
                return d
            return pd.to_datetime(d).date()

        start_date = _to_date(start_date)
        end_date = _to_date(end_date)

        # 기본값 설정: 최근 1년
        if end_date is None and start_date is None:
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
        elif start_date is None:
            end_date = end_date or date.today()
            start_date = end_date - timedelta(days=365)
        elif end_date is None:
            end_date = date.today()

        return start_date, end_date

    def _ensure_stock_exists(self, conn, engine: Engine, ticker: str, start_date: date, end_date: date) -> tuple[int, any]:
        """
        stock_id를 조회하고, DB에 없으면 yfinance에서 데이터를 가져와 저장합니다.
        """
        row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()

        if not row:
            self.logger.info(f"티커 '{ticker}'이 DB에 없음 — yfinance에서 수집 시도")
            try:
                df_new = self.data_fetcher.fetch_stock_data(ticker, start_date, end_date, use_cache=True)
                if df_new is None or df_new.empty:
                    raise ValueError("yfinance에서 유효한 데이터가 반환되지 않았습니다.")
                self.save_ticker_data(ticker, df_new)

                # 데이터 저장 후 커넥션을 닫고 새로 연결 - 트랜잭션 격리 문제 방지
                conn.close()
                conn = engine.connect()
            except Exception as e:
                self.logger.exception("티커가 DB에 없고 yfinance 수집 실패")
                raise ValueError(f"티커 '{ticker}'이(가) DB에 없고 yfinance 수집 실패: {e}")

            row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
            if not row:
                raise ValueError(f"티커 '{ticker}'을(를) DB에 추가할 수 없습니다.")

        stock_id = row[0]
        return stock_id, conn

    def _get_date_coverage(self, conn, stock_id: int) -> tuple[Optional[date], Optional[date]]:
        """
        DB에 저장된 주가 데이터의 날짜 범위를 조회합니다.
        """
        date_row = conn.execute(
            text("SELECT MIN(date), MAX(date) FROM daily_prices WHERE stock_id = :sid"),
            {"sid": stock_id}
        ).fetchone()

        db_min, db_max = None, None
        if date_row and date_row[0] is not None:
            db_min = pd.to_datetime(date_row[0]).date()
            db_max = pd.to_datetime(date_row[1]).date()

        return db_min, db_max

    def _fetch_and_save_missing_data(
        self,
        conn,
        engine: Engine,
        ticker: str,
        start_date: date,
        end_date: date,
        db_min: Optional[date],
        db_max: Optional[date]
    ) -> any:
        """
        요청 범위와 DB 범위를 비교하여 누락된 데이터를 yfinance에서 가져와 저장합니다.
        """
        # 누락된 구간 계산
        missing_ranges = []
        if db_min is None:
            # DB에 데이터가 전혀 없음 -> 요청 범위 전체를 가져와야 함
            missing_ranges.append((start_date, end_date))
        else:
            # 시작 날짜가 DB 범위보다 이전인 경우
            if start_date < db_min:
                missing_ranges.append((start_date, db_min - timedelta(days=1)))
            # 종료 날짜가 DB 범위보다 이후인 경우
            if end_date > db_max:
                missing_ranges.append((db_max + timedelta(days=1), end_date))

        # 누락된 구간이 없으면 그대로 반환
        if not missing_ranges:
            return conn

        # 전략 1: 통합 fetch (여러 구간을 하나로 합쳐서 패딩 추가)
        if self.data_fetcher is not None:
            min_start = min(s for s, _ in missing_ranges if s is not None)
            max_end = max(e for _, e in missing_ranges if e is not None)
            PAD_DAYS = 3
            co_start = max(min_start - timedelta(days=PAD_DAYS), date(1970, 1, 1))
            co_end = min(max_end + timedelta(days=PAD_DAYS), date.today())

            try:
                self.logger.info(f"DB에 누락된 기간을 yfinance에서 가져옵니다(통합+패드): {ticker} {co_start} -> {co_end}")
                df_new = self.data_fetcher.fetch_stock_data(ticker, co_start, co_end, use_cache=True)

                if df_new is not None and not df_new.empty:
                    self.save_ticker_data(ticker, df_new)
                    # 데이터 저장 후 커넥션을 닫고 새로 연결하여 트랜잭션 격리 문제 방지
                    conn.close()
                    conn = engine.connect()
                    return conn
                else:
                    self.logger.warning("통합 fetch가 빈 결과를 반환했습니다; 개별 구간으로 폴백합니다.")
                    raise ValueError("empty result from consolidated fetch")
            except Exception:
                self.logger.exception("통합 누락 기간 수집 실패, 개별 구간 시도 중")

        # 전략 2 (fallback): 개별 구간별 fetch
        for s, e in missing_ranges:
            if s is None or e is None:
                continue
            if s > e:
                continue
            try:
                self.logger.info(f"DB에 누락된 기간을 yfinance에서 가져옵니다: {ticker} {s} -> {e}")
                df_new = self.data_fetcher.fetch_stock_data(ticker, s, e, use_cache=True)
                
                if df_new is not None and not df_new.empty:
                     self.save_ticker_data(ticker, df_new)
                     # 데이터 저장 후 커넥션 갱신
                     conn.close()
                     conn = engine.connect()
            except Exception:
                self.logger.exception("누락 기간 수집 실패")

        return conn

    def _query_and_format_dataframe(
        self,
        conn,
        stock_id: int,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        DB에서 요청 범위의 주가 데이터를 조회하고 DataFrame으로 포맷합니다.
        """
        # SQL 쿼리 작성
        q = "SELECT date, open, high, low, close, adj_close, volume FROM daily_prices WHERE stock_id = :sid"
        params = {"sid": stock_id}
        if start_date:
            q += " AND date >= :start"
            params["start"] = str(start_date)
        if end_date:
            q += " AND date <= :end"
            params["end"] = str(end_date)
        q += " ORDER BY date ASC"

        # 쿼리 실행
        res = conn.execute(text(q), params)
        rows = res.fetchall()
        if not rows:
            raise ValueError(f"티커 '{ticker}'에 대한 데이터가 없습니다. (요청 범위: {start_date} - {end_date})")

        # DataFrame 생성
        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "adj_close", "volume"])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # 컬럼명 정규화
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'adj_close': 'Adj Close',
            'volume': 'Volume'
        })

        # 타입 보장
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Volume' in df.columns:
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype('int64')

        return df

    def _load_ticker_data_internal(self, ticker: str, start_date=None, end_date=None) -> pd.DataFrame:
        """
        실제 데이터 로드 로직 (내부용)

        Note: _ensure_stock_exists와 _fetch_and_save_missing_data는 내부적으로
        커넥션을 닫고 새로 연결하는 패턴을 사용하므로 context manager 대신 수동 관리.
        """
        engine = self._get_engine()
        conn = engine.connect()
        try:
            # 1. 날짜 정규화 및 기본값 설정
            start_date, end_date = self._normalize_date_params(start_date, end_date)

            # 2. stock_id 확보 (DB에 없으면 yfinance에서 수집)
            stock_id, conn = self._ensure_stock_exists(conn, engine, ticker, start_date, end_date)

            # 3. DB에 저장된 데이터 범위 조회
            db_min, db_max = self._get_date_coverage(conn, stock_id)

            # 4. 누락된 구간 수집 (통합 fetch 시도 → fallback: 개별 fetch)
            conn = self._fetch_and_save_missing_data(conn, engine, ticker, start_date, end_date, db_min, db_max)

            # 5. 최종 데이터 조회 및 DataFrame 반환
            df = self._query_and_format_dataframe(conn, stock_id, ticker, start_date, end_date)

            return df
        finally:
            conn.close()

    def load_news_from_db(self, ticker: str, max_age_hours: int = 3) -> Optional[list]:
        """
        DB에서 뉴스 데이터 조회 (최대 age 체크)
        """
        engine = self._get_engine()
        try:
            # created_at이 max_age_hours 이내인 뉴스만 조회
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            query = text("""
                SELECT title, link, description, news_date, created_at
                FROM stock_news
                WHERE ticker = :ticker
                AND created_at >= :cutoff_time
                ORDER BY news_date DESC, created_at DESC
                LIMIT 20
            """)

            with engine.connect() as conn:
                result = conn.execute(query, {"ticker": ticker, "cutoff_time": cutoff_time})
                rows = result.fetchall()

            if not rows:
                self.logger.debug(f"DB에 {ticker}의 최신 뉴스({max_age_hours}시간 이내)가 없습니다")
                return None

            # 뉴스 리스트로 변환
            news_list = []
            for row in rows:
                news_list.append({
                    'title': row[0],
                    'link': row[1],
                    'description': row[2] or '',
                    'pubDate': row[3].strftime('%a, %d %b %Y %H:%M:%S +0900') if isinstance(row[3], date) else str(row[3])
                })

            self.logger.info(f"DB에서 {ticker} 뉴스 {len(news_list)}개 조회 (created_at >= {cutoff_time})")
            return news_list

        except Exception as e:
            self.logger.error(f"DB 뉴스 조회 실패: {ticker} - {str(e)}")
            return None

    def save_news_to_db(self, ticker: str, news_list: list) -> int:
        """
        뉴스 데이터를 DB에 저장
        """
        if not news_list:
            return 0

        engine = self._get_engine()

        try:
            with engine.begin() as conn:
                # 기존 해당 티커의 모든 뉴스 삭제 (새로 저장하기 전에)
                delete_query = text("""
                    DELETE FROM stock_news
                    WHERE ticker = :ticker
                """)
                conn.execute(delete_query, {"ticker": ticker})

                # 새 뉴스 저장
                saved_count = 0
                for news in news_list:
                    try:
                        # pubDate 파싱 (RFC 2822 형식)
                        pub_date_str = news.get('pubDate', '')
                        pub_timestamp = email.utils.parsedate_tz(pub_date_str)
                        if pub_timestamp:
                            news_date = datetime.fromtimestamp(email.utils.mktime_tz(pub_timestamp)).date()
                        else:
                            news_date = datetime.now().date()

                        # 단순 삽입 (이미 해당 티커의 기존 데이터는 삭제됨)
                        insert_query = text("""
                            INSERT INTO stock_news (ticker, news_date, title, link, description, source, created_at)
                            VALUES (:ticker, :news_date, :title, :link, :description, :source, NOW())
                        """)

                        conn.execute(insert_query, {
                            "ticker": ticker,
                            "news_date": news_date,
                            "title": news['title'][:500],  # 길이 제한
                            "link": news.get('link', '')[:1000],
                            "description": news.get('description', '')[:1000] if news.get('description') else None,
                            "source": "Naver"
                        })
                        saved_count += 1

                    except Exception as e:
                        self.logger.warning(f"뉴스 저장 실패 (계속 진행): {str(e)}")
                        continue

                self.logger.info(f"DB에 {ticker} 뉴스 {saved_count}/{len(news_list)}개 저장 완료")
                return saved_count

        except Exception as e:
            self.logger.error(f"DB 뉴스 저장 실패: {ticker} - {str(e)}")
            return 0
