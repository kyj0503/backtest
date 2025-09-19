package com.webproject.backtest_be_spring.auth.application.command;

import java.util.Objects;

public record LoginCommand(String email, String password) {
    public LoginCommand {
        Objects.requireNonNull(email, "email must not be null");
        Objects.requireNonNull(password, "password must not be null");
    }
}
