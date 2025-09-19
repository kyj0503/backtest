package com.webproject.backtest_be_spring.auth.application.dto;

public record AuthResult(UserSummary user, TokenBundle tokens) {
}
