package com.webproject.backtest_be_spring.auth.presentation.api.dto;

import java.time.Instant;

public record TokenResponse(String accessToken, String refreshToken, String tokenType, Instant accessExpiresAt, Instant refreshTokenExpiresAt) {
}
