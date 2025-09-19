package com.webproject.backtest_be_spring.user.presentation.api.dto;

import jakarta.validation.constraints.Size;

public record UpdateProfileRequest(
        @Size(min = 2, max = 50) String username,
        String investmentType,
        String profileImage
) {
}
