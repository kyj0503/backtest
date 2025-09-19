-- =================================================================
-- Spring Boot 커뮤니티 플랫폼 데이터베이스 스키마
-- 대상 DBMS: MySQL 8.0+
-- 버전: 4.0 - Spring Boot 단독 아키텍처 (커뮤니티/채팅/회원/관리자)
-- 기능: 게시판, 채팅, 회원관리, 소셜로그인, 관리자, 로깅/감사
-- =================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET FOREIGN_KEY_CHECKS=0;
-- Removed NO_AUTO_CREATE_USER as it is unsupported in MySQL 8+
SET sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Ensure target database exists before creating tables
CREATE DATABASE IF NOT EXISTS stock_community
  CHARACTER SET = 'utf8mb4'
  COLLATE = 'utf8mb4_0900_ai_ci';

USE stock_community;

-- =================================================================
-- 1. 회원 관리 (SpringBoot가 담당할 테이블들)
-- =================================================================

-- 회원 기본 정보
CREATE TABLE IF NOT EXISTS users (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  username        VARCHAR(50)     NOT NULL COMMENT '닉네임 (고유)',
  email           VARCHAR(255)    NOT NULL COMMENT '이메일 (고유)',
  password_hash   VARBINARY(255)  NOT NULL COMMENT '비밀번호 해시',
  password_salt   VARBINARY(128)  NOT NULL COMMENT '비밀번호 솔트',
  password_algo   VARCHAR(50)     NOT NULL DEFAULT 'bcrypt' COMMENT '해시 알고리즘',
  profile_image   VARCHAR(500)    DEFAULT NULL COMMENT '프로필 이미지 URL',
  investment_type VARCHAR(20) NOT NULL DEFAULT 'balanced' COMMENT '투자 성향',
  is_admin        TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '관리자 여부',
  is_active       TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '계정 활성화 상태',
  is_email_verified TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '이메일 인증 여부',
  last_login_at   TIMESTAMP       NULL COMMENT '최종 로그인 시각',
  is_deleted      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_username (username),
  KEY idx_users_created (created_at DESC),
  KEY idx_users_investment (investment_type),
  KEY idx_users_last_login (last_login_at DESC),
  CONSTRAINT chk_users_investment_type CHECK (investment_type IN ('conservative', 'moderate', 'balanced', 'aggressive', 'speculative'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='회원 기본 정보';

-- 회원 세션 (Access Token + Refresh Token 지원)
CREATE TABLE IF NOT EXISTS user_sessions (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '회원ID',
  access_token  VARCHAR(1024)   NOT NULL COMMENT 'JWT Access Token',
  refresh_token VARCHAR(512)    NOT NULL COMMENT 'JWT Refresh Token',
  token_type    VARCHAR(20)     NOT NULL DEFAULT 'Bearer' COMMENT '토큰 타입',
  user_agent    VARCHAR(500)    DEFAULT NULL COMMENT '접속 User Agent',
  ip_address    VARCHAR(45)     DEFAULT NULL COMMENT '접속 IP (IPv6 지원)',
  device_info   JSON            DEFAULT NULL COMMENT '기기 정보 (JSON)',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  access_expires_at TIMESTAMP   NOT NULL COMMENT 'Access Token 만료일(UTC)',
  refresh_expires_at TIMESTAMP  NOT NULL COMMENT 'Refresh Token 만료일(UTC)',
  last_used_at  TIMESTAMP       NULL COMMENT '마지막 사용 시각',
  is_revoked    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '토큰 폐기 여부',
  revoked_at    TIMESTAMP       NULL COMMENT '폐기 시각',
  PRIMARY KEY (id),
  UNIQUE KEY uq_sessions_access_token (access_token(255)),
  UNIQUE KEY uq_sessions_refresh_token (refresh_token),
  KEY idx_sessions_user (user_id),
  KEY idx_sessions_created (created_at DESC),
  KEY idx_sessions_access_expires (access_expires_at),
  KEY idx_sessions_refresh_expires (refresh_expires_at),
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='회원 세션 (JWT 토큰 관리)';

-- 소셜 로그인 연동
CREATE TABLE IF NOT EXISTS user_social_accounts (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '회원ID',
  provider      ENUM('google', 'kakao', 'naver', 'github') NOT NULL COMMENT '소셜 로그인 제공자',
  provider_id   VARCHAR(100)    NOT NULL COMMENT '소셜 로그인 고유ID',
  provider_email VARCHAR(255)   DEFAULT NULL COMMENT '소셜 계정 이메일',
  provider_data JSON            DEFAULT NULL COMMENT '소셜 계정 추가 정보',
  is_active     TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '연동 활성화 상태',
  linked_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '연동 일시',
  last_used_at  TIMESTAMP       NULL COMMENT '마지막 사용 일시',
  PRIMARY KEY (id),
  UNIQUE KEY uq_social_provider (provider, provider_id),
  KEY idx_social_user (user_id),
  KEY idx_social_provider (provider),
  CONSTRAINT fk_social_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='소셜 로그인 계정 연동';

-- =================================================================
-- 2. 커뮤니티 & 게시판 (SpringBoot가 담당할 테이블들)
-- =================================================================

-- 게시글
CREATE TABLE IF NOT EXISTS posts (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '작성자',
  category      ENUM('general', 'strategy', 'question', 'news', 'backtest_share') DEFAULT 'general' COMMENT '게시글 카테고리',
  title         VARCHAR(200)    NOT NULL COMMENT '제목',
  content       MEDIUMTEXT      NOT NULL COMMENT '내용 (Markdown 지원)',
  content_type  ENUM('text', 'markdown') DEFAULT 'markdown' COMMENT '내용 형식',
  view_count    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '조회수',
  like_count    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '좋아요 수',
  comment_count INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '댓글 수',
  is_pinned     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '상단 고정',
  is_featured   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '추천 게시글',
  is_deleted    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  deleted_at    TIMESTAMP       NULL COMMENT '삭제 일시',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_posts_user (user_id),
  KEY idx_posts_category (category),
  KEY idx_posts_created (created_at DESC),
  KEY idx_posts_like_count (like_count DESC),
  KEY idx_posts_view_count (view_count DESC),
  KEY idx_posts_pinned (is_pinned DESC, created_at DESC),
  KEY idx_posts_featured (is_featured DESC, created_at DESC),
  CONSTRAINT fk_posts_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='커뮤니티 게시글';

-- 게시글 댓글 (대댓글 지원)
CREATE TABLE IF NOT EXISTS post_comments (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  post_id       BIGINT UNSIGNED NOT NULL COMMENT '게시글ID',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '작성자',
  parent_id     BIGINT UNSIGNED NULL COMMENT '부모 댓글ID (대댓글인 경우)',
  content       TEXT            NOT NULL COMMENT '댓글 내용',
  like_count    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '좋아요 수',
  is_deleted    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  deleted_at    TIMESTAMP       NULL COMMENT '삭제 일시',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_comments_post (post_id),
  KEY idx_comments_user (user_id),
  KEY idx_comments_parent (parent_id),
  KEY idx_comments_created (created_at DESC),
  CONSTRAINT fk_comments_post FOREIGN KEY (post_id)
    REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_comments_parent FOREIGN KEY (parent_id)
    REFERENCES post_comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='게시글 댓글';

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

-- 댓글 좋아요
CREATE TABLE IF NOT EXISTS comment_likes (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  comment_id  BIGINT UNSIGNED NOT NULL COMMENT '댓글ID',
  user_id     BIGINT UNSIGNED NOT NULL COMMENT '사용자ID',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  UNIQUE KEY uq_comment_likes (comment_id, user_id),
  KEY idx_comment_likes_user (user_id),
  CONSTRAINT fk_comment_likes_comment FOREIGN KEY (comment_id)
    REFERENCES post_comments(id) ON DELETE CASCADE,
  CONSTRAINT fk_comment_likes_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='댓글 좋아요';

-- =================================================================
-- 3. 실시간 채팅 (SpringBoot WebSocket이 담당할 테이블들)
-- =================================================================

-- 채팅방
CREATE TABLE IF NOT EXISTS chat_rooms (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  name          VARCHAR(100)    NOT NULL COMMENT '채팅방 이름',
  description   TEXT            DEFAULT NULL COMMENT '채팅방 설명',
  room_type     ENUM('public', 'private', 'direct') DEFAULT 'public' COMMENT '채팅방 타입',
  max_members   INT UNSIGNED    DEFAULT 100 COMMENT '최대 멤버 수',
  current_members INT UNSIGNED  DEFAULT 0 COMMENT '현재 멤버 수',
  created_by    BIGINT UNSIGNED NOT NULL COMMENT '생성자',
  is_active     TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '활성화 상태',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_rooms_type (room_type),
  KEY idx_rooms_created_by (created_by),
  KEY idx_rooms_created (created_at DESC),
  CONSTRAINT fk_rooms_creator FOREIGN KEY (created_by)
    REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅방';

-- 채팅방 멤버
CREATE TABLE IF NOT EXISTS chat_room_members (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  room_id     BIGINT UNSIGNED NOT NULL COMMENT '채팅방ID',
  user_id     BIGINT UNSIGNED NOT NULL COMMENT '사용자ID',
  role        ENUM('member', 'moderator', 'admin') DEFAULT 'member' COMMENT '멤버 역할',
  joined_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '입장 일시',
  last_read_at TIMESTAMP      NULL COMMENT '마지막 읽음 일시',
  is_active   TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '활성 상태',
  PRIMARY KEY (id),
  UNIQUE KEY uq_room_member (room_id, user_id),
  KEY idx_members_user (user_id),
  KEY idx_members_role (role),
  CONSTRAINT fk_members_room FOREIGN KEY (room_id)
    REFERENCES chat_rooms(id) ON DELETE CASCADE,
  CONSTRAINT fk_members_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅방 멤버';

-- 채팅 메시지
CREATE TABLE IF NOT EXISTS chat_messages (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  room_id     BIGINT UNSIGNED NOT NULL COMMENT '채팅방ID',
  user_id     BIGINT UNSIGNED NOT NULL COMMENT '발신자ID',
  message_type ENUM('text', 'image', 'file', 'system') DEFAULT 'text' COMMENT '메시지 타입',
  content     TEXT            NOT NULL COMMENT '메시지 내용',
  file_url    VARCHAR(500)    DEFAULT NULL COMMENT '첨부파일 URL',
  file_name   VARCHAR(255)    DEFAULT NULL COMMENT '첨부파일명',
  file_size   INT UNSIGNED    DEFAULT NULL COMMENT '파일 크기(bytes)',
  reply_to_id BIGINT UNSIGNED NULL COMMENT '답장 대상 메시지ID',
  is_deleted  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '논리삭제',
  deleted_at  TIMESTAMP       NULL COMMENT '삭제 일시',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_messages_room_created (room_id, created_at DESC),
  KEY idx_messages_user (user_id),
  KEY idx_messages_reply (reply_to_id),
  KEY idx_messages_type (message_type),
  CONSTRAINT fk_messages_room FOREIGN KEY (room_id)
    REFERENCES chat_rooms(id) ON DELETE CASCADE,
  CONSTRAINT fk_messages_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_messages_reply FOREIGN KEY (reply_to_id)
    REFERENCES chat_messages(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅 메시지';

-- =================================================================
-- 4. 신고 & 시스템 관리
-- =================================================================

-- 신고 관리
CREATE TABLE IF NOT EXISTS reports (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  reporter_id   BIGINT UNSIGNED NOT NULL COMMENT '신고자ID',
  target_type   ENUM('user', 'post', 'comment', 'chat_message') NOT NULL COMMENT '신고 대상 타입',
  target_id     BIGINT UNSIGNED NOT NULL COMMENT '신고 대상 ID',
  report_reason ENUM('spam', 'abuse', 'inappropriate', 'copyright', 'other') NOT NULL COMMENT '신고 사유',
  description   TEXT            DEFAULT NULL COMMENT '상세 설명',
  status        ENUM('pending', 'processing', 'resolved', 'dismissed') NOT NULL DEFAULT 'pending' COMMENT '처리 상태',
  processor_id  BIGINT UNSIGNED DEFAULT NULL COMMENT '처리자 ID',
  resolution    TEXT            DEFAULT NULL COMMENT '처리 결과',
  processed_at  TIMESTAMP       DEFAULT NULL COMMENT '처리 일시',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  KEY idx_report_reporter (reporter_id),
  KEY idx_report_target (target_type, target_id),
  KEY idx_report_status (status),
  KEY idx_report_created (created_at DESC),
  KEY idx_report_processor (processor_id),
  CONSTRAINT fk_report_reporter FOREIGN KEY (reporter_id)
    REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_report_processor FOREIGN KEY (processor_id)
    REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='신고 관리';

-- 시스템 공지사항
CREATE TABLE IF NOT EXISTS system_notices (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  title         VARCHAR(200)    NOT NULL COMMENT '공지 제목',
  content       LONGTEXT        NOT NULL COMMENT '공지 내용',
  notice_type   ENUM('general', 'maintenance', 'update', 'emergency', 'event') NOT NULL DEFAULT 'general' COMMENT '공지 타입',
  priority      ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '우선순위',
  is_popup      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '팝업 표시 여부',
  is_pinned     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '상단 고정 여부',
  start_date    TIMESTAMP       DEFAULT NULL COMMENT '게시 시작일',
  end_date      TIMESTAMP       DEFAULT NULL COMMENT '게시 종료일',
  target_users  JSON            DEFAULT NULL COMMENT '대상 사용자 조건 (JSON)',
  read_count    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '읽음 수',
  author_id     BIGINT UNSIGNED NOT NULL COMMENT '작성자ID',
  is_active     TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '활성화 상태',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  KEY idx_notice_type (notice_type),
  KEY idx_notice_priority (priority),
  KEY idx_notice_active (is_active, start_date, end_date),
  KEY idx_notice_pinned (is_pinned, created_at DESC),
  KEY idx_notice_author (author_id),
  CONSTRAINT fk_notice_author FOREIGN KEY (author_id)
    REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시스템 공지사항';

-- 공지사항 읽음 상태
CREATE TABLE IF NOT EXISTS notice_read_status (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  notice_id     BIGINT UNSIGNED NOT NULL COMMENT '공지ID',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '사용자ID',
  read_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '읽은 일시',
  PRIMARY KEY (id),
  UNIQUE KEY uq_notice_read (notice_id, user_id),
  KEY idx_notice_read_user (user_id),
  CONSTRAINT fk_notice_read_notice FOREIGN KEY (notice_id)
    REFERENCES system_notices(id) ON DELETE CASCADE,
  CONSTRAINT fk_notice_read_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='공지사항 읽음 상태';

-- 시스템 설정
CREATE TABLE IF NOT EXISTS system_settings (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  setting_key   VARCHAR(100)    NOT NULL COMMENT '설정 키',
  setting_value LONGTEXT        NOT NULL COMMENT '설정 값',
  setting_type  ENUM('string', 'number', 'boolean', 'json') NOT NULL DEFAULT 'string' COMMENT '값 타입',
  category      VARCHAR(50)     NOT NULL DEFAULT 'general' COMMENT '설정 카테고리',
  description   VARCHAR(500)    DEFAULT NULL COMMENT '설정 설명',
  is_public     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '공개 여부',
  last_updated_by BIGINT UNSIGNED DEFAULT NULL COMMENT '최종 수정자',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일(UTC)',
  PRIMARY KEY (id),
  UNIQUE KEY uq_setting_key (setting_key),
  KEY idx_setting_category (category),
  KEY idx_setting_public (is_public),
  CONSTRAINT fk_setting_updater FOREIGN KEY (last_updated_by)
    REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시스템 설정';

-- =================================================================
-- 5. 로깅 & 감사 시스템 (Spring Boot 관리)
-- =================================================================

-- 사용자 활동 로그
CREATE TABLE IF NOT EXISTS user_activity_logs (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  user_id       BIGINT UNSIGNED NULL COMMENT '사용자ID (비로그인 시 NULL)',
  session_id    VARCHAR(100)    DEFAULT NULL COMMENT '세션ID',
  activity_type ENUM('login', 'logout', 'post_create', 'post_update', 'post_delete', 'comment_create', 'comment_update', 'comment_delete', 'chat_join', 'chat_leave', 'chat_message', 'profile_update', 'password_change', 'admin_action') NOT NULL COMMENT '활동 타입',
  target_type   ENUM('user', 'post', 'comment', 'chat_room', 'chat_message', 'system') DEFAULT NULL COMMENT '대상 객체 타입',
  target_id     BIGINT UNSIGNED DEFAULT NULL COMMENT '대상 객체 ID',
  ip_address    VARCHAR(45)     NOT NULL COMMENT '접속 IP',
  user_agent    VARCHAR(500)    DEFAULT NULL COMMENT 'User Agent',
  details       JSON            DEFAULT NULL COMMENT '상세 정보 (JSON)',
  result        ENUM('success', 'failure', 'error') DEFAULT 'success' COMMENT '실행 결과',
  error_message TEXT            DEFAULT NULL COMMENT '오류 메시지',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  KEY idx_activity_user (user_id),
  KEY idx_activity_type (activity_type),
  KEY idx_activity_target (target_type, target_id),
  KEY idx_activity_created (created_at DESC),
  KEY idx_activity_ip (ip_address),
  KEY idx_activity_session (session_id),
  CONSTRAINT fk_activity_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='사용자 활동 로그'
PARTITION BY RANGE (YEAR(created_at)) (
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p2025 VALUES LESS THAN (2026),
  PARTITION p2026 VALUES LESS THAN (2027),
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 관리자 작업 로그
CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  admin_id      BIGINT UNSIGNED NOT NULL COMMENT '관리자ID',
  action_type   ENUM('user_suspend', 'user_ban', 'user_unban', 'post_delete', 'post_restore', 'comment_delete', 'comment_restore', 'report_process', 'notice_create', 'notice_update', 'notice_delete', 'system_setting_update', 'chat_room_create', 'chat_room_delete') NOT NULL COMMENT '작업 타입',
  target_type   ENUM('user', 'post', 'comment', 'report', 'notice', 'system_setting', 'chat_room') NOT NULL COMMENT '대상 타입',
  target_id     BIGINT UNSIGNED NOT NULL COMMENT '대상 ID',
  before_value  JSON            DEFAULT NULL COMMENT '변경 전 값',
  after_value   JSON            DEFAULT NULL COMMENT '변경 후 값',
  reason        TEXT            DEFAULT NULL COMMENT '작업 사유',
  ip_address    VARCHAR(45)     NOT NULL COMMENT '관리자 IP',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  KEY idx_audit_admin (admin_id),
  KEY idx_audit_action (action_type),
  KEY idx_audit_target (target_type, target_id),
  KEY idx_audit_created (created_at DESC),
  CONSTRAINT fk_audit_admin FOREIGN KEY (admin_id)
    REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='관리자 작업 감사 로그';

-- 시스템 성능 로그
CREATE TABLE IF NOT EXISTS system_performance_logs (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  metric_type   ENUM('api_response_time', 'db_query_time', 'memory_usage', 'cpu_usage', 'active_sessions', 'concurrent_users') NOT NULL COMMENT '지표 타입',
  metric_value  DECIMAL(15, 6)  NOT NULL COMMENT '지표 값',
  unit          VARCHAR(20)     DEFAULT NULL COMMENT '단위 (ms, %, MB 등)',
  endpoint      VARCHAR(200)    DEFAULT NULL COMMENT 'API 엔드포인트',
  additional_data JSON          DEFAULT NULL COMMENT '추가 데이터',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일(UTC)',
  PRIMARY KEY (id),
  KEY idx_perf_type (metric_type),
  KEY idx_perf_created (created_at DESC),
  KEY idx_perf_endpoint (endpoint),
  KEY idx_perf_composite (metric_type, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시스템 성능 로그'
PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
  PARTITION p202501 VALUES LESS THAN (UNIX_TIMESTAMP('2025-02-01')),
  PARTITION p202502 VALUES LESS THAN (UNIX_TIMESTAMP('2025-03-01')),
  PARTITION p202503 VALUES LESS THAN (UNIX_TIMESTAMP('2025-04-01')),
  PARTITION p202504 VALUES LESS THAN (UNIX_TIMESTAMP('2025-05-01')),
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =================================================================
-- 6. 데이터베이스 성능 최적화 설정
-- =================================================================

-- 데이터베이스 튜닝 파라미터 (시스템 시작 시 실행)
SET GLOBAL innodb_buffer_pool_size = 256 * 1024 * 1024; -- 256MB (개발환경)
SET GLOBAL innodb_log_file_size = 64 * 1024 * 1024; -- 64MB
SET GLOBAL innodb_log_buffer_size = 16 * 1024 * 1024; -- 16MB
SET GLOBAL query_cache_size = 64 * 1024 * 1024; -- 64MB
SET GLOBAL max_connections = 200;
SET GLOBAL thread_cache_size = 16;
SET GLOBAL table_open_cache = 400;
SET GLOBAL innodb_flush_log_at_trx_commit = 2; -- 개발환경: 성능 우선

-- =================================================================
-- 7. 추가 인덱스 최적화 (커뮤니티 특화)
-- =================================================================

-- 사용자 관련 복합 인덱스
ALTER TABLE users ADD INDEX idx_user_status_level (user_status, user_level);
ALTER TABLE users ADD INDEX idx_user_activity (last_login_at DESC, is_deleted);

-- 게시판 검색 최적화
ALTER TABLE posts ADD FULLTEXT INDEX ft_post_search (title, content);
ALTER TABLE comments ADD FULLTEXT INDEX ft_comment_content (content);

-- 채팅 성능 최적화
ALTER TABLE chat_messages ADD INDEX idx_chat_room_time_type (room_id, created_at DESC, message_type);
ALTER TABLE chat_room_members ADD INDEX idx_member_activity (user_id, is_active, last_read_at DESC);

-- 활동 로그 성능 최적화  
ALTER TABLE user_activity_logs ADD INDEX idx_activity_user_type_time (user_id, activity_type, created_at DESC);

-- 관리자 계정 생성 (비밀번호: admin123!)
INSERT IGNORE INTO users (id, username, email, password_hash, display_name, user_role, user_status, is_email_verified, created_at) VALUES
(1, 'admin', 'admin@community.local', '$2a$12$LQv3c1yqBwLVMc5rBXnDIe.5uOZjOTiNtY6XvToWY1y4Z5nOJ5N6K', '시스템 관리자', 'admin', 'active', 1, NOW());

-- =================================================================
-- 8. 초기 데이터 삽입
-- =================================================================

-- 시스템 설정 기본값 (Spring Boot 커뮤니티 플랫폼 전용)
INSERT IGNORE INTO system_settings (setting_key, setting_value, setting_type, category, description) VALUES
('site_title', '커뮤니티 플랫폼', 'string', 'general', '사이트 제목'),
('site_description', 'Spring Boot 기반 커뮤니티 플랫폼', 'string', 'general', '사이트 설명'),
('max_file_upload_size', '10485760', 'number', 'general', '최대 파일 업로드 크기 (10MB)'),
('enable_registration', 'true', 'boolean', 'auth', '회원가입 활성화'),
('enable_social_login', 'false', 'boolean', 'auth', '소셜 로그인 활성화'),
('enable_chat', 'true', 'boolean', 'feature', '채팅 기능 활성화'),
('enable_file_upload', 'true', 'boolean', 'feature', '파일 업로드 활성화'),
('maintenance_mode', 'false', 'boolean', 'system', '점검 모드'),
('posts_per_page', '20', 'number', 'display', '페이지당 게시물 수'),
('comments_per_page', '50', 'number', 'display', '페이지당 댓글 수'),
('max_comment_depth', '3', 'number', 'community', '최대 댓글 대댓글 깊이'),
('user_level_threshold', '{"bronze": 100, "silver": 500, "gold": 1000, "platinum": 5000}', 'json', 'gamification', '사용자 레벨 기준점'),
('chat_message_limit_per_minute', '10', 'number', 'chat', '분당 채팅 메시지 제한'),
('auto_ban_spam_threshold', '5', 'number', 'moderation', '자동 차단 스팸 임계값');

-- 게시판 카테고리 생성
INSERT IGNORE INTO categories (id, name, description, display_order, is_active) VALUES
(1, '공지사항', '사이트 공지사항 및 업데이트 소식', 1, 1),
(2, '자유게시판', '자유로운 주제로 대화를 나누는 공간', 2, 1),
(3, '질문답변', '궁금한 것들을 질문하고 답변하는 공간', 3, 1),
(4, '개발이야기', '개발 관련 이야기를 나누는 공간', 4, 1),
(5, '취미생활', '취미와 관련된 이야기를 나누는 공간', 5, 1);

-- 기본 채팅방 생성
INSERT IGNORE INTO chat_rooms (id, name, description, room_type, created_by) VALUES
(1, '환영합니다!', '새로 오신 분들을 위한 인사 공간입니다', 'public', 1),
(2, '자유 채팅', '자유로운 주제로 대화를 나누는 공간입니다', 'public', 1),
(3, '개발 토론', '개발 관련 토론을 나누는 공간입니다', 'public', 1),
(4, '도움 요청', '도움이 필요할 때 사용하는 공간입니다', 'public', 1);

-- 관리자를 모든 채팅방에 자동 추가
INSERT IGNORE INTO chat_room_members (room_id, user_id, role, joined_at) VALUES
(1, 1, 'admin', NOW()),
(2, 1, 'admin', NOW()),
(3, 1, 'admin', NOW()),
(4, 1, 'admin', NOW());

SET FOREIGN_KEY_CHECKS=1;

-- =================================================================
-- 9. 스키마 검증 및 완료
-- =================================================================

-- 스크립트 완료 메시지
SELECT 'Spring Boot 커뮤니티 플랫폼 데이터베이스 스키마 생성이 완료되었습니다.' AS message;
SELECT 'FastAPI 백테스팅 관련 의존성이 제거되었습니다.' AS cleanup_message;

-- 생성된 테이블 목록 확인
SELECT 
    TABLE_NAME as '생성된_테이블',
    TABLE_COMMENT as '설명',
    TABLE_ROWS as '예상_행수'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- 주요 인덱스 확인
SELECT 
    TABLE_NAME as '테이블명',
    INDEX_NAME as '인덱스명',
    COLUMN_NAME as '컬럼명',
    INDEX_TYPE as '타입'
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE()
  AND INDEX_NAME != 'PRIMARY'
ORDER BY TABLE_NAME, INDEX_NAME;

-- 외래키 제약조건 확인
SELECT 
    TABLE_NAME as '테이블명',
    COLUMN_NAME as '컬럼명', 
    CONSTRAINT_NAME as '제약조건명',
    REFERENCED_TABLE_NAME as '참조_테이블',
    REFERENCED_COLUMN_NAME as '참조_컬럼'
FROM information_schema.KEY_COLUMN_USAGE 
WHERE TABLE_SCHEMA = DATABASE()
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME;
