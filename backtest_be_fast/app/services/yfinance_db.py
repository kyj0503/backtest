"""
yfinance 데이터 MySQL 저장 서비스

**역할**:
- yfinance API로 수집한 주가 데이터를 MySQL DB에 저장
- DB 우선 조회 전략으로 외부 API 호출 최소화
- 누락된 기간 데이터 자동 보완

**주요 기능**:
1. load_ticker_data(): 주가 데이터 조회 (DB 우선)
   - DB에서 먼저 조회
   - 누락 기간이 있으면 yfinance로 보완
   - 새로 가져온 데이터를 DB에 저장
2. save_ticker_data(): DataFrame을 DB에 저장
3. get_date_range(): DB에 저장된 데이터 범위 조회

**DB 스키마**:
- 테이블: daily_prices
- 컬럼: ticker, date, open, high, low, close, volume, adj_close
- 복합 기본키: (ticker, date)

**최적화 전략**:
- 배치 삽입: 대량 데이터를 한 번에 저장
- 중복 방지: ON DUPLICATE KEY UPDATE
- 날짜 범위 캐싱: 불필요한 API 호출 방지

**의존성**:
- SQLAlchemy: DB 연결 및 쿼리
- yfinance: 외부 데이터 소스
- pandas: 데이터 처리

**연관 컴포넌트**:
- Backend: app/repositories/data_repository.py (Repository 패턴)
- Backend: app/services/data_service.py (데이터 로딩)
- Database: database/schema.sql (테이블 정의)

**환경 설정**:
- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME: 환경 변수
"""
import os
import json
import logging
import time
import email.utils
from typing import Optional, Union, List, Dict, Any, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
from datetime import datetime, date, timedelta
from app.utils.data_fetcher import data_fetcher

logger = logging.getLogger(__name__)

_ENGINE_CACHE: Optional[Engine] = None


def _get_engine() -> Engine:
    global _ENGINE_CACHE
    if _ENGINE_CACHE is not None:
        return _ENGINE_CACHE
    # Prefer settings (which loads .env) but allow direct env fallback if necessary
    try:
        from app.core.config import settings
        db_url = settings.database_url or os.getenv("DATABASE_URL")
    except Exception:
        db_url = os.getenv("DATABASE_URL")

    # Ensure these local variables always exist for logging/fallbacks
    db_host = None
    db_port = None
    db_user = None
    db_pass = None
    db_name = None

    if db_url:
        # Try to parse components from the full DATABASE_URL for informative logging
        try:
            # sqlalchemy >=1.4 exposes make_url in sqlalchemy.engine
            try:
                from sqlalchemy.engine import make_url
            except Exception:
                from sqlalchemy.engine.url import make_url

            parsed = make_url(db_url)
            db_host = parsed.host
            db_port = str(parsed.port) if parsed.port is not None else None
            db_user = parsed.username
            db_pass = parsed.password
            db_name = parsed.database
        except Exception:
            # If parsing fails, try to fallback to individual env vars so logs
            # and diagnostic output remain useful instead of None.
            try:
                db_host = settings.database_host or os.getenv("DATABASE_HOST")
                db_port = settings.database_port or os.getenv("DATABASE_PORT")
                db_user = settings.database_user or os.getenv("DATABASE_USER")
                db_pass = settings.database_password or os.getenv("DATABASE_PASSWORD")
                db_name = settings.database_name or os.getenv("DATABASE_NAME")
            except Exception:
                db_host = os.getenv("DATABASE_HOST")
                db_port = os.getenv("DATABASE_PORT")
                db_user = os.getenv("DATABASE_USER")
                db_pass = os.getenv("DATABASE_PASSWORD")
                db_name = os.getenv("DATABASE_NAME")
    else:
        # If DATABASE_URL is not provided, build it from individual env vars so
        # the service can connect to the Docker Compose mysql host (e.g. 'mysql').
        try:
            db_host = settings.database_host or os.getenv("DATABASE_HOST", "127.0.0.1")
            db_port = settings.database_port or os.getenv("DATABASE_PORT", "3306")
            db_user = settings.database_user or os.getenv("DATABASE_USER", "root")
            db_pass = settings.database_password or os.getenv("DATABASE_PASSWORD", "password")
            db_name = settings.database_name or os.getenv("DATABASE_NAME", "stock_data_cache")
            db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        except Exception:
            db_host = os.getenv("DATABASE_HOST", "127.0.0.1")
            db_port = os.getenv("DATABASE_PORT", "3306")
            db_user = os.getenv("DATABASE_USER", "root")
            db_pass = os.getenv("DATABASE_PASSWORD", "password")
            db_name = os.getenv("DATABASE_NAME", "stock_data_cache")
            db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    # Log the connection info we will use (mask password)
    try:
        masked_db_url = db_url.replace(db_pass, "***") if (db_pass and isinstance(db_url, str)) else db_url
    except Exception:
        masked_db_url = "<unavailable>"
    logger.info(
        "Creating SQLAlchemy engine -> host=%s port=%s user=%s db=%s DATABASE_URL_set=%s",
        db_host or "<unknown>", db_port or "<unknown>", db_user or "<unknown>", db_name or "<unknown>", 'yes' if os.getenv('DATABASE_URL') else 'no'
    )
    logger.debug(f"SQLAlchemy URL (masked): {masked_db_url}")
    # Also print to stdout and log as error to ensure visibility in all log configurations
    try:
        print(f"[yfinance_db] Creating engine -> host={db_host} port={db_port} user={db_user} db={db_name} masked_url={masked_db_url}")
    except Exception:
        pass
    logger.error(f"[yfinance_db] SQLAlchemy URL (masked): {masked_db_url}")

    _ENGINE_CACHE = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=40,           # 기본 5 → 40 (동시 연결 수 증가)
        max_overflow=80,        # 기본 10 → 80 (추가 연결 허용)
        pool_timeout=30,        # 연결 대기 시간 30초
        pool_recycle=3600,      # 1시간마다 연결 재생성 (커넥션 풀 관리)
        future=True
    )
    return _ENGINE_CACHE


