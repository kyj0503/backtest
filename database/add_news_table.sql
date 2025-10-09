-- =================================================================
-- 뉴스 테이블 추가 스크립트
-- 기존 DB에 stock_news 테이블을 추가합니다.
-- =================================================================

USE stock_data_cache;

-- stock_news 테이블이 이미 존재하면 삭제 후 재생성
DROP TABLE IF EXISTS stock_news;

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

SELECT 'stock_news 테이블 생성이 완료되었습니다.' AS message;

-- 생성된 테이블 확인
SHOW TABLES;

-- stock_news 테이블 구조 확인
DESC stock_news;
