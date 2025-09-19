package com.webproject.backtest_be_spring.chat.presentation.api.dto;

import com.webproject.backtest_be_spring.chat.application.dto.ChatRoomDto;
import java.time.Instant;

public record ChatRoomResponse(
        Long id,
        String name,
        String description,
        String roomType,
        Integer maxMembers,
        Integer currentMembers,
        boolean active,
        Instant createdAt,
        Instant updatedAt,
        Creator creator) {

    public static ChatRoomResponse from(ChatRoomDto dto) {
        return new ChatRoomResponse(
                dto.id(),
                dto.name(),
                dto.description(),
                dto.roomType().name().toLowerCase(),
                dto.maxMembers(),
                dto.currentMembers(),
                dto.active(),
                dto.createdAt(),
                dto.updatedAt(),
                new Creator(dto.creator().id(), dto.creator().username()));
    }

    public record Creator(Long id, String username) {
    }
}
