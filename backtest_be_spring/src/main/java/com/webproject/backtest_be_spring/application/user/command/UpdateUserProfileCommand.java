package com.webproject.backtest_be_spring.application.user.command;

import com.webproject.backtest_be_spring.domain.user.model.InvestmentType;
import java.util.Optional;

public record UpdateUserProfileCommand(
        Optional<String> username,
        Optional<String> profileImage,
        Optional<InvestmentType> investmentType
) {
    public UpdateUserProfileCommand(
            Optional<String> username,
            Optional<String> profileImage,
            Optional<InvestmentType> investmentType) {
        this.username = username == null ? Optional.empty() : username;
        this.profileImage = profileImage == null ? Optional.empty() : profileImage;
        this.investmentType = investmentType == null ? Optional.empty() : investmentType;
    }
}
