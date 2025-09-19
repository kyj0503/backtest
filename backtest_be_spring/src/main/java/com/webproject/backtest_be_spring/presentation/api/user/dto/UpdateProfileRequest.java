package com.webproject.backtest_be_spring.presentation.api.user.dto;

import jakarta.validation.constraints.Size;

public record UpdateProfileRequest(
        @Size(min = 2, max = 50) String username,
        String investmentType,
        String profileImage
) {
}