def save_ticker_data(ticker: str, df: pd.DataFrame) -> int:
    """stocks 테이블에 티커 등록 및 daily_prices에 행을 upsert 합니다.

    Returns: 저장된 행 수
    """
    engine = _get_engine()
    conn = engine.connect()
    trans = conn.begin()
    try:
        # ensure stock exists
        info = {}
        try:
            info = data_fetcher.get_ticker_info(ticker)
        except Exception:
            logger.warning("티커 info 조회 실패")

        # insert or update stocks
        insert_stock = text(
            """
            INSERT INTO stocks (ticker, name, exchange, sector, industry, summary, info_json, last_info_update)
            VALUES (:ticker, :name, :exchange, :sector, :industry, :summary, :info_json, :now)
            ON DUPLICATE KEY UPDATE name=VALUES(name), exchange=VALUES(exchange), sector=VALUES(sector),
              industry=VALUES(industry), summary=VALUES(summary), info_json=VALUES(info_json), last_info_update=VALUES(last_info_update)
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
            "now": now
        })

        # get stock_id
        stock_id_row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
        if not stock_id_row:
            raise RuntimeError("stock_id를 찾을 수 없습니다.")
        stock_id = stock_id_row[0]

        # prepare daily prices upsert
        rows = []
        df_proc = df.copy()
        if 'Date' in df_proc.columns:
            df_proc['date'] = pd.to_datetime(df_proc['Date']).dt.date
        else:
            df_proc = df_proc.reset_index()
            df_proc['date'] = pd.to_datetime(df_proc[df_proc.columns[0]]).dt.date

        for _, r in df_proc.iterrows():
            o = None if pd.isna(r.get('Open')) else float(r.get('Open'))
            h = None if pd.isna(r.get('High')) else float(r.get('High'))
            l = None if pd.isna(r.get('Low')) else float(r.get('Low'))
            c = None if pd.isna(r.get('Close')) else float(r.get('Close'))
            ac = None
            if 'Adj Close' in r or 'AdjClose' in r or 'Adj_Close' in r:
                ac = r.get('Adj Close') or r.get('AdjClose') or r.get('Adj_Close')
                ac = None if pd.isna(ac) else float(ac)
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
            # batch upsert
            insert_stmt = text(
                """
                INSERT INTO daily_prices (stock_id, date, open, high, low, close, adj_close, volume)
                VALUES (:stock_id, :date, :open, :high, :low, :close, :adj_close, :volume)
                ON DUPLICATE KEY UPDATE open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close), adj_close=VALUES(adj_close), volume=VALUES(volume)
                """
            )
            # chunking
            chunk_size = 500
            total = 0
            for i in range(0, len(rows), chunk_size):
                batch = rows[i:i+chunk_size]
                conn.execute(insert_stmt, batch)
                total += len(batch)

        trans.commit()
        return len(rows)

    except Exception as e:
        trans.rollback()
        logger.exception("save_ticker_data 실패")
        raise
    finally:
        conn.close()


def load_ticker_data(ticker: str, start_date: Optional[Union[str, date]] = None, end_date: Optional[Union[str, date]] = None, max_retries: int = 3, retry_delay: float = 2.0) -> pd.DataFrame:
    """DB에서 ticker의 daily_prices를 조회해 pandas DataFrame으로 반환합니다.

    start_date/end_date는 date 또는 문자열(YYYY-MM-DD)을 받을 수 있습니다.
    반환 DataFrame은 DatetimeIndex(날짜)와 컬럼 ['Open','High','Low','Close','Adj_Close','Volume']를 가집니다.
    
    Args:
        ticker: 종목 심볼
        start_date: 시작 날짜
        end_date: 종료 날짜
        max_retries: 최대 재시도 횟수 (기본 3회)
        retry_delay: 재시도 간 대기 시간 (초, 기본 2초)
    
    Returns:
        DataFrame: 주가 데이터
        
    Raises:
        ValueError: 모든 재시도 실패 시
    """
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[시도 {attempt}/{max_retries}] {ticker} 데이터 로드 중... ({start_date} ~ {end_date})")
            
            # 실제 데이터 로드 로직
            df = _load_ticker_data_internal(ticker, start_date, end_date)
            
            if df is not None and not df.empty:
                logger.info(f"[성공] {ticker} 데이터 로드 완료: {len(df)}행 (시도 {attempt}회)")
                return df
            else:
                logger.warning(f"[시도 {attempt}/{max_retries}] {ticker} 데이터가 비어있음")
                last_exception = ValueError(f"{ticker} 데이터가 비어있습니다")
                
        except Exception as e:
            logger.warning(f"[시도 {attempt}/{max_retries}] {ticker} 데이터 로드 실패: {str(e)}")
            last_exception = e
        
        # 마지막 시도가 아니면 대기 후 재시도
        if attempt < max_retries:
            wait_time = retry_delay * attempt  # 점진적 증가 (2초, 4초, 6초...)
            logger.info(f"[재시도 대기] {wait_time}초 후 {ticker} 데이터 재시도...")
            time.sleep(wait_time)
    
    # 모든 재시도 실패
    error_msg = f"[실패] {ticker} 데이터 로드 실패 (총 {max_retries}회 시도)"
    if last_exception:
        error_msg += f": {str(last_exception)}"
    logger.error(error_msg)
    raise ValueError(error_msg)


def get_ticker_info_from_db(ticker: str) -> Dict[str, Any]:
    """
    DB에서 티커의 메타데이터 조회

    Args:
        ticker: 종목 심볼

    Returns:
        티커 정보 딕셔너리 (currency, first_trade_date 포함)
        
    Note:
        - 캐시된 info_json 사용으로 Yahoo Finance API 재호출 최소화
        - first_trade_date가 없으면 Yahoo Finance에서 가져와 DB 업데이트
    """
    engine = _get_engine()
    conn = engine.connect()
    try:
        ticker = ticker.upper()
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
                    logger.info(f"{ticker}: DB에 상장일 없음 - Yahoo Finance에서 조회")
                    try:
                        fresh_info = data_fetcher.get_ticker_info(ticker)
                        if fresh_info.get('first_trade_date'):
                            info['first_trade_date'] = fresh_info['first_trade_date']
                            # DB 업데이트
                            conn.execute(
                                text("UPDATE stocks SET info_json = :info WHERE id = :id"),
                                {"info": json.dumps(info), "id": stock_id}
                            )
                            conn.commit()
                            logger.info(f"{ticker}: 상장일 업데이트 완료 - {info['first_trade_date']}")
                    except Exception as e:
                        logger.warning(f"{ticker}: 상장일 조회 실패 - {e}")
                
                return {
                    'symbol': ticker,
                    'currency': info.get('currency', 'USD'),
                    'company_name': info.get('company_name', ticker),
                    'exchange': info.get('exchange', 'Unknown'),
                    'first_trade_date': info.get('first_trade_date', None)
                }
            except Exception as e:
                logger.warning(f"info_json 파싱 실패: {ticker} - {e}")

        # DB에 없으면 기본값 반환
        return {
            'symbol': ticker,
            'currency': 'USD',
            'company_name': ticker,
            'exchange': 'Unknown',
            'first_trade_date': None
        }
    except Exception as e:
        logger.error(f"티커 정보 조회 실패: {ticker} - {e}")
        return {
            'symbol': ticker,
            'currency': 'USD',
            'company_name': ticker,
            'exchange': 'Unknown',
            'first_trade_date': None
        }
    finally:
        conn.close()


def get_ticker_info_batch_from_db(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    DB에서 여러 티커의 메타데이터를 배치로 조회 (N+1 쿼리 최적화)

    Args:
        tickers: 종목 심볼 리스트

    Returns:
        티커별 정보 딕셔너리 (key: ticker, value: info dict)
        
    Note:
        상장일이 없는 종목이 있으면 로그에 경고를 출력합니다.
        scripts/update_ticker_listing_dates.py를 실행하여 일괄 업데이트할 수 있습니다.
    """
    if not tickers:
        return {}

    engine = _get_engine()
    conn = engine.connect()
    try:
        # 대문자로 변환
        upper_tickers = [t.upper() for t in tickers]

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
                    logger.warning(f"info_json 파싱 실패: {ticker} - {e}")
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
            logger.warning(
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
        logger.error(f"배치 티커 정보 조회 실패: {e}")
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
    finally:
        conn.close()


def _normalize_date_params(start_date: Optional[Union[str, date, datetime, pd.Timestamp]], end_date: Optional[Union[str, date, datetime, pd.Timestamp]]) -> Tuple[date, date]:
    """
    날짜 매개변수를 정규화하고 기본값을 설정합니다.

    Args:
        start_date: 시작 날짜 (date, str, datetime, pd.Timestamp, or None)
        end_date: 종료 날짜 (date, str, datetime, pd.Timestamp, or None)

    Returns:
        tuple[date, date]: (정규화된_시작날짜, 정규화된_종료날짜)

    Note:
        - 둘 다 None인 경우: 최근 1년 (today - 365일 ~ today)
        - start만 None인 경우: end - 365일 ~ end
        - end만 None인 경우: start ~ today
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


def _ensure_stock_exists(conn, engine: Engine, ticker: str, start_date: date, end_date: date) -> tuple[int, any]:
    """
    stock_id를 조회하고, DB에 없으면 yfinance에서 데이터를 가져와 저장합니다.

    Args:
        conn: DB 연결 객체
        engine: SQLAlchemy 엔진
        ticker: 티커 심볼
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        tuple[int, Connection]: (stock_id, 갱신된_connection)

    Raises:
        ValueError: 티커를 찾을 수 없거나 생성할 수 없는 경우

    Note:
        - DB에 없으면 yfinance에서 수집하여 저장
        - 데이터 저장 후 트랜잭션 격리 문제 방지를 위해 connection 갱신
    """
    row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()

    if not row:
        logger.info(f"티커 '{ticker}'이 DB에 없음 — yfinance에서 수집 시도")
        try:
            df_new = data_fetcher.get_stock_data(ticker, start_date, end_date, use_cache=True)
            if df_new is None or df_new.empty:
                raise ValueError("yfinance에서 유효한 데이터가 반환되지 않았습니다.")
            save_ticker_data(ticker, df_new)

            # 데이터 저장 후 커넥션을 닫고 새로 연결 - 트랜잭션 격리 문제 방지
            conn.close()
            time.sleep(0.1)  # 100ms 대기 - DB 커밋 완료 보장
            conn = engine.connect()
        except Exception as e:
            logger.exception("티커가 DB에 없고 yfinance 수집 실패")
            raise ValueError(f"티커 '{ticker}'이(가) DB에 없고 yfinance 수집 실패: {e}")

        row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
        if not row:
            raise ValueError(f"티커 '{ticker}'을(를) DB에 추가할 수 없습니다.")

    stock_id = row[0]
    return stock_id, conn


def _get_date_coverage(conn, stock_id: int) -> tuple[Optional[date], Optional[date]]:
    """
    DB에 저장된 주가 데이터의 날짜 범위를 조회합니다.

    Args:
        conn: DB 연결 객체
        stock_id: 주식 ID

    Returns:
        tuple[Optional[date], Optional[date]]: (최소_날짜, 최대_날짜)
        데이터가 없으면 (None, None) 반환
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

    Args:
        conn: DB 연결 객체
        engine: SQLAlchemy 엔진
        ticker: 티커 심볼
        start_date: 요청 시작 날짜
        end_date: 요청 종료 날짜
        db_min: DB에 저장된 최소 날짜 (None이면 DB에 데이터 없음)
        db_max: DB에 저장된 최대 날짜 (None이면 DB에 데이터 없음)

    Returns:
        Connection: 갱신된 DB 연결 객체

    Note:
        - 통합 fetch 시도 (여러 구간을 하나로 합쳐서 패딩 추가)
        - 실패 시 개별 구간별 fetch로 fallback
        - 데이터 저장 후 트랜잭션 격리 문제 방지를 위해 connection 갱신
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
    if data_fetcher is not None:
        min_start = min(s for s, _ in missing_ranges if s is not None)
        max_end = max(e for _, e in missing_ranges if e is not None)
        PAD_DAYS = 3
        co_start = max(min_start - timedelta(days=PAD_DAYS), date(1970, 1, 1))
        co_end = min(max_end + timedelta(days=PAD_DAYS), date.today())

        try:
            logger.info(f"DB에 누락된 기간을 yfinance에서 가져옵니다(통합+패드): {ticker} {co_start} -> {co_end}")
            df_new = data_fetcher.get_stock_data(ticker, co_start, co_end, use_cache=True)
            if df_new is not None and not df_new.empty:
                save_ticker_data(ticker, df_new)
                # 데이터 저장 후 커넥션을 닫고 새로 연결하여 트랜잭션 격리 문제 방지
                conn.close()
                time.sleep(0.1)  # 100ms 대기 - DB 커밋 완료 보장
                conn = engine.connect()
                return conn
            else:
                logger.warning("통합 fetch가 빈 결과를 반환했습니다; 개별 구간으로 폴백합니다.")
                raise ValueError("empty result from consolidated fetch")
        except Exception:
            logger.exception("통합 누락 기간 수집 실패, 개별 구간 시도 중")

    # 전략 2 (fallback): 개별 구간별 fetch
    for s, e in missing_ranges:
        if s is None or e is None:
            continue
        if s > e:
            continue
        try:
            logger.info(f"DB에 누락된 기간을 yfinance에서 가져옵니다: {ticker} {s} -> {e}")
            df_new = data_fetcher.get_stock_data(ticker, s, e, use_cache=True)
            if df_new is not None and not df_new.empty:
                save_ticker_data(ticker, df_new)
                # 데이터 저장 후 커넥션 갱신
                conn.close()
                time.sleep(0.1)
                conn = engine.connect()
        except Exception:
            logger.exception("누락 기간 수집 실패")

    return conn


def _query_and_format_dataframe(
    conn,
    stock_id: int,
    ticker: str,
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    DB에서 요청 범위의 주가 데이터를 조회하고 DataFrame으로 포맷합니다.

    Args:
        conn: DB 연결 객체
        stock_id: 주식 ID
        ticker: 티커 심볼 (에러 메시지용)
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        pd.DataFrame: 주가 데이터 (날짜 인덱스, OHLCV 컬럼)

    Raises:
        ValueError: 데이터가 없는 경우

    Note:
        - 컬럼명을 표준 포맷으로 정규화 (Open, High, Low, Close, Adj Close, Volume)
        - 숫자형 타입 보장
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


def _load_ticker_data_internal(ticker: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    실제 데이터 로드 로직 (내부용)

    DB 우선 조회 전략:
    1. 날짜 매개변수 정규화
    2. stock_id 확보 (없으면 yfinance에서 가져와 저장)
    3. DB 데이터 범위 조회
    4. 누락 구간 수집 (통합 fetch → fallback: 개별 fetch)
    5. 최종 데이터 조회 및 DataFrame 반환

    Args:
        ticker: 티커 심볼
        start_date: 시작 날짜 (date, str, datetime, or None)
        end_date: 종료 날짜 (date, str, datetime, or None)

    Returns:
        pd.DataFrame: 주가 데이터 (날짜 인덱스, OHLCV 컬럼)

    Raises:
        ValueError: 데이터를 찾을 수 없거나 생성할 수 없는 경우

    Note:
        - 144줄 함수를 5개 헬퍼로 분할하여 가독성 향상
        - 각 헬퍼는 단일 책임 원칙 준수
    """
    engine = _get_engine()
    conn = engine.connect()
    try:
        # 1. 날짜 정규화 및 기본값 설정
        start_date, end_date = _normalize_date_params(start_date, end_date)

        # 2. stock_id 확보 (DB에 없으면 yfinance에서 수집)
        stock_id, conn = _ensure_stock_exists(conn, engine, ticker, start_date, end_date)

        # 3. DB에 저장된 데이터 범위 조회
        db_min, db_max = _get_date_coverage(conn, stock_id)

        # 4. 누락된 구간 수집 (통합 fetch 시도 → fallback: 개별 fetch)
        conn = _fetch_and_save_missing_data(conn, engine, ticker, start_date, end_date, db_min, db_max)

        # 5. 최종 데이터 조회 및 DataFrame 반환
        df = _query_and_format_dataframe(conn, stock_id, ticker, start_date, end_date)

        return df
    finally:
        conn.close()


def load_news_from_db(ticker: str, max_age_hours: int = 3) -> Optional[list]:
    """
    DB에서 뉴스 데이터 조회 (최대 age 체크)

    Args:
        ticker: 종목 심볼
        max_age_hours: 최대 age (시간) - 이보다 오래된 데이터는 제외

    Returns:
        뉴스 리스트 또는 None (데이터가 없거나 너무 오래된 경우)
        각 뉴스는 다음 키를 포함하는 딕셔너리:
            - title: 뉴스 제목
            - link: 뉴스 링크
            - description: 뉴스 설명
            - pubDate: 발행일 (RFC 2822 형식)
    """
    engine = _get_engine()
    conn = engine.connect()
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

        result = conn.execute(query, {"ticker": ticker, "cutoff_time": cutoff_time})
        rows = result.fetchall()

        if not rows:
            logger.debug(f"DB에 {ticker}의 최신 뉴스({max_age_hours}시간 이내)가 없습니다")
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

        logger.info(f"DB에서 {ticker} 뉴스 {len(news_list)}개 조회 (created_at >= {cutoff_time})")
        return news_list

    except Exception as e:
        logger.error(f"DB 뉴스 조회 실패: {ticker} - {str(e)}")
        return None
    finally:
        conn.close()


def save_news_to_db(ticker: str, news_list: list) -> int:
    """
    뉴스 데이터를 DB에 저장

    이 함수는 해당 ticker의 기존 뉴스를 모두 삭제한 후 새 뉴스를 저장합니다.
    이는 중복 방지와 최신 데이터 유지를 위한 설계입니다.

    Args:
        ticker: 종목 심볼
        news_list: 뉴스 딕셔너리 리스트

    Returns:
        저장된 행 수
    """
    if not news_list:
        return 0

    engine = _get_engine()
    conn = engine.connect()
    trans = conn.begin()

    try:
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
                logger.warning(f"뉴스 저장 실패 (계속 진행): {str(e)}")
                continue

        trans.commit()
        logger.info(f"DB에 {ticker} 뉴스 {saved_count}/{len(news_list)}개 저장 완료")
        return saved_count

    except Exception as e:
        trans.rollback()
        logger.error(f"DB 뉴스 저장 실패: {ticker} - {str(e)}")
        return 0
    finally:
        conn.close()

