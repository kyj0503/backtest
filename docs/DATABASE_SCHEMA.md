# 데이터베이스 스키마 가이드

본 문서는 백테스팅 시스템에서 사용하는 두 개의 주요 데이터베이스의 테이블 구조와 컬럼 정보를 상세히 설명합니다.

## 개요

시스템은 두 개의 분리된 데이터베이스를 사용합니다:
1. **Community DB** (`schema.sql`): 사용자 인증, 커뮤니티 기능, 백테스트 히스토리
2. **Stock Data Cache DB** (`yfinance.sql`): 주식 데이터 캐싱 및 금융 데이터

## Community 데이터베이스 (schema.sql)

### users 테이블
사용자 계정 정보를 저장합니다.

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    profile_image VARCHAR(500),           -- 프로필 이미지 URL
    investment_type ENUM('conservative', 'moderate', 'aggressive') DEFAULT 'moderate',
    is_admin BOOLEAN DEFAULT FALSE,       -- 관리자 권한
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### user_sessions 테이블
사용자 세션 및 토큰 관리를 위한 테이블입니다.

```sql
CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    user_agent TEXT,                      -- 브라우저 정보
    ip_address VARCHAR(45),               -- IPv4/IPv6 주소
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### posts 테이블
커뮤니티 게시글 정보를 저장합니다.

```sql
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    view_count INT UNSIGNED DEFAULT 0,    -- 조회수
    like_count INT UNSIGNED DEFAULT 0,    -- 좋아요 수
    is_deleted BOOLEAN DEFAULT FALSE,     -- 소프트 삭제
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### post_comments 테이블
게시글 댓글을 저장합니다.

