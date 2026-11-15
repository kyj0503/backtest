"""stock_news unique key and drop redundant indexes

Revision ID: d5c3763b29e6
Revises: 622933e2fe2e
Create Date: 2026-08-03 00:29:05.878138

P3-09 + P3-10: 두 감사 항목이 같은 세 테이블(stocks, daily_prices, stock_news)의
인덱스 정의를 건드리므로 하나의 리비전으로 묶는다.

P3-09 (stock_news 중복 방지):
  UNIQUE 인덱스 uq_ticker_date_link (ticker, news_date, link(255))를 추가한다.
  기존에는 ticker별 dedup이 애플리케이션의 "티커별 DELETE 후 INSERT" 단일
  트랜잭션에만 의존했다 (app/repositories/yfinance_repository.py의
  save_news_to_db, ~712-766행). 동일 티커에 대한 두 저장이 겹치면(예: 캐시
  미스가 동시에 발생한 두 백테스트 요청) 각자 DELETE 후 겹치는 뉴스 목록을
  INSERT해 중복 행이 생길 수 있었다. link(255)는 utf8mb4 기준 1020바이트로
  ticker(80B)+news_date(3B)와 합쳐도 InnoDB DYNAMIC row format의 인덱스 접두어
  한도(3072바이트)에 안전하게 들어간다.

  FK는 추가하지 않았다: ticker는 언뜻 stocks.ticker를 참조할 후보처럼 보이지만,
  app/services/unified_data_service.py의 collect_all_unified_data()는 가격 데이터
  저장 경로(_fetch_price_histories → stocks/daily_prices 행 생성)와 뉴스 수집
  경로(collect_latest_news → stock_news 행 생성)를 ThreadPoolExecutor의 서로
  독립된 futures로 병렬 실행한다 — 두 작업 사이에 순서 보장이나 공유 트랜잭션이
  없다. 특정 티커의 가격 조회가 실패하거나 아직 커밋되지 않은 상태에서도 같은
  티커의 뉴스 저장은 독립적으로 성공할 수 있으므로, FK를 걸면 정상적인 뉴스
  저장이 FK 위반으로 실패할 위험이 있다 (database/schema.sql의 stock_news 테이블
  위 주석에 동일 근거 기록).

P3-10 (중복 인덱스 3개 제거 — 쓰기 증폭만 유발, 조회 이득 없음):
  - stocks.idx_ticker: 같은 테이블의 `ticker` UNIQUE 제약이 이미 만드는 인덱스와
    완전히 중복.
  - daily_prices.idx_stock_date_desc (stock_id, date DESC): PK (stock_id, date)와
    중복 — InnoDB는 PK(clustered index)를 역순으로도 효율적으로 스캔하므로
    "최신 N일" 조회(ORDER BY date DESC)에 별도 인덱스가 필요 없다.
  - stock_news.idx_ticker: idx_ticker_date (ticker, news_date)의 leftmost prefix와
    중복 (ticker 단독 조회도 idx_ticker_date로 처리됨).

실측 검증(mysql:8.4 스로어웨이 컨테이너에서: (1) database/schema.sql을 직접
적용한 스키마와 (2) 622933e2fe2e 위에 이 리비전까지 `alembic upgrade head`로
적용한 스키마 양쪽의 SHOW CREATE TABLE 출력이 동일함을 확인, 중복 삽입 시도가
실제로 ER_DUP_ENTRY로 거부되는지도 확인): b5-F-report.md 참고.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5c3763b29e6'
down_revision: Union[str, Sequence[str], None] = '622933e2fe2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # P3-10: 중복 인덱스 제거 (쓰기 증폭만 유발)
    op.drop_index('idx_ticker', table_name='stocks')
    op.drop_index('idx_stock_date_desc', table_name='daily_prices')
    op.drop_index('idx_ticker', table_name='stock_news')

    # P3-09: stock_news 중복 삽입을 막는 UNIQUE 인덱스.
    # link에 프리픽스 길이(255)가 필요해 (MySQL 전용 컬럼 프리픽스 인덱스)
    # op.create_unique_constraint 대신 op.create_index(unique=True) +
    # mysql_length dialect kwarg를 쓴다 — UniqueConstraint는 컬럼 프리픽스
    # 길이를 표현할 표준 방법이 없다.
    op.create_index(
        'uq_ticker_date_link',
        'stock_news',
        ['ticker', 'news_date', 'link'],
        unique=True,
        mysql_length={'link': 255},
    )


def downgrade() -> None:
    """Downgrade schema (역순)."""
    op.drop_index('uq_ticker_date_link', table_name='stock_news')

    op.create_index('idx_ticker', 'stock_news', ['ticker'])
    op.create_index('idx_stock_date_desc', 'daily_prices', ['stock_id', sa.text('date DESC')])
    op.create_index('idx_ticker', 'stocks', ['ticker'])
