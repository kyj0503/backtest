package com.webproject.backtest_be_spring.chat.application.command;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;

public record UpdateChatRoomCommand(
        String name,
        String description,
        ChatRoomType roomType,
        Integer maxMembers,
        Boolean active) {
}
