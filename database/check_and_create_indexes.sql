-- MySQL 인덱스 확인 및 생성 스크립트
-- 성능 최적화를 위한 daily_prices 테이블 인덱스

-- 현재 인덱스 확인
SHOW INDEX FROM daily_prices;

-- 복합 인덱스 생성 (ticker, date)
-- 이 인덱스는 특정 ticker의 날짜 범위 조회를 크게 가속화합니다
-- 예: SELECT * FROM daily_prices WHERE ticker = 'AAPL' AND date BETWEEN '2023-01-01' AND '2023-12-31'
CREATE INDEX IF NOT EXISTS idx_ticker_date ON daily_prices(ticker, date);

-- date 단독 인덱스 (옵션)
-- 전체 시장 데이터를 날짜별로 조회하는 경우 유용
-- CREATE INDEX IF NOT EXISTS idx_date ON daily_prices(date);

-- 인덱스 생성 후 확인
SHOW INDEX FROM daily_prices;

-- 인덱스 사용 통계 확인 (MySQL 5.7+)
-- SELECT * FROM information_schema.INNODB_SYS_INDEXES
-- WHERE TABLE_ID IN (SELECT TABLE_ID FROM information_schema.INNODB_SYS_TABLES WHERE NAME = 'backtest/daily_prices');

-- 쿼리 성능 확인 (EXPLAIN 사용)
EXPLAIN SELECT * FROM daily_prices WHERE ticker = 'AAPL' AND date BETWEEN '2023-01-01' AND '2023-12-31';
