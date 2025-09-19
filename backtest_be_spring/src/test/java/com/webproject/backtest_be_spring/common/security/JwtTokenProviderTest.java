package com.webproject.backtest_be_spring.common.security;

import static org.assertj.core.api.Assertions.assertThat;

import com.webproject.backtest_be_spring.common.security.JwtProperties;
import io.jsonwebtoken.Claims;
import java.time.Duration;
import java.time.Instant;
import java.util.Set;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class JwtTokenProviderTest {

    private final JwtProperties properties = new JwtProperties(
            "test-secret-key-change-me-change-me-change-me-change-me-1234567890",
            Duration.ofMinutes(15),
            Duration.ofDays(7),
            "backtest-be-spring-test");

    private final JwtTokenProvider tokenProvider = new JwtTokenProvider(properties);

    @Test
    @DisplayName("액세스 토큰은 사용자 정보를 담고 있어야 한다")
    void generateAccessTokenContainsUserClaims() {
        String token = tokenProvider.generateAccessToken(1L, "alice", "alice@example.com", Set.of("ROLE_USER"));

        Claims claims = tokenProvider.parseClaims(token);

        assertThat(claims.getSubject()).isEqualTo("1");
        assertThat(claims.getIssuer()).isEqualTo("backtest-be-spring-test");
        assertThat(claims.get("username", String.class)).isEqualTo("alice");
        assertThat(claims.get("email", String.class)).isEqualTo("alice@example.com");
        assertThat((Iterable<String>) claims.get("roles", Iterable.class)).containsExactly("ROLE_USER");
        assertThat(tokenProvider.isTokenValid(token)).isTrue();
    }

    @Test
    @DisplayName("리프레시 토큰은 세션 식별자를 클레임으로 포함한다")
    void generateRefreshTokenContainsSessionId() {
        String token = tokenProvider.generateRefreshToken(1L, "session-123");

        Claims claims = tokenProvider.parseClaims(token);

        assertThat(claims.getSubject()).isEqualTo("1");
        assertThat(claims.get("sessionId", String.class)).isEqualTo("session-123");
        assertThat(tokenProvider.getExpiry(token)).isAfter(Instant.now());
    }
}
