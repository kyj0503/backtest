package com.webproject.backtest_be_spring.presentation.community.dto;

import jakarta.validation.constraints.Size;

public record PostUpdateRequest(
        String category,
        @Size(min = 1, max = 200) String title,
        String content,
        String contentType,
        Boolean pinned,
        Boolean featured) {
}
