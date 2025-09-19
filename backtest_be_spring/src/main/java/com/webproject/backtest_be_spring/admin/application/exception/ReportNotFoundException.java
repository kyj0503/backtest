package com.webproject.backtest_be_spring.admin.application.exception;

public class ReportNotFoundException extends RuntimeException {

    public ReportNotFoundException(Long id) {
        super("신고 내역을 찾을 수 없습니다. id=" + id);
    }
}
