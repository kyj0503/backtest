package com.webproject.backtest_be_spring.domain.chat.model;

public enum ChatRoomType {
    PUBLIC,
    PRIVATE,
    DIRECT;

    public static ChatRoomType from(String value) {
        if (value == null || value.isBlank()) {
            return PUBLIC;
        }
        return ChatRoomType.valueOf(value.trim().toUpperCase());
    }
}
