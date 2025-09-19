package com.webproject.backtest_be_spring.auth.application.exception;

public class InvalidRefreshTokenException extends RuntimeException {
    public InvalidRefreshTokenException() {
        super("유효하지 않은 리프레시 토큰입니다.");
    }
}
