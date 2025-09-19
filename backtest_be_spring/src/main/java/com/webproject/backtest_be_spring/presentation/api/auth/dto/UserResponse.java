package com.webproject.backtest_be_spring.presentation.api.auth.dto;

public record UserResponse(
        Long id,
        String username,
        String email,
        String profileImage,
        String investmentType,
        boolean emailVerified
) {
}
