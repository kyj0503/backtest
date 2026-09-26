"""종목 뉴스(stock_news) 캐시 저장·조회 — YFinanceRepository 믹스인

외부 뉴스 API 결과를 티커별로 stock_news 테이블에 캐시한다. 가격 데이터와
테이블·트랜잭션을 공유하지 않는다.
"""
import email.utils
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import text


class NewsStoreMixin:
    """stock_news 테이블 캐시.

    호스트 클래스(YFinanceRepository)가 `_get_engine()`, `logger`, `data_fetcher`를
    제공한다고 가정한다. 테스트가 인스턴스의 `_get_engine`/`data_fetcher`를
    monkeypatch로 바꾸므로 모두 self를 통해 참조한다.
    """

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
