package com.webproject.backtest_be_spring.auth.presentation.api.legacy.dto;

public record UserResponse(
        Long id,
        String username,
        String email,
        String profileImage,
        String investmentType,
        boolean emailVerified
) {
}
