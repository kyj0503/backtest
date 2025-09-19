package com.webproject.backtest_be_spring.chat.application.command;

import com.webproject.backtest_be_spring.chat.domain.model.ChatMessageType;

public record SendChatMessageCommand(
        ChatMessageType messageType,
        String content,
        String fileUrl,
        String fileName,
        Integer fileSize,
        Long replyToId) {
}
