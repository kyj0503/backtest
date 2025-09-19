package com.webproject.backtest_be_spring.chat.application.dto;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;
import java.time.Instant;

public record ChatRoomDto(
        Long id,
        String name,
        String description,
        ChatRoomType roomType,
        Integer maxMembers,
        Integer currentMembers,
        boolean active,
        Instant createdAt,
        Instant updatedAt,
        Creator creator) {

    public static ChatRoomDto from(ChatRoom room) {
        return new ChatRoomDto(
                room.getId(),
                room.getName(),
                room.getDescription(),
                room.getRoomType(),
                room.getMaxMembers(),
                room.getCurrentMembers(),
                room.isActive(),
                room.getCreatedAt(),
                room.getUpdatedAt(),
                new Creator(room.getCreatedBy().getId(), room.getCreatedBy().getUsername()));
    }

    public record Creator(Long id, String username) {
    }
}
