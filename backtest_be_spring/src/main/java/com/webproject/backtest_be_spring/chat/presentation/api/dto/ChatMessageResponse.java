package com.webproject.backtest_be_spring.chat.presentation.api.dto;

import com.webproject.backtest_be_spring.chat.application.dto.ChatMessageDto;
import java.time.Instant;

public record ChatMessageResponse(
        Long id,
        Long roomId,
        Long senderId,
        String senderName,
        String messageType,
        String content,
        String fileUrl,
        String fileName,
        Integer fileSize,
        Long replyToId,
        boolean deleted,
        Instant createdAt,
        Instant updatedAt) {

    public static ChatMessageResponse from(ChatMessageDto dto) {
        return new ChatMessageResponse(
                dto.id(),
                dto.roomId(),
                dto.senderId(),
                dto.senderName(),
                dto.messageType().name().toLowerCase(),
                dto.content(),
                dto.fileUrl(),
                dto.fileName(),
                dto.fileSize(),
                dto.replyToId(),
                dto.deleted(),
                dto.createdAt(),
                dto.updatedAt());
    }
}
