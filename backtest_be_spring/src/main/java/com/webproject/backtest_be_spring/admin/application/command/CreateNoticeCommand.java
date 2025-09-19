package com.webproject.backtest_be_spring.admin.application.command;

import com.webproject.backtest_be_spring.admin.domain.model.SystemNoticePriority;
import com.webproject.backtest_be_spring.admin.domain.model.SystemNoticeType;
import java.time.Instant;

public record CreateNoticeCommand(
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
