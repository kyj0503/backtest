-- =================================================================
-- 미사용 테이블 삭제 스크립트
-- MySQL 서버에 이미 생성된 미사용 테이블들을 삭제합니다.
-- =================================================================

USE stock_data_cache;

-- 외래키 제약조건이 있는 테이블부터 삭제해야 합니다.
DROP TABLE IF EXISTS cache_metadata;
DROP TABLE IF EXISTS exchange_rates;
DROP TABLE IF EXISTS financial_statements;
DROP TABLE IF EXISTS stock_splits;
DROP TABLE IF EXISTS dividends;

SELECT '미사용 테이블 삭제가 완료되었습니다.' AS message;

-- 남은 테이블 확인
SHOW TABLES;
