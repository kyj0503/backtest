package com.webproject.backtest_be_spring.admin.domain.model;

public enum ReportTargetType {
    USER,
    POST,
    COMMENT,
    CHAT_MESSAGE;

    public static ReportTargetType from(String value) {
        return ReportTargetType.valueOf(value.trim().toUpperCase());
    }
}
