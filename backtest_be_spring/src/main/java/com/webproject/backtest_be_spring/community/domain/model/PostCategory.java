package com.webproject.backtest_be_spring.community.domain.model;

public enum PostCategory {
    GENERAL,
    STRATEGY,
    QUESTION,
    NEWS,
    BACKTEST_SHARE;

    public static PostCategory from(String value) {
        if (value == null || value.isBlank()) {
            return GENERAL;
        }
        return PostCategory.valueOf(value.trim().toUpperCase());
    }
}
