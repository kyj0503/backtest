package com.webproject.backtest_be_spring.application.auth.dto;

import java.time.Instant;

public record TokenBundle(
        String accessToken,
        String refreshToken,
        String tokenType,
        Instant accessTokenExpiresAt,
        Instant refreshTokenExpiresAt
) {
}
