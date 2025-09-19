package com.webproject.backtest_be_spring.user.domain;

import java.util.Objects;

/**
 * 사용자 식별자를 나타내는 Value Object
 */
public record UserId(Long value) {
    
    public UserId {
        Objects.requireNonNull(value, "UserId value cannot be null");
        if (value <= 0) {
            throw new IllegalArgumentException("UserId must be positive, but was: " + value);
        }
    }
    
    public static UserId of(Long value) {
        return new UserId(value);
    }
    
    @Override
    public String toString() {
        return "UserId{" + value + "}";
    }
}