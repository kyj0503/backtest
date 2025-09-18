package com.webproject.backtest_be_spring.application.auth.dto;

public record AuthResult(UserSummary user, TokenBundle tokens) {
}
