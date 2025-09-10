-- =================================================================
-- yfinance 데이터베이스 업데이트 마이그레이션 스크립트
-- 대상: 기존 운영 중인 stock_data_cache 데이터베이스
-- 적용일: 2025-09-10
-- =================================================================

USE stock_data_cache;

-- 기존 데이터 백업 권장 (실행 전 확인)
-- mysqldump -u [username] -p stock_data_cache > backup_$(date +%Y%m%d_%H%M%S).sql

-- =================================================================
-- 1단계: 성능 개선을 위한 인덱스 추가 (무손실, 즉시 적용 가능)
-- =================================================================

-- daily_prices 테이블 인덱스 추가
SELECT 'Adding performance indexes for daily_prices...' AS status;

-- 날짜 범위 조회 최적화 (백테스트에서 자주 사용)
SET @sql_idx1 = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE daily_prices ADD INDEX idx_date_range (date)',
        'SELECT "Index idx_date_range already exists" AS notice'
    )
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = 'stock_data_cache' 
    AND TABLE_NAME = 'daily_prices' 
    AND INDEX_NAME = 'idx_date_range'
);

PREPARE stmt_idx1 FROM @sql_idx1;
EXECUTE stmt_idx1;
DEALLOCATE PREPARE stmt_idx1;

-- 종목별 최신 데이터 조회 최적화
SET @sql_idx2 = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE daily_prices ADD INDEX idx_stock_date_desc (stock_id, date DESC)',
        'SELECT "Index idx_stock_date_desc already exists" AS notice'
    )
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = 'stock_data_cache' 
    AND TABLE_NAME = 'daily_prices' 
    AND INDEX_NAME = 'idx_stock_date_desc'
);

PREPARE stmt_idx2 FROM @sql_idx2;
EXECUTE stmt_idx2;
DEALLOCATE PREPARE stmt_idx2;

-- dividends 테이블 인덱스 추가
SET @sql_idx3 = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE dividends ADD INDEX idx_date (date)',
        'SELECT "Index idx_date already exists on dividends" AS notice'
    )
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = 'stock_data_cache' 
    AND TABLE_NAME = 'dividends' 
    AND INDEX_NAME = 'idx_date'
);

PREPARE stmt_idx3 FROM @sql_idx3;
EXECUTE stmt_idx3;
DEALLOCATE PREPARE stmt_idx3;

-- stock_splits 테이블 인덱스 추가
SET @sql_idx4 = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE stock_splits ADD INDEX idx_date (date)',
        'SELECT "Index idx_date already exists on stock_splits" AS notice'
    )
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = 'stock_data_cache' 
    AND TABLE_NAME = 'stock_splits' 
    AND INDEX_NAME = 'idx_date'
);

PREPARE stmt_idx4 FROM @sql_idx4;
EXECUTE stmt_idx4;
DEALLOCATE PREPARE stmt_idx4;

-- =================================================================
-- 2단계: 새로운 기능을 위한 테이블 추가
-- =================================================================

-- 환율 데이터 테이블 (KRW=X 등 환율 정보 캐싱용)
SELECT 'Creating exchange_rates table...' AS status;

CREATE TABLE IF NOT EXISTS exchange_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL COMMENT '통화쌍 (예: KRW=X, EUR=X)',
    date DATE NOT NULL COMMENT '날짜',
    rate DECIMAL(19, 6) NOT NULL COMMENT '환율',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    UNIQUE KEY uq_currency_date (currency_pair, date),
    INDEX idx_currency (currency_pair),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='환율 정보';

-- 캐시 메타데이터 테이블 (데이터 신선도 관리)
SELECT 'Creating cache_metadata table...' AS status;

