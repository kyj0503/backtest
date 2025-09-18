package com.webproject.backtest_be_spring.application.user.dto;

import java.time.Instant;

public record UserProfileDto(
        Long id,
        String username,
        String email,
        String profileImage,
        String investmentType,
        boolean emailVerified,
        Instant createdAt,
        Instant updatedAt
) {
}
