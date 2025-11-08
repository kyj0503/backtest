-- MySQL 인덱스 검증 스크립트
-- daily_prices 테이블의 성능 최적화 인덱스 확인
--
-- 참고: schema.sql로 생성된 데이터베이스는 이미 최적의 인덱스를 가지고 있습니다.
-- 이 스크립트는 기존 DB의 인덱스 상태를 확인하는 용도입니다.

-- 현재 인덱스 확인
SHOW INDEX FROM daily_prices;

-- 필수 인덱스 확인
-- daily_prices 테이블에 다음 인덱스가 있어야 합니다:
--
-- 1. PRIMARY KEY (stock_id, date)
--    - 종목별 날짜 범위 조회에 최적 (가장 중요!)
--    - 예: WHERE stock_id = X AND date BETWEEN '2023-01-01' AND '2023-12-31'
--
-- 2. INDEX idx_date_range (date)
--    - 전체 종목의 특정 날짜 조회에 사용
--
-- 3. INDEX idx_stock_date_desc (stock_id, date DESC)
--    - 종목별 최신 데이터 조회 최적화 (예: 최근 N일 데이터)

-- 인덱스 존재 여부 확인 쿼리
SELECT
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    INDEX_TYPE,
    COLLATION
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'daily_prices'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- 쿼리 성능 확인 (EXPLAIN 사용)
-- 실제 사용되는 쿼리 패턴 테스트
-- stock_id는 stocks 테이블과 조인하여 ticker로 변환됩니다
EXPLAIN SELECT dp.date, dp.open, dp.high, dp.low, dp.close, dp.adj_close, dp.volume
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.id
WHERE s.ticker = 'AAPL'
  AND dp.date BETWEEN '2023-01-01' AND '2023-12-31'
ORDER BY dp.date ASC;

-- 성능 통계
SELECT
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY,
    INDEX_TYPE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'daily_prices'
GROUP BY INDEX_NAME, TABLE_NAME, CARDINALITY, INDEX_TYPE;
