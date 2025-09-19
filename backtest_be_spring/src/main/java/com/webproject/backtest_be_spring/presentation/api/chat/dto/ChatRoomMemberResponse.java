package com.webproject.backtest_be_spring.presentation.api.chat.dto;

import com.webproject.backtest_be_spring.application.chat.dto.ChatRoomMemberDto;
import java.time.Instant;

public record ChatRoomMemberResponse(
        Long id,
        Long userId,
        String username,
        String role,
        boolean active,
        Instant joinedAt,
        Instant lastReadAt) {

    public static ChatRoomMemberResponse from(ChatRoomMemberDto dto) {
        return new ChatRoomMemberResponse(
                dto.id(),
                dto.userId(),
                dto.username(),
                dto.role().name().toLowerCase(),
                dto.active(),
                dto.joinedAt(),
                dto.lastReadAt());
    }
}
