package com.webproject.backtest_be_spring.auth.application.dto;

public record UserSummary(
        Long id,
        String username,
        String email,
        String profileImage,
        String investmentType,
        boolean emailVerified
) {
}
