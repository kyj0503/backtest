package com.webproject.backtest_be_spring.community.application.exception;

public class CommunityAccessDeniedException extends RuntimeException {

    public CommunityAccessDeniedException() {
        super("해당 작업을 수행할 권한이 없습니다.");
    }
}
