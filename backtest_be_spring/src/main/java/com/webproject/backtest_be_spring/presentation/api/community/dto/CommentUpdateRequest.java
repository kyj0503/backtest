package com.webproject.backtest_be_spring.presentation.api.community.dto;

import jakarta.validation.constraints.NotBlank;

public record CommentUpdateRequest(@NotBlank String content) {
}
