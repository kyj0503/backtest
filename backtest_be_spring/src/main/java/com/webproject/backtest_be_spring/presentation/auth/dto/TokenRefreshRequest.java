package com.webproject.backtest_be_spring.presentation.auth.dto;

import jakarta.validation.constraints.NotBlank;

public record TokenRefreshRequest(@NotBlank String refreshToken) {
}
