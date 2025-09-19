package com.webproject.backtest_be_spring.application.chat.command;

import com.webproject.backtest_be_spring.domain.chat.ChatRoomType;

public record UpdateChatRoomCommand(
        String name,
        String description,
        ChatRoomType roomType,
        Integer maxMembers,
        Boolean active) {
}
