package com.webproject.backtest_be_spring.presentation.api.auth.dto;

public record AuthResponse(UserResponse user, TokenResponse tokens) {
}
