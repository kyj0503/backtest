package com.webproject.backtest_be_spring.presentation.admin.dto;

import java.time.Instant;

public record NoticeUpdateRequest(
        String title,
        String content,
        String noticeType,
        String priority,
        Boolean popup,
        Boolean pinned,
        Instant startDate,
        Instant endDate,
        Boolean active) {
}
