package com.webproject.backtest_be_spring.domain.chat.model;

public enum ChatMessageType {
    TEXT,
    IMAGE,
    FILE,
    SYSTEM;

    public static ChatMessageType from(String value) {
        if (value == null || value.isBlank()) {
            return TEXT;
        }
        return ChatMessageType.valueOf(value.trim().toUpperCase());
    }
}
