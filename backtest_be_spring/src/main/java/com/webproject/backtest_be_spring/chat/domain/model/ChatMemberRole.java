package com.webproject.backtest_be_spring.chat.domain.model;

public enum ChatMemberRole {
    MEMBER,
    MODERATOR,
    ADMIN;

    public static ChatMemberRole from(String value) {
        if (value == null || value.isBlank()) {
            return MEMBER;
        }
        return ChatMemberRole.valueOf(value.trim().toUpperCase());
    }
}
