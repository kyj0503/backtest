"""initial schema

Revision ID: 622933e2fe2e
Revises:
Create Date: 2026-08-02 14:16:53.737978

P2-28: 이 마이그레이션은 database/schema.sql의 DROP+CREATE DDL(stocks,
daily_prices, stock_news)을 alembic 리비전으로 옮긴 것이다. 두 파일의 관계:

- database/schema.sql: 최초 부팅 경로. compose*.yaml이
  docker-entrypoint-initdb.d에 마운트하므로, MySQL 컨테이너가 빈 데이터
  디렉터리로 최초 기동할 때 공식 mysql 이미지가 자동으로 1회 실행한다
  (CREATE DATABASE 포함). 이 마이그레이션은 그 실행에 관여하지 않는다 —
  이미 존재하는 컨테이너를 재시작해도 initdb.d는 다시 돌지 않는다.
- alembic (이 디렉터리): 이미 떠 있는(스키마가 있는 없든) DB에 대해 이후의
  스키마 변경을 순서대로 적용하는 경로. DATABASE_URL이 가리키는 DB가 이미
  존재한다고 가정한다(CREATE DATABASE를 실행하지 않는다) — DB 자체 생성과
  charset/collation은 여전히 schema.sql/MYSQL_DATABASE 환경변수의 몫이다.

즉 "처음 컨테이너를 띄울 때"는 schema.sql이 스키마를 만들고, 그 이후 스키마를
바꿔야 할 때는 (schema.sql을 다시 손대는 대신) 여기에 새 리비전을 추가한다.
`alembic upgrade head`를 빈 DB에 대해 실행하면 이 리비전이 schema.sql과
동일한 테이블/인덱스/제약조건을 만든다 (직접 검증: mysql:8.4 throwaway
컨테이너에 적용 후 SHOW CREATE TABLE로 비교, b4-E-report.md 참고).

이 리포지토리는 SQLAlchemy ORM 모델(Declarative Base)을 쓰지 않고 raw SQL/Core
(app/services/database/connection_manager.py의 Engine)로 DB에 접근하므로
autogenerate용 target_metadata가 없다(alembic/env.py 참고) — 이후 리비전들도
schema.sql과 마찬가지로 손으로 작성해야 한다.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '622933e2fe2e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    테이블 생성 순서는 FK 의존성을 따른다: stocks -> daily_prices(FK ->
    stocks.id). stock_news는 ticker를 FK로 참조하지 않는다(schema.sql과
    동일 — 의도적으로 느슨하게 결합됨).
    """
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False, comment='주식 티커 (예: AAPL, 005930.KS)'),
        sa.Column('name', sa.String(255), nullable=True, comment='회사명 (예: Apple Inc.)'),
        sa.Column('exchange', sa.String(20), nullable=True, comment='거래소 (예: NMS, KSC)'),
        sa.Column('sector', sa.String(100), nullable=True, comment='섹터'),
        sa.Column('industry', sa.String(100), nullable=True, comment='산업'),
        sa.Column('summary', sa.Text(), nullable=True, comment='회사 요약'),
        sa.Column('info_json', sa.JSON(), nullable=True, comment="yfinance의 'info' 전체를 저장할 JSON 필드"),
        sa.Column('last_info_update', sa.TIMESTAMP(), nullable=True, comment='정보 마지막 업데이트 시각'),
        sa.Column('data_last_update', sa.TIMESTAMP(), nullable=True, comment='데이터 마지막 업데이트 시각'),
        sa.Column('last_split_date', sa.Date(), nullable=True, comment='최근 주가 분할/병합 날짜'),
        sa.Column('last_split_ratio', sa.DECIMAL(10, 6), nullable=True, comment='최근 분할 비율 (2.0 = 1:2 분할, 0.1 = 10:1 병합)'),
        sa.Column('splits_updated_at', sa.DateTime(), nullable=True, comment='분할 정보 마지막 업데이트 시각'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci',
        comment='주식 종목의 기본 정보를 저장하는 테이블',
    )
    op.create_index('idx_ticker', 'stocks', ['ticker'])
    op.create_index('idx_last_update', 'stocks', ['data_last_update'])
    op.create_index('idx_splits_updated_at', 'stocks', ['splits_updated_at'])

    op.create_table(
        'daily_prices',
        sa.Column('stock_id', sa.Integer(), nullable=False, comment='stocks 테이블의 ID (Foreign Key)'),
        sa.Column('date', sa.Date(), nullable=False, comment='날짜'),
        sa.Column('open', sa.DECIMAL(19, 4), nullable=False, comment='시가'),
        sa.Column('high', sa.DECIMAL(19, 4), nullable=False, comment='고가'),
        sa.Column('low', sa.DECIMAL(19, 4), nullable=False, comment='저가'),
        sa.Column('close', sa.DECIMAL(19, 4), nullable=False, comment='종가'),
        sa.Column('adj_close', sa.DECIMAL(19, 4), nullable=True, comment='수정 종가'),
        sa.Column('volume', mysql.BIGINT(unsigned=True), server_default=sa.text('0'), nullable=True, comment='거래량 (음수 없음)'),
        sa.Column('data_quality', mysql.ENUM('good', 'estimated', 'suspicious'), server_default=sa.text("'good'"), nullable=True, comment='데이터 품질'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('stock_id', 'date'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.CheckConstraint('open >= 0 AND high >= 0 AND low >= 0 AND close >= 0', name='chk_prices_positive'),
        sa.CheckConstraint('high >= low', name='chk_high_low'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci',
        comment='일별 주가 정보 (OHLCV)',
    )
    op.create_index('idx_date_range', 'daily_prices', ['date'])
    op.create_index('idx_stock_date_desc', 'daily_prices', ['stock_id', sa.text('date DESC')])

    op.create_table(
        'stock_news',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False, comment='주식 티커 (예: AAPL, 005930.KS)'),
        sa.Column('news_date', sa.Date(), nullable=False, comment='뉴스 날짜 (변동성 발생일)'),
        sa.Column('title', sa.String(500), nullable=False, comment='뉴스 제목'),
        sa.Column('link', sa.String(1000), nullable=True, comment='뉴스 링크'),
        sa.Column('description', sa.Text(), nullable=True, comment='뉴스 요약'),
        sa.Column('source', sa.String(100), nullable=True, comment='뉴스 출처 (예: 네이버)'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='저장일'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='수정일'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci',
        comment='종목별 뉴스 캐시',
    )
    op.create_index('idx_ticker', 'stock_news', ['ticker'])
    op.create_index('idx_news_date', 'stock_news', ['news_date'])
    op.create_index('idx_ticker_date', 'stock_news', ['ticker', 'news_date'])
    op.create_index('idx_created_at', 'stock_news', ['created_at'])


def downgrade() -> None:
    """Downgrade schema (역순: FK가 걸린 daily_prices를 stocks보다 먼저 제거)."""
    op.drop_table('stock_news')
    op.drop_table('daily_prices')
    op.drop_table('stocks')