```sql
CREATE TABLE post_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,     -- 소프트 삭제
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### post_likes 테이블
게시글 좋아요 정보를 저장합니다.

```sql
CREATE TABLE post_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_post_user_like (post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### reports 테이블
신고 기능을 위한 테이블입니다.

```sql
CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    reported_user_id INT,
    post_id INT,
    comment_id INT,
    report_type ENUM('spam', 'harassment', 'inappropriate', 'other') NOT NULL,
    reason TEXT,
    status ENUM('pending', 'reviewed', 'resolved', 'dismissed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE SET NULL,
    FOREIGN KEY (comment_id) REFERENCES post_comments(id) ON DELETE SET NULL
);
```

### notices 테이블
시스템 공지사항을 저장합니다.

```sql
CREATE TABLE notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_important BOOLEAN DEFAULT FALSE,   -- 중요 공지
    is_active BOOLEAN DEFAULT TRUE,       -- 활성 상태
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);
```

### backtest_history 테이블
사용자별 백테스트 실행 히스토리를 저장합니다.

```sql
CREATE TABLE backtest_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    backtest_type ENUM('single', 'portfolio') NOT NULL,
    parameters JSON NOT NULL,             -- 백테스트 실행 파라미터
    results JSON,                         -- 백테스트 결과
    execution_time_ms INT,               -- 실행 시간 (밀리초)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

## Stock Data Cache 데이터베이스 (yfinance.sql)

### stocks 테이블
주식 종목의 기본 정보를 저장합니다.

```sql
CREATE TABLE stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    exchange VARCHAR(20),
    sector VARCHAR(100),
    industry VARCHAR(100),
    summary TEXT,
    info_json JSON,                       -- yfinance의 'info' 전체 데이터
    last_info_update TIMESTAMP NULL,
    data_last_update TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### daily_prices 테이블
일별 주가 데이터(OHLCV)를 저장합니다.

```sql
CREATE TABLE daily_prices (
    stock_id INT NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(19, 4) NOT NULL,
    high DECIMAL(19, 4) NOT NULL,
    low DECIMAL(19, 4) NOT NULL,
    close DECIMAL(19, 4) NOT NULL,
    adj_close DECIMAL(19, 4),
    volume BIGINT UNSIGNED DEFAULT 0,
    data_quality ENUM('good', 'estimated', 'suspicious') DEFAULT 'good',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_id, date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
);
```

### dividends 테이블
배당금 지급 이력을 저장합니다.

```sql
CREATE TABLE dividends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    date DATE NOT NULL,
    dividend DECIMAL(19, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_stock_date (stock_id, date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
);
```

### stock_splits 테이블
주식 분할 이벤트 이력을 저장합니다.

```sql
CREATE TABLE stock_splits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    date DATE NOT NULL,
    split_ratio FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_stock_date (stock_id, date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
);
```

### financial_statements 테이블
재무제표 정보를 JSON 형태로 저장합니다.

```sql
CREATE TABLE financial_statements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    report_type ENUM('income_statement', 'balance_sheet', 'cash_flow') NOT NULL,
    period_type ENUM('annual', 'quarterly') NOT NULL,
    report_date DATE NOT NULL,
    statement_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_financial_report (stock_id, report_type, period_type, report_date),
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
);
```

### exchange_rates 테이블
환율 정보를 저장합니다.

```sql
CREATE TABLE exchange_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,  -- 예: KRW=X, EUR=X
    date DATE NOT NULL,
    rate DECIMAL(19, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_currency_date (currency_pair, date)
);
```

### cache_metadata 테이블
데이터 캐시의 메타정보와 상태를 관리합니다.

```sql
CREATE TABLE cache_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    data_type ENUM('prices', 'info', 'dividends', 'splits', 'exchange') NOT NULL,
    last_fetch TIMESTAMP NOT NULL,
    next_update TIMESTAMP NULL,
    fetch_status ENUM('success', 'failed', 'partial') DEFAULT 'success',
    error_message TEXT NULL,
    fetch_count INT UNSIGNED DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ticker_type (ticker, data_type)
);
```

## 인덱스 최적화

### Community DB 인덱스
- `users`: `username`, `email` (UNIQUE), `is_admin`, `investment_type`
- `user_sessions`: `session_token` (UNIQUE), `user_id`, `expires_at`
- `posts`: `user_id`, `created_at`, `is_deleted`, `view_count`, `like_count`
- `post_comments`: `post_id`, `user_id`, `created_at`, `is_deleted`
- `post_likes`: `(post_id, user_id)` (UNIQUE)
- `reports`: `reporter_id`, `status`, `created_at`
- `notices`: `is_active`, `is_important`, `created_at`
- `backtest_history`: `user_id`, `backtest_type`, `created_at`

### Stock Data Cache DB 인덱스
- `stocks`: `ticker` (UNIQUE), `data_last_update`
- `daily_prices`: `(stock_id, date)` (PRIMARY), `date`, `(stock_id, date DESC)`
- `dividends`: `(stock_id, date)` (UNIQUE), `date`
- `stock_splits`: `(stock_id, date)` (UNIQUE), `date`
- `financial_statements`: `(stock_id, report_type, period_type, report_date)` (UNIQUE)
- `exchange_rates`: `(currency_pair, date)` (UNIQUE), `currency_pair`, `date`
- `cache_metadata`: `(ticker, data_type)` (UNIQUE), `next_update`, `last_fetch`, `fetch_status`

## 데이터 품질 및 제약사항

### 검증 규칙
1. **가격 데이터**: 모든 가격은 0 이상, high >= low 제약
2. **중복 방지**: 날짜별 데이터는 UNIQUE KEY로 중복 방지
3. **소프트 삭제**: 게시글/댓글은 `is_deleted` 플래그 사용
4. **데이터 품질**: `daily_prices`에 품질 등급 관리
5. **외래키 무결성**: CASCADE 삭제로 참조 무결성 보장

### 성능 고려사항
1. **파티셀링**: 대용량 price 데이터는 날짜 기반 파티셔닝 고려
2. **캐시 전략**: 자주 조회되는 최근 데이터 우선 캐싱
3. **배치 처리**: 대량 데이터 삽입 시 벌크 연산 사용

## 마이그레이션

기존 데이터베이스 업그레이드를 위한 마이그레이션 스크립트는 `database/yfinance_migration_001.sql`에서 제공됩니다. 이 스크립트는 멱등성을 보장하여 안전한 반복 실행이 가능합니다.
