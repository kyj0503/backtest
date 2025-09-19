package com.webproject.backtest_be_spring.presentation.api.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatRoomCreateRequest(
        @NotBlank @Size(max = 100) String name,
        String description,
        String roomType,
        Integer maxMembers) {
}
