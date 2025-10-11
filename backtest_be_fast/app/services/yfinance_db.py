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
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
from datetime import datetime, date, timedelta

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

    _ENGINE_CACHE = create_engine(db_url, pool_pre_ping=True, future=True)
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
            from app.utils.data_fetcher import data_fetcher
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


def load_ticker_data(ticker: str, start_date=None, end_date=None) -> pd.DataFrame:
    """DB에서 ticker의 daily_prices를 조회해 pandas DataFrame으로 반환합니다.

    start_date/end_date는 date 또는 문자열(YYYY-MM-DD)을 받을 수 있습니다.
    반환 DataFrame은 DatetimeIndex(날짜)와 컬럼 ['Open','High','Low','Close','Adj_Close','Volume']를 가집니다.
    """
    engine = _get_engine()
    conn = engine.connect()
    try:
        # normalize start/end to date objects
        def _to_date(d):
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

        # defaults: last 1 year if not provided
        if end_date is None and start_date is None:
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
        elif start_date is None:
            end_date = end_date or date.today()
            start_date = end_date - timedelta(days=365)
        elif end_date is None:
            end_date = date.today()

        # find stock_id; if missing, fetch from yfinance and save
        row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
        if not row:
            logger.info(f"티커 '{ticker}'이 DB에 없음 — yfinance에서 수집 시도")
            try:
                from app.utils.data_fetcher import data_fetcher
                df_new = data_fetcher.get_stock_data(ticker, start_date, end_date, use_cache=True)
                if df_new is None or df_new.empty:
                    raise ValueError("yfinance에서 유효한 데이터가 반환되지 않았습니다.")
                save_ticker_data(ticker, df_new)
            except Exception as e:
                logger.exception("티커가 DB에 없고 yfinance 수집 실패")
                raise ValueError(f"티커 '{ticker}'이(가) DB에 없고 yfinance 수집 실패: {e}")

            # re-query using a fresh connection to avoid transaction snapshot issues
            # (some MySQL isolation levels like REPEATABLE READ may not see rows inserted
            #  by a different connection within the same snapshot)
            conn.close()
            conn = engine.connect()
            row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
            if not row:
                raise ValueError(f"티커 '{ticker}'을(를) DB에 추가할 수 없습니다.")

        stock_id = row[0]

        # check existing coverage
        date_row = conn.execute(text("SELECT MIN(date), MAX(date) FROM daily_prices WHERE stock_id = :sid"), {"sid": stock_id}).fetchone()
        db_min, db_max = None, None
        if date_row and date_row[0] is not None:
            db_min = pd.to_datetime(date_row[0]).date()
            db_max = pd.to_datetime(date_row[1]).date()

        # fetch missing ranges if any
        try:
            from app.utils.data_fetcher import data_fetcher
        except Exception:
            data_fetcher = None

        missing_ranges = []
        if db_min is None:
            # no data at all in DB for this ticker -> fetch full requested range
            missing_ranges.append((start_date, end_date))
        else:
            if start_date < db_min:
                missing_ranges.append((start_date, db_min - timedelta(days=1)))
            if end_date > db_max:
                missing_ranges.append((db_max + timedelta(days=1), end_date))

        # If there are multiple small missing ranges, try to coalesce into one padded fetch
        if missing_ranges and data_fetcher is not None:
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
                else:
                    logger.warning("통합 fetch가 빈 결과를 반환했습니다; 개별 구간으로 폴백합니다.")
                    raise ValueError("empty result from consolidated fetch")
            except Exception:
                logger.exception("통합 누락 기간 수집 실패, 개별 구간 시도 중")
                # fallback: try per-range fetch as before
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
                    except Exception:
                        logger.exception("누락 기간 수집 실패")
        else:
            if data_fetcher is None and missing_ranges:
                logger.warning("data_fetcher 모듈을 찾을 수 없어 누락 데이터를 가져올 수 없습니다.")

        # build query to return requested interval
        q = "SELECT date, open, high, low, close, adj_close, volume FROM daily_prices WHERE stock_id = :sid"
        params = {"sid": stock_id}
        if start_date:
            q += " AND date >= :start"
            params["start"] = str(start_date)
        if end_date:
            q += " AND date <= :end"
            params["end"] = str(end_date)
        q += " ORDER BY date ASC"

        res = conn.execute(text(q), params)
        rows = res.fetchall()
        if not rows:
            raise ValueError(f"티커 '{ticker}'에 대한 데이터가 없습니다. (요청 범위: {start_date} - {end_date})")

        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "adj_close", "volume"])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        # normalize column names to expected ones
        df = df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'adj_close': 'Adj Close', 'volume': 'Volume'
        })
        # ensure types
        for col in ['Open','High','Low','Close','Adj Close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Volume' in df.columns:
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype('int64')

        return df
    finally:
        conn.close()
