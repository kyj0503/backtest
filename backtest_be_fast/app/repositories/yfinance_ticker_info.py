"""티커 메타데이터(stocks.info_json) 조회 — YFinanceRepository 믹스인

통화·거래소·상장일 같은 티커 정보를 stocks 테이블에서 읽는다. 상장일이 비어
있으면 DB 커넥션을 닫은 뒤 Yahoo Finance에서 채워 넣는다 (P2-10).
"""
import json
from typing import Any, Dict, List

from sqlalchemy import text


class TickerInfoQueriesMixin:
    """stocks.info_json 기반 티커 메타데이터 조회.

    호스트 클래스(YFinanceRepository)가 `_get_engine()`, `logger`, `data_fetcher`를
    제공한다고 가정한다. 테스트가 인스턴스의 `_get_engine`/`data_fetcher`를
    monkeypatch로 바꾸므로 모두 self를 통해 참조한다.
    """

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
            # 커넥션은 SELECT 하나만 수행하고 즉시 반환한다 (P2-10). 상장일이
            # 없어 Yahoo Finance를 조회해야 하는 경우, 그 네트워크 호출과 후속
            # UPDATE(_update_ticker_info)는 아래에서 이 커넥션을 닫은 뒤 별도로
            # 수행한다 - 느린 외부 응답 동안 DB 커넥션을 붙잡지 않기 위함이다.
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
                    # (DB 커넥션이 열려있지 않은 상태에서 네트워크 호출)
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
