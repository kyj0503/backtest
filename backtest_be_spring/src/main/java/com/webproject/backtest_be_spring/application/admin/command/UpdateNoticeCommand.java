package com.webproject.backtest_be_spring.application.admin.command;

import com.webproject.backtest_be_spring.domain.admin.SystemNoticePriority;
import com.webproject.backtest_be_spring.domain.admin.SystemNoticeType;
import java.time.Instant;

public record UpdateNoticeCommand(
        String title,
        String content,
        SystemNoticeType noticeType,
        SystemNoticePriority priority,
        Boolean popup,
        Boolean pinned,
        Instant startDate,
        Instant endDate,
        Boolean active) {
}
