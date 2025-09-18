package com.webproject.backtest_be_spring.application.auth.command;

import com.webproject.backtest_be_spring.domain.user.InvestmentType;
import java.util.Objects;
import java.util.Optional;

public record RegisterUserCommand(
        String username,
        String email,
        String password,
        Optional<InvestmentType> investmentType
) {
    public RegisterUserCommand {
        Objects.requireNonNull(username, "username must not be null");
        Objects.requireNonNull(email, "email must not be null");
        Objects.requireNonNull(password, "password must not be null");
        this.investmentType = investmentType == null ? Optional.empty() : investmentType;
    }
}
