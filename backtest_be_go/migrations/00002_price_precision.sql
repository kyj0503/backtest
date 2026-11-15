-- 가격 정밀도: DECIMAL(19,4) → DECIMAL(38,18) (rust-migration F14, Alembic 6f903c2a711b와 같은 변경).
-- 소수점 넷째 자리 아래 수정 주가(분할·배당 조정)와 저가 자산이 반올림되지 않게 한다.
--
-- 되돌리기(Down)는 없다. 정밀도를 줄이면 유효한 가격이 되돌릴 수 없게 반올림된다.
-- 되돌려야 하면 적용 전 백업을 복원한다.
-- +goose NO TRANSACTION
-- +goose Up
ALTER TABLE daily_prices
    MODIFY open DECIMAL(38, 18) NOT NULL COMMENT '시가',
    MODIFY high DECIMAL(38, 18) NOT NULL COMMENT '고가',
    MODIFY low DECIMAL(38, 18) NOT NULL COMMENT '저가',
    MODIFY close DECIMAL(38, 18) NOT NULL COMMENT '종가',
    MODIFY adj_close DECIMAL(38, 18) COMMENT '수정 종가';
