package com.webproject.backtest_be_spring.domain.community;

public enum PostContentType {
    TEXT,
    MARKDOWN;

    public static PostContentType from(String value) {
        if (value == null || value.isBlank()) {
            return MARKDOWN;
        }
        return PostContentType.valueOf(value.trim().toUpperCase());
    }
}
