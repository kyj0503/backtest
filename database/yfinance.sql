-- =================================================================
-- yfinance 데이터 캐싱을 위한 데이터베이스 및 테이블 생성 DDL
-- 대상 DBMS: MySQL 8.0
-- =================================================================

-- 1. 데이터베이스 생성 (이미 존재하면 생성하지 않음)
-- utf8mb4 문자셋은 이모지 등 다양한 문자를 지원하는 표준입니다.
CREATE DATABASE IF NOT EXISTS stock_data_cache
    CHARACTER SET = 'utf8mb4'
    COLLATE = 'utf8mb4_unicode_ci';

-- 2. 생성된 데이터베이스 사용
USE stock_data_cache;

-- 3. 테이블 생성
-- 실행 시 오류를 방지하기 위해 기존 테이블이 있다면 삭제 후 재생성합니다.

DROP TABLE IF EXISTS financial_statements;
DROP TABLE IF EXISTS stock_splits;
DROP TABLE IF EXISTS dividends;
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker)
) COMMENT '주식 종목의 기본 정보를 저장하는 테이블';


-- === `daily_prices` 테이블: 일별 시세 정보 ===
-- 가장 빈번하게 조회되고 데이터가 많이 쌓이는 테이블입니다.
CREATE TABLE daily_prices (
    stock_id INT NOT NULL,                        -- stocks 테이블의 ID (Foreign Key)
    date DATE NOT NULL,                           -- 날짜
    open DECIMAL(19, 4),                          -- 시가
    high DECIMAL(19, 4),                          -- 고가
    low DECIMAL(19, 4),                           -- 저가
    close DECIMAL(19, 4),                         -- 종가
    adj_close DECIMAL(19, 4),                     -- 수정 종가
    volume BIGINT UNSIGNED,                       -- 거래량 (음수 없음)
    PRIMARY KEY (stock_id, date),                 -- 복합 기본 키
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
) COMMENT '일별 주가 정보 (OHLCV)';


-- === `dividends` 테이블: 배당 정보 ===
-- 배당금 지급 이력을 저장합니다.
CREATE TABLE dividends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    date DATE NOT NULL,
    dividend DECIMAL(19, 4),
    UNIQUE KEY uq_stock_date (stock_id, date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
) COMMENT '배당금 지급 이력';


-- === `stock_splits` 테이블: 주식 분할 정보 ===
-- 주식 분할 이벤트 이력을 저장합니다.
CREATE TABLE stock_splits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    date DATE NOT NULL,
    split_ratio FLOAT NOT NULL,                  -- 분할 비율 (예: 2:1 분할 시 2.0)
    UNIQUE KEY uq_stock_date (stock_id, date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
) COMMENT '주식 분할 이력';


-- === `financial_statements` 테이블: 재무제표 정보 ===
-- 손익계산서, 대차대조표, 현금흐름표 데이터를 JSON 형태로 저장합니다.
CREATE TABLE financial_statements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    report_type ENUM('income_statement', 'balance_sheet', 'cash_flow') NOT NULL, -- 재무제표 종류
    period_type ENUM('annual', 'quarterly') NOT NULL, -- 기간 종류 (연간/분기별)
    report_date DATE NOT NULL,                                                 -- 보고서 기준일
    statement_data JSON NOT NULL,                                              -- 재무제표 전체 데이터
    UNIQUE KEY uq_financial_report (stock_id, report_type, period_type, report_date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
) COMMENT '재무제표 데이터';


-- 스크립트 완료 --
SELECT '데이터베이스와 테이블 생성이 완료되었습니다.' AS message;