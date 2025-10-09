-- =================================================================
-- yfinance 데이터 캐싱 및 뉴스 데이터 저장을 위한 데이터베이스 및 테이블 생성 DDL
-- 대상 DBMS: MySQL 8.0+
-- =================================================================

-- 1. 데이터베이스 생성 (이미 존재하면 생성하지 않음)
-- utf8mb4_0900_ai_ci는 MySQL 8.0의 권장 콜레이션입니다.
CREATE DATABASE IF NOT EXISTS stock_data_cache
    CHARACTER SET = 'utf8mb4'
    COLLATE = 'utf8mb4_0900_ai_ci';

-- 2. 생성된 데이터베이스 사용
USE stock_data_cache;

-- 3. 테이블 생성
-- 실행 시 오류를 방지하기 위해 기존 테이블이 있다면 삭제 후 재생성합니다.

DROP TABLE IF EXISTS stock_news;
DROP TABLE IF EXISTS daily_prices;
DROP TABLE IF EXISTS stocks;


-- === `stocks` 테이블: 주식 기본 정보 ===
-- 각 주식(티커)의 고유 정보와 자주 변하지 않는 데이터를 저장합니다.
CREATE TABLE stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,          -- 주식 티커 (예: AAPL, 005930.KS)
    name VARCHAR(255),                            -- 회사명 (예: Apple Inc.)
    exchange VARCHAR(20),                         -- 거래소 (예: NMS, KSC)
    sector VARCHAR(100),                          -- 섹터
    industry VARCHAR(100),                        -- 산업
    summary TEXT,                                 -- 회사 요약
    info_json JSON,                               -- yfinance의 'info' 전체를 저장할 JSON 필드
    last_info_update TIMESTAMP NULL,              -- 정보 마지막 업데이트 시각
    data_last_update TIMESTAMP NULL,              -- 데이터 마지막 업데이트 시각
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_last_update (data_last_update)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT '주식 종목의 기본 정보를 저장하는 테이블';


-- === `daily_prices` 테이블: 일별 시세 정보 ===
-- 가장 빈번하게 조회되고 데이터가 많이 쌓이는 테이블입니다.
CREATE TABLE daily_prices (
    stock_id INT NOT NULL,                        -- stocks 테이블의 ID (Foreign Key)
    date DATE NOT NULL,                           -- 날짜
    open DECIMAL(19, 4) NOT NULL,                 -- 시가
    high DECIMAL(19, 4) NOT NULL,                 -- 고가
    low DECIMAL(19, 4) NOT NULL,                  -- 저가
    close DECIMAL(19, 4) NOT NULL,                -- 종가
    adj_close DECIMAL(19, 4),                     -- 수정 종가
    volume BIGINT UNSIGNED DEFAULT 0,             -- 거래량 (음수 없음)
    data_quality ENUM('good', 'estimated', 'suspicious') DEFAULT 'good', -- 데이터 품질
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_id, date),                 -- 복합 기본 키
    INDEX idx_date_range (date),                  -- 날짜 범위 조회 최적화
    INDEX idx_stock_date_desc (stock_id, date DESC), -- 종목별 최신 데이터 조회 최적화
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    CONSTRAINT chk_prices_positive CHECK (open >= 0 AND high >= 0 AND low >= 0 AND close >= 0),
    CONSTRAINT chk_high_low CHECK (high >= low)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT '일별 주가 정보 (OHLCV)';


-- === `stock_news` 테이블: 종목별 뉴스 정보 ===
-- 네이버 뉴스 API 등에서 가져온 종목 관련 뉴스를 캐싱합니다.
CREATE TABLE stock_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,                  -- 주식 티커 (예: AAPL, 005930.KS)
    news_date DATE NOT NULL,                      -- 뉴스 날짜 (변동성 발생일)
    title VARCHAR(500) NOT NULL,                  -- 뉴스 제목
    link VARCHAR(1000),                           -- 뉴스 링크
    description TEXT,                             -- 뉴스 요약
    source VARCHAR(100),                          -- 뉴스 출처 (예: 네이버)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '저장일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    INDEX idx_ticker (ticker),
    INDEX idx_news_date (news_date),
    INDEX idx_ticker_date (ticker, news_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT '종목별 뉴스 캐시';


-- 스크립트 완료 --
SELECT '데이터베이스와 테이블 생성이 완료되었습니다.' AS message;

-- 생성된 테이블 확인
SHOW TABLES;

-- 인덱스 확인
SELECT
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'stock_data_cache'
    AND TABLE_NAME IN ('stocks', 'daily_prices', 'stock_news')
ORDER BY TABLE_NAME, INDEX_NAME;
