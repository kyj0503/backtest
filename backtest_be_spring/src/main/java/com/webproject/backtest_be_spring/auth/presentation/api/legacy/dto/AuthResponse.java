package com.webproject.backtest_be_spring.auth.presentation.api.legacy.dto;

public record AuthResponse(UserResponse user, TokenResponse tokens) {
}
