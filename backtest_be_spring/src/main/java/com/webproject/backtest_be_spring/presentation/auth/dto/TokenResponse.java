package com.webproject.backtest_be_spring.presentation.auth.dto;

import java.time.Instant;

public record TokenResponse(
        String accessToken,
        String refreshToken,
        String tokenType,
        Instant accessTokenExpiresAt,
        Instant refreshTokenExpiresAt
) {
}