CREATE TABLE IF NOT EXISTS cache_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL COMMENT '종목 심볼',
    data_type ENUM('prices', 'info', 'dividends', 'splits', 'exchange') NOT NULL COMMENT '데이터 타입',
    last_fetch TIMESTAMP NOT NULL COMMENT '마지막 가져온 시간',
    next_update TIMESTAMP NULL COMMENT '다음 업데이트 예정 시간',
    fetch_status ENUM('success', 'failed', 'partial') DEFAULT 'success' COMMENT '가져오기 상태',
    error_message TEXT NULL COMMENT '오류 메시지',
    fetch_count INT UNSIGNED DEFAULT 1 COMMENT '가져오기 횟수',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    UNIQUE KEY uq_ticker_type (ticker, data_type),
    INDEX idx_next_update (next_update),
    INDEX idx_last_fetch (last_fetch),
    INDEX idx_fetch_status (fetch_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='데이터 캐시 메타정보';

-- =================================================================
-- 3단계: 데이터 무결성 검증 및 제약조건 추가 (선택적)
-- =================================================================

-- 기존 데이터 검증
SELECT 'Checking data integrity...' AS status;

-- NULL 값 체크
SELECT 
    'daily_prices' AS table_name,
    COUNT(*) AS null_close_count
FROM daily_prices 
WHERE close IS NULL;

-- 음수 값 체크
SELECT 
    'daily_prices' AS table_name,
    COUNT(*) AS negative_price_count
FROM daily_prices 
WHERE open < 0 OR high < 0 OR low < 0 OR close < 0;

-- 논리적 오류 체크 (고가 < 저가)
SELECT 
    'daily_prices' AS table_name,
    COUNT(*) AS invalid_high_low_count
FROM daily_prices 
WHERE high < low;

-- 제약조건 추가 (위 검증에서 문제없을 경우에만 실행)
-- ALTER TABLE daily_prices ADD CONSTRAINT chk_prices_positive 
-- CHECK (open >= 0 AND high >= 0 AND low >= 0 AND close >= 0);

-- ALTER TABLE daily_prices ADD CONSTRAINT chk_high_low 
-- CHECK (high >= low);

-- =================================================================
-- 4단계: 기존 테이블 개선 (선택적)
-- =================================================================

-- stocks 테이블에 마지막 업데이트 추적 컬럼 추가 (이미 있다면 무시)
SELECT 'Adding columns to existing tables...' AS status;

-- 컬럼 존재 여부 확인 후 추가
SET @sql_stocks = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE stocks ADD COLUMN data_last_update TIMESTAMP NULL COMMENT "데이터 마지막 업데이트"',
        'SELECT "Column data_last_update already exists in stocks table" AS notice'
    )
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'stock_data_cache' 
    AND TABLE_NAME = 'stocks' 
    AND COLUMN_NAME = 'data_last_update'
);

PREPARE stmt_stocks FROM @sql_stocks;
EXECUTE stmt_stocks;
DEALLOCATE PREPARE stmt_stocks;

-- daily_prices 테이블에 데이터 품질 플래그 추가 (선택적)
SET @sql_daily = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE daily_prices ADD COLUMN data_quality ENUM("good", "estimated", "suspicious") DEFAULT "good" COMMENT "데이터 품질"',
        'SELECT "Column data_quality already exists in daily_prices table" AS notice'
    )
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'stock_data_cache' 
    AND TABLE_NAME = 'daily_prices' 
    AND COLUMN_NAME = 'data_quality'
);

PREPARE stmt_daily FROM @sql_daily;
EXECUTE stmt_daily;
DEALLOCATE PREPARE stmt_daily;

-- =================================================================
-- 완료 메시지
-- =================================================================

SELECT CONCAT(
    'Migration completed successfully at ', 
    NOW(), 
    '. Please verify the new indexes and tables.'
) AS completion_message;

-- 추가된 인덱스 확인
SHOW INDEX FROM daily_prices WHERE Key_name LIKE 'idx_%';
SHOW INDEX FROM dividends WHERE Key_name LIKE 'idx_%';
SHOW INDEX FROM stock_splits WHERE Key_name LIKE 'idx_%';

-- 새 테이블 확인
SHOW TABLES LIKE '%exchange%';
SHOW TABLES LIKE '%cache%';
