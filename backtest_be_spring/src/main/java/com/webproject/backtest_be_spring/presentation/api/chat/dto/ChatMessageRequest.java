package com.webproject.backtest_be_spring.presentation.api.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatMessageRequest(
        String messageType,
        @NotBlank @Size(max = 2000) String content,
        String fileUrl,
        String fileName,
        Integer fileSize,
        Long replyToId) {
}
