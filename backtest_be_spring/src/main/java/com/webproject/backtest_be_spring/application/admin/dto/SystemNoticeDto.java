package com.webproject.backtest_be_spring.application.admin.dto;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import com.webproject.backtest_be_spring.domain.admin.model.SystemNoticePriority;
import com.webproject.backtest_be_spring.domain.admin.model.SystemNoticeType;
import java.time.Instant;

public record SystemNoticeDto(
        Long id,
        String title,
        String content,
        SystemNoticeType noticeType,
        SystemNoticePriority priority,
        boolean popup,
        boolean pinned,
        Instant startDate,
        Instant endDate,
        boolean active,
        Long authorId,
        String authorName,
        Instant createdAt,
        Instant updatedAt) {

    public static SystemNoticeDto from(SystemNotice notice) {
        return new SystemNoticeDto(
                notice.getId(),
                notice.getTitle(),
                notice.getContent(),
                notice.getNoticeType(),
                notice.getPriority(),
                notice.isPopup(),
                notice.isPinned(),
                notice.getStartDate(),
                notice.getEndDate(),
                notice.isActive(),
                notice.getAuthor().getId(),
                notice.getAuthor().getUsername(),
                notice.getCreatedAt(),
                notice.getUpdatedAt());
    }
}
