"""
뉴스 Repository
DB에서 뉴스 데이터를 관리합니다.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy import text
from ..services.yfinance_db import _get_engine

logger = logging.getLogger(__name__)


class NewsRepository:
    """뉴스 데이터 Repository"""

    def __init__(self):
        self.engine = None

    def _get_connection(self):
        """DB 연결 가져오기"""
        if self.engine is None:
            self.engine = _get_engine()
        return self.engine.connect()

    def save_news(self, ticker: str, news_date: date, news_list: List[Dict[str, Any]], source: str = "naver") -> int:
        """
        뉴스 데이터를 DB에 저장합니다.

        Args:
            ticker: 종목 티커
            news_date: 뉴스 날짜
            news_list: 뉴스 리스트 [{'title', 'link', 'description', 'pubDate'}]
            source: 뉴스 출처 (기본값: naver)

        Returns:
            저장된 뉴스 개수
        """
        if not news_list:
            return 0

        conn = self._get_connection()
        trans = conn.begin()

        try:
            # 기존 데이터 삭제 (날짜별로)
            delete_query = text("""
                DELETE FROM stock_news
                WHERE ticker = :ticker AND news_date = :news_date
            """)
            conn.execute(delete_query, {"ticker": ticker, "news_date": news_date})

            # 새 뉴스 데이터 삽입
            insert_query = text("""
                INSERT INTO stock_news (ticker, news_date, title, link, description, source)
                VALUES (:ticker, :news_date, :title, :link, :description, :source)
            """)

            saved_count = 0
            for news_item in news_list:
                try:
                    conn.execute(insert_query, {
                        "ticker": ticker,
                        "news_date": news_date,
                        "title": news_item.get('title', ''),
                        "link": news_item.get('link', ''),
                        "description": news_item.get('description', ''),
                        "source": source
                    })
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"뉴스 항목 저장 실패: {e}")
                    continue

            trans.commit()
            logger.info(f"뉴스 저장 완료: {ticker} {news_date} - {saved_count}건")
            return saved_count

        except Exception as e:
            trans.rollback()
            logger.exception(f"뉴스 저장 실패: {ticker} {news_date}")
            raise
        finally:
            conn.close()

    def get_news_by_ticker_date(self, ticker: str, start_date: date, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        종목과 날짜 범위로 뉴스를 조회합니다.

        Args:
            ticker: 종목 티커
            start_date: 시작 날짜
            end_date: 종료 날짜 (없으면 start_date와 동일)

        Returns:
            뉴스 리스트
        """
        if end_date is None:
            end_date = start_date

        conn = self._get_connection()

        try:
            query = text("""
                SELECT ticker, news_date, title, link, description, source, created_at
                FROM stock_news
                WHERE ticker = :ticker
                  AND news_date >= :start_date
                  AND news_date <= :end_date
                ORDER BY news_date DESC, created_at DESC
            """)

            result = conn.execute(query, {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date
            })

            news_list = []
            for row in result:
                news_list.append({
                    "ticker": row[0],
                    "news_date": row[1].strftime('%Y-%m-%d') if hasattr(row[1], 'strftime') else str(row[1]),
                    "title": row[2],
                    "link": row[3],
                    "description": row[4],
                    "source": row[5],
                    "created_at": row[6].isoformat() if hasattr(row[6], 'isoformat') else str(row[6])
                })

            return news_list

        except Exception as e:
            logger.exception(f"뉴스 조회 실패: {ticker} {start_date} ~ {end_date}")
            return []
        finally:
            conn.close()

    def check_news_exists(self, ticker: str, news_date: date) -> bool:
        """
        특정 종목의 특정 날짜 뉴스가 DB에 존재하는지 확인합니다.

        Args:
            ticker: 종목 티커
            news_date: 뉴스 날짜

        Returns:
            존재 여부
        """
        conn = self._get_connection()

        try:
            query = text("""
                SELECT COUNT(*) as count
                FROM stock_news
                WHERE ticker = :ticker AND news_date = :news_date
            """)

            result = conn.execute(query, {
                "ticker": ticker,
                "news_date": news_date
            })

            row = result.fetchone()
            return row[0] > 0 if row else False

        except Exception as e:
            logger.exception(f"뉴스 존재 여부 확인 실패: {ticker} {news_date}")
            return False
        finally:
            conn.close()

    def delete_old_news(self, days_old: int = 90) -> int:
        """
        오래된 뉴스 데이터를 삭제합니다.

        Args:
            days_old: 삭제할 뉴스의 기준 일수 (기본값: 90일)

        Returns:
            삭제된 행 수
        """
        conn = self._get_connection()
        trans = conn.begin()

        try:
            query = text("""
                DELETE FROM stock_news
                WHERE created_at < DATE_SUB(NOW(), INTERVAL :days DAY)
            """)

            result = conn.execute(query, {"days": days_old})
            deleted_count = result.rowcount

            trans.commit()
            logger.info(f"오래된 뉴스 삭제 완료: {deleted_count}건 ({days_old}일 이전)")
            return deleted_count

        except Exception as e:
            trans.rollback()
            logger.exception("오래된 뉴스 삭제 실패")
            raise
        finally:
            conn.close()


# 전역 인스턴스
news_repository = NewsRepository()
