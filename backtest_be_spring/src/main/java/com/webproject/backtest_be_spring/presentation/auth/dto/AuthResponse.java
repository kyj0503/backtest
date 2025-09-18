package com.webproject.backtest_be_spring.presentation.auth.dto;

public record AuthResponse(UserResponse user, TokenResponse tokens) {
}
