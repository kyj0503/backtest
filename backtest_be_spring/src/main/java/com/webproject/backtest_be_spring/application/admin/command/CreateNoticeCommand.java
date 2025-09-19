package com.webproject.backtest_be_spring.application.admin.command;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNoticePriority;
import com.webproject.backtest_be_spring.domain.admin.model.SystemNoticeType;
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
