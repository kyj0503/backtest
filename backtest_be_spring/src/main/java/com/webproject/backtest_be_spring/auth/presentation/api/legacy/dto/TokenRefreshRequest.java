package com.webproject.backtest_be_spring.auth.presentation.api.legacy.dto;

import jakarta.validation.constraints.NotBlank;

public record TokenRefreshRequest(@NotBlank String refreshToken) {
}
