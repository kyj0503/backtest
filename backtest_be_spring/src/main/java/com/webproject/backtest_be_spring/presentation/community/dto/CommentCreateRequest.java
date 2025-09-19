package com.webproject.backtest_be_spring.presentation.community.dto;

import jakarta.validation.constraints.NotBlank;

public record CommentCreateRequest(Long parentId, @NotBlank String content) {
}
