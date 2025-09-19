package com.webproject.backtest_be_spring.application.chat.command;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomType;

public record CreateChatRoomCommand(
        String name,
        String description,
        ChatRoomType roomType,
        Integer maxMembers) {
}
