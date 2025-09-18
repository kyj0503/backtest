package com.webproject.backtest_be_spring.application.auth.command;

import java.util.Objects;

public record TokenRefreshCommand(String refreshToken) {
    public TokenRefreshCommand {
        Objects.requireNonNull(refreshToken, "refreshToken must not be null");
    }
}
