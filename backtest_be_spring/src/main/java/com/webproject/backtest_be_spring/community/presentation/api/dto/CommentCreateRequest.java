package com.webproject.backtest_be_spring.community.presentation.api.dto;

import jakarta.validation.constraints.NotBlank;

public record CommentCreateRequest(Long parentId, @NotBlank String content) {
}
