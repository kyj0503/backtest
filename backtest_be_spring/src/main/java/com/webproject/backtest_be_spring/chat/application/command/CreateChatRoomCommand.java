package com.webproject.backtest_be_spring.chat.application.command;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;

public record CreateChatRoomCommand(
        String name,
        String description,
        ChatRoomType roomType,
        Integer maxMembers) {
}
