package com.webproject.backtest_be_spring.admin.application.exception;

public class AdminAccessDeniedException extends RuntimeException {

    public AdminAccessDeniedException() {
        super("관리자 권한이 필요합니다.");
    }
}
