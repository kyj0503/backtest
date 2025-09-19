package com.webproject.backtest_be_spring.admin.presentation.api.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record ReportProcessRequest(
        @NotNull String status,
        @NotBlank String resolution) {
}
