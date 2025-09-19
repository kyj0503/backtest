package com.webproject.backtest_be_spring.presentation.community.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PostCreateRequest(
        String category,
        @NotBlank @Size(min = 1, max = 200) String title,
        @NotBlank String content,
        String contentType,
        Boolean pinned,
        Boolean featured) {
}
