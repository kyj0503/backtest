package com.webproject.backtest_be_spring.application.chat.dto;

import com.webproject.backtest_be_spring.domain.chat.model.ChatMessage;
import com.webproject.backtest_be_spring.domain.chat.model.ChatMessageType;
import java.time.Instant;

public record ChatMessageDto(
        Long id,
        Long roomId,
        Long senderId,
        String senderName,
        ChatMessageType messageType,
        String content,
        String fileUrl,
        String fileName,
        Integer fileSize,
        Long replyToId,
        boolean deleted,
        Instant createdAt,
        Instant updatedAt) {

    public static ChatMessageDto from(ChatMessage message) {
        return new ChatMessageDto(
                message.getId(),
                message.getRoom().getId(),
                message.getSender().getId(),
                message.getSender().getUsername(),
                message.getMessageType(),
                message.getContent(),
                message.getFileUrl(),
                message.getFileName(),
                message.getFileSize(),
                message.getReplyTo() != null ? message.getReplyTo().getId() : null,
                message.isDeleted(),
                message.getCreatedAt(),
                message.getUpdatedAt());
    }
}
