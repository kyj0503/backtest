package com.webproject.backtest_be_spring.application.chat.command;

import com.webproject.backtest_be_spring.domain.chat.ChatMessageType;

public record SendChatMessageCommand(
        ChatMessageType messageType,
        String content,
        String fileUrl,
        String fileName,
        Integer fileSize,
        Long replyToId) {
}
