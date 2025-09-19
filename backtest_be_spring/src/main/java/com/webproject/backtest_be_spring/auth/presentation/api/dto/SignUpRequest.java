package com.webproject.backtest_be_spring.auth.presentation.api.dto;

public record SignUpRequest(String username, String email, String password, String investmentType) {
}
