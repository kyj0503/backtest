
-- MySQL schema for authentication, sessions, and community board (improved)
-- Charset/Collation: utf8mb4_0900_ai_ci for full Unicode (including emoji)

SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET FOREIGN_KEY_CHECKS=0;


CREATE TABLE IF NOT EXISTS users (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  username        VARCHAR(50)     NOT NULL COMMENT '닉네임',
  email           VARCHAR(255)    NOT NULL COMMENT '이메일',
  password_hash   VARBINARY(255)  NOT NULL COMMENT '비밀번호 해시',
  password_salt   VARBINARY(128)  NOT NULL COMMENT '비밀번호 솔트',
  password_algo   VARCHAR(50)     NOT NULL DEFAULT 'pbkdf2_sha256' COMMENT '해시 알고리즘',
  profile_image   VARCHAR(500)    DEFAULT NULL COMMENT '프로필 이미지 URL',
  investment_type ENUM('conservative', 'moderate', 'balanced', 'aggressive', 'speculative') DEFAULT 'balanced' COMMENT '투자 성향',
  is_admin        TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '관리자 여부',
  is_deleted      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_username (username),
  KEY idx_users_created (created_at DESC),
  KEY idx_users_investment (investment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='회원';


CREATE TABLE IF NOT EXISTS user_sessions (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '회원ID',
  token         VARCHAR(512)    NOT NULL COMMENT '세션 토큰(JWT 등)',
  user_agent    VARCHAR(255)    DEFAULT NULL COMMENT '접속 UA',
  ip_address    VARCHAR(45)     DEFAULT NULL COMMENT '접속 IP',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  expires_at    TIMESTAMP       NULL COMMENT '만료일(UTC)',
  is_deleted    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  PRIMARY KEY (id),
  UNIQUE KEY uq_sessions_token (token),
  KEY idx_sessions_user (user_id),
  KEY idx_sessions_created (created_at DESC),
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='회원 세션';


CREATE TABLE IF NOT EXISTS posts (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '작성자',
  title         VARCHAR(200)    NOT NULL COMMENT '제목',
  content       MEDIUMTEXT      NOT NULL COMMENT '내용',
  view_count    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '조회수',
  like_count    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '좋아요 수',
  is_deleted    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_posts_user (user_id),
  KEY idx_posts_created (created_at DESC),
  KEY idx_posts_like_count (like_count DESC),
  CONSTRAINT fk_posts_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='커뮤니티 게시글';


CREATE TABLE IF NOT EXISTS post_comments (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  post_id       BIGINT UNSIGNED NOT NULL COMMENT '게시글ID',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '작성자',
  content       TEXT            NOT NULL COMMENT '내용',
  is_deleted    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  KEY idx_comments_post (post_id),
  KEY idx_comments_user (user_id),
  KEY idx_comments_created (created_at DESC),
  CONSTRAINT fk_comments_post FOREIGN KEY (post_id)
    REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='커뮤니티 댓글';


-- 게시글 좋아요
CREATE TABLE IF NOT EXISTS post_likes (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  post_id     BIGINT UNSIGNED NOT NULL COMMENT '게시글ID',
  user_id     BIGINT UNSIGNED NOT NULL COMMENT '사용자ID',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  UNIQUE KEY uq_post_likes (post_id, user_id),
  KEY idx_post_likes_user (user_id),
  CONSTRAINT fk_post_likes_post FOREIGN KEY (post_id)
    REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_post_likes_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='게시글 좋아요';


-- 신고
CREATE TABLE IF NOT EXISTS reports (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  reporter_id BIGINT UNSIGNED NOT NULL COMMENT '신고자',
  target_type ENUM('post', 'comment', 'user') NOT NULL COMMENT '신고 대상 타입',
  target_id   BIGINT UNSIGNED NOT NULL COMMENT '신고 대상 ID',
  reason      VARCHAR(200)    NOT NULL COMMENT '신고 사유',
  status      ENUM('pending', 'processed', 'rejected') NOT NULL DEFAULT 'pending' COMMENT '처리 상태',
  admin_memo  TEXT            DEFAULT NULL COMMENT '관리자 메모',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  processed_at TIMESTAMP      DEFAULT NULL COMMENT '처리일(UTC)',
  PRIMARY KEY (id),
  KEY idx_reports_reporter (reporter_id),
  KEY idx_reports_target (target_type, target_id),
  KEY idx_reports_status (status),
  CONSTRAINT fk_reports_reporter FOREIGN KEY (reporter_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='신고';


-- 공지사항
CREATE TABLE IF NOT EXISTS notices (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  admin_id    BIGINT UNSIGNED NOT NULL COMMENT '작성 관리자',
  title       VARCHAR(200)    NOT NULL COMMENT '제목',
  content     MEDIUMTEXT      NOT NULL COMMENT '내용',
  is_pinned   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '상단 고정',
  is_deleted  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_notices_admin (admin_id),
  KEY idx_notices_created (created_at DESC),
  KEY idx_notices_pinned (is_pinned DESC, created_at DESC),
  CONSTRAINT fk_notices_admin FOREIGN KEY (admin_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='공지사항';


-- 백테스트 히스토리
CREATE TABLE IF NOT EXISTS backtest_history (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id         BIGINT UNSIGNED NOT NULL COMMENT '사용자ID',
  ticker          VARCHAR(20)     NOT NULL COMMENT '종목 심볼',
  strategy_name   VARCHAR(100)    NOT NULL COMMENT '전략명',
  start_date      DATE            NOT NULL COMMENT '시작일',
  end_date        DATE            NOT NULL COMMENT '종료일',
  initial_cash    DECIMAL(19, 4)  NOT NULL COMMENT '초기 투자금',
  final_value     DECIMAL(19, 4)  DEFAULT NULL COMMENT '최종 평가금액',
  total_return    DECIMAL(10, 4)  DEFAULT NULL COMMENT '총 수익률(%)',
  sharpe_ratio    DECIMAL(10, 4)  DEFAULT NULL COMMENT '샤프 지수',
  max_drawdown    DECIMAL(10, 4)  DEFAULT NULL COMMENT '최대 낙폭(%)',
  strategy_params JSON            DEFAULT NULL COMMENT '전략 파라미터',
  result_data     JSON            DEFAULT NULL COMMENT '백테스트 결과 데이터',
  is_deleted      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  KEY idx_backtest_user (user_id),
  KEY idx_backtest_ticker (ticker),
  KEY idx_backtest_created (created_at DESC),
  KEY idx_backtest_return (total_return DESC),
  CONSTRAINT fk_backtest_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='백테스트 히스토리';

SET FOREIGN_KEY_CHECKS=1;

