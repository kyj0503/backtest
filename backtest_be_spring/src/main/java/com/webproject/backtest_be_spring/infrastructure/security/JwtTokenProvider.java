package com.webproject.backtest_be_spring.infrastructure.security;

import com.webproject.backtest_be_spring.infrastructure.security.JwtProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.DecodingException;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import javax.crypto.SecretKey;

public class JwtTokenProvider {

    private final JwtProperties properties;
    private final SecretKey secretKey;

    public JwtTokenProvider(JwtProperties properties) {
        this.properties = properties;
        byte[] keyBytes = resolveKeyBytes(properties.getSecret());
        this.secretKey = Keys.hmacShaKeyFor(keyBytes);
    }

    public String generateAccessToken(Long userId, String username, String email, Collection<String> roles) {
        Instant now = Instant.now();
        Instant expiry = now.plus(properties.getAccessTokenExpiration());

        Map<String, Object> claims = new HashMap<>();
        claims.put("username", username);
        claims.put("email", email);
        claims.put("roles", roles);

        return buildToken(userId, claims, now, expiry);
    }

    public String generateRefreshToken(Long userId, String sessionId) {
        Instant now = Instant.now();
        Instant expiry = now.plus(properties.getRefreshTokenExpiration());

        Map<String, Object> claims = new HashMap<>();
        claims.put("sessionId", sessionId);

        return buildToken(userId, claims, now, expiry);
    }

    public Claims parseClaims(String token) {
        return Jwts.parserBuilder()
                .requireIssuer(properties.getIssuer())
                .setSigningKey(secretKey)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    public boolean isTokenValid(String token) {
        try {
            Claims claims = parseClaims(token);
            Date expiration = claims.getExpiration();
            return expiration != null && expiration.toInstant().isAfter(Instant.now());
        } catch (Exception ex) {
            return false;
        }
    }

    public Instant getExpiry(String token) {
        return parseClaims(token).getExpiration().toInstant();
    }

    private String buildToken(Long userId, Map<String, Object> claims, Instant issuedAt, Instant expiry) {
        return Jwts.builder()
                .setSubject(String.valueOf(userId))
                .setIssuer(properties.getIssuer())
                .setIssuedAt(Date.from(issuedAt))
                .setExpiration(Date.from(expiry))
                .addClaims(claims)
                .signWith(secretKey, SignatureAlgorithm.HS512)
                .compact();
    }

    private byte[] resolveKeyBytes(String secret) {
        try {
            return Decoders.BASE64.decode(secret);
        } catch (IllegalArgumentException | DecodingException ex) {
            return secret.getBytes(StandardCharsets.UTF_8);
        }
    }
}
