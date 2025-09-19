package com.webproject.backtest_be_spring.domain.admin.model;

public enum ReportTargetType {
    USER,
    POST,
    COMMENT,
    CHAT_MESSAGE;

    public static ReportTargetType from(String value) {
        return ReportTargetType.valueOf(value.trim().toUpperCase());
    }
}
