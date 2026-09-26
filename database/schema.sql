-- =================================================================
-- yfinance 데이터 캐싱 및 뉴스 데이터 저장을 위한 데이터베이스 및 테이블 생성 DDL
-- 대상 DBMS: MySQL 8.4 (8.0+ 문법)
--
-- 스키마 변경은 이 파일과 Alembic 새 리비전(backtest_be_fast/alembic/versions/)을
-- 함께 고친다. 두 경로(빈 DB에 이 파일로 initdb / `alembic upgrade head`)의
-- 최종 스키마는 COMMENT까지 같아야 하며, scripts/check-schema-parity.sh로
-- 확인한다 (A-11). 컬럼 설명은 `--` 주석이 아니라 COMMENT 절로 적는다 —
-- Alembic 리비전이 같은 문구를 COMMENT로 만들기 때문이다.
-- =================================================================

-- 0. 클라이언트 문자셋 고정 (A-11)
-- 공식 mysql 이미지의 initdb는 로케일이 POSIX인 mysql 클라이언트로 이 파일을
-- 실행하고, 그 클라이언트의 기본 연결 문자셋은 latin1이다. SET NAMES가 없으면
-- 아래 한글 COMMENT가 UTF-8 바이트를 latin1로 읽은 이중 인코딩(예: '주식' →
-- 'ì£¼ì‹')으로 저장된다 — mysql:8.4 initdb 실측(character_set_client=latin1).
SET NAMES utf8mb4;

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
    ticker VARCHAR(20) NOT NULL UNIQUE COMMENT '주식 티커 (예: AAPL, 005930.KS)',
    name VARCHAR(255) COMMENT '회사명 (예: Apple Inc.)',
    exchange VARCHAR(20) COMMENT '거래소 (예: NMS, KSC)',
    sector VARCHAR(100) COMMENT '섹터',
    industry VARCHAR(100) COMMENT '산업',
    summary TEXT COMMENT '회사 요약',
    info_json JSON COMMENT 'yfinance의 ''info'' 전체를 저장할 JSON 필드',
    last_info_update TIMESTAMP NULL COMMENT '정보 마지막 업데이트 시각',
    data_last_update TIMESTAMP NULL COMMENT '데이터 마지막 업데이트 시각',
    last_split_date DATE DEFAULT NULL COMMENT '최근 주가 분할/병합 날짜',
    last_split_ratio DECIMAL(10, 6) DEFAULT NULL COMMENT '최근 분할 비율 (2.0 = 1:2 분할, 0.1 = 10:1 병합)',
    splits_updated_at DATETIME DEFAULT NULL COMMENT '분할 정보 마지막 업데이트 시각',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- P3-10: idx_ticker를 제거했다. 위 `ticker VARCHAR(20) NOT NULL UNIQUE`가
    -- 이미 동일 컬럼에 인덱스를 자동 생성하므로 별도 INDEX는 쓰기 증폭만 유발했다.
    INDEX idx_last_update (data_last_update),
    INDEX idx_splits_updated_at (splits_updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT '주식 종목의 기본 정보를 저장하는 테이블';


-- === `daily_prices` 테이블: 일별 시세 정보 ===
-- 가장 빈번하게 조회되고 데이터가 많이 쌓이는 테이블입니다.
--
-- 성능 최적화:
-- 1. PRIMARY KEY (stock_id, date): 종목별 날짜 범위 조회에 최적 (가장 중요!)
--    - WHERE stock_id = X AND date BETWEEN Y AND Z 쿼리에 사용
--    - 추가 인덱스 불필요 (이미 최적 성능 제공)
-- 2. INDEX idx_date_range (date): 전체 종목의 특정 날짜 조회
-- (P3-10: idx_stock_date_desc (stock_id, date DESC)는 제거했다. PK가 이미
--  (stock_id, date)를 커버하는 clustered index이고, InnoDB는 이를 역순으로도
--  효율적으로 스캔하므로 "최신 N일" 조회(ORDER BY date DESC)에 별도 인덱스가
--  필요 없다 — 모든 INSERT/UPDATE/DELETE에서 추가로 유지비용만 냈다.)
--
-- 물리 FK 없음 (A-10, 2026-09-26): stock_id는 stocks.id를 가리키는 논리 참조다.
-- 과거의 FOREIGN KEY ... ON DELETE CASCADE는 한 번도 발동한 적이 없고(코드에
-- DELETE FROM stocks 경로 없음), stocks 삭제 기능이 생기면 코드에 드러나지 않은
-- 채 일봉 전체를 지우는 위험만 있었다. 참조 무결성은 애플리케이션이 맡는다:
-- - 저장: save_ticker_data()가 한 트랜잭션에서 부모 upsert → id 조회 → 자식 저장
-- - 삭제: stocks 행을 지우는 경로는 없다. 일봉은 명시적 DELETE로만 지운다
--   (manage_stock_splits.py의 분할 재수집). stocks 삭제 기능을 추가한다면
--   같은 트랜잭션에서 daily_prices를 먼저 지울 것
-- - 고아 점검: backtest_be_fast/scripts/check_orphan_prices.py
-- stock_news와 같은 방침이다 (아래 stock_news 주석 참고).
CREATE TABLE daily_prices (
    stock_id INT NOT NULL COMMENT 'stocks.id 논리 참조 (물리 FK 없음)',
    date DATE NOT NULL COMMENT '날짜',
    open DECIMAL(19, 4) NOT NULL COMMENT '시가',
    high DECIMAL(19, 4) NOT NULL COMMENT '고가',
    low DECIMAL(19, 4) NOT NULL COMMENT '저가',
    close DECIMAL(19, 4) NOT NULL COMMENT '종가',
    adj_close DECIMAL(19, 4) COMMENT '수정 종가',
    volume BIGINT UNSIGNED DEFAULT 0 COMMENT '거래량 (음수 없음)',
    data_quality ENUM('good', 'estimated', 'suspicious') DEFAULT 'good' COMMENT '데이터 품질',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_id, date),                 -- 복합 기본 키 (성능 최적화의 핵심)
    INDEX idx_date_range (date),                  -- 날짜 범위 조회 최적화
    CONSTRAINT chk_prices_positive CHECK (open >= 0 AND high >= 0 AND low >= 0 AND close >= 0),
    CONSTRAINT chk_high_low CHECK (high >= low)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT '일별 주가 정보 (OHLCV)';


-- === `stock_news` 테이블: 종목별 뉴스 정보 ===
-- 네이버 뉴스 API 등에서 가져온 종목 관련 뉴스를 캐싱합니다.
--
-- P3-09: UNIQUE KEY uq_ticker_date_link로 중복 삽입을 DB 레벨에서 막는다.
-- 기존에는 ticker별 dedup을 애플리케이션(yfinance_repository.py의
-- save_news_to_db, "티커별 DELETE 후 INSERT" 단일 트랜잭션)에만 의존했는데,
-- 동일 티커에 대한 두 저장이 겹치면(예: 캐시 미스가 동시에 발생한 두 백테스트
-- 요청) 각자 DELETE 후 겹치는 뉴스 목록을 INSERT해 중복 행이 생길 수 있었다.
-- link(255)는 utf8mb4 기준 255*4=1020바이트로, ticker(80B)+news_date(3B)와
-- 합쳐도 InnoDB DYNAMIC row format의 인덱스 접두어 한도(3072바이트)에 안전하게
-- 들어간다 (실측: mysql:8.4 컨테이너에 SHOW CREATE TABLE로 확인, b5-F-report.md).
--
-- FK는 추가하지 않았다: ticker는 언뜻 stocks.ticker를 참조할 후보처럼 보이지만,
-- app/services/unified_data_service.py의 collect_all_unified_data()는 가격 데이터
-- 저장 경로(_fetch_price_histories → stocks/daily_prices 행 생성)와 뉴스 수집
-- 경로(collect_latest_news → stock_news 행 생성)를 ThreadPoolExecutor의 서로
-- 독립된 futures로 병렬 실행한다 — 두 작업 사이에 순서 보장이나 공유 트랜잭션이
-- 없다. 특정 티커의 가격 조회가 실패하거나(예: 유효하지 않은 심볼) 아직
-- 커밋되지 않은 상태에서도 같은 티커의 뉴스 저장은 독립적으로 성공할 수 있으므로,
-- FK를 걸면 정상적인 뉴스 저장이 FK 위반으로 실패할 위험이 있다.
CREATE TABLE stock_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL COMMENT '주식 티커 (예: AAPL, 005930.KS)',
    news_date DATE NOT NULL COMMENT '뉴스 날짜 (변동성 발생일)',
    title VARCHAR(500) NOT NULL COMMENT '뉴스 제목',
    link VARCHAR(1000) COMMENT '뉴스 링크',
    description TEXT COMMENT '뉴스 요약',
    source VARCHAR(100) COMMENT '뉴스 출처 (예: 네이버)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '저장일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    -- P3-10: idx_ticker를 제거했다. idx_ticker_date (ticker, news_date)가 이미
    -- ticker를 최좌측 컬럼으로 포함하므로(leftmost prefix), ticker 단독 조회도
    -- idx_ticker_date로 처리된다 — idx_ticker는 그 접두어와 완전히 중복이었다.
    INDEX idx_news_date (news_date),
    INDEX idx_ticker_date (ticker, news_date),
    INDEX idx_created_at (created_at),
    UNIQUE KEY uq_ticker_date_link (ticker, news_date, link(255))
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
