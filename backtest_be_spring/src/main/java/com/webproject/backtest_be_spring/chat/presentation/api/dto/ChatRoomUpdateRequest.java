package com.webproject.backtest_be_spring.chat.presentation.api.dto;

import jakarta.validation.constraints.Size;

public record ChatRoomUpdateRequest(
        @Size(max = 100) String name,
        String description,
        String roomType,
        Integer maxMembers,
        Boolean active) {
}
