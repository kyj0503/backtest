package com.webproject.backtest_be_spring.admin.presentation.api.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public record NoticeCreateRequest(
        @NotBlank @Size(max = 200) String title,
        @NotBlank String content,
        String noticeType,
        String priority,
        Boolean popup,
        Boolean pinned,
        Instant startDate,
        Instant endDate,
        Boolean active) {
}
