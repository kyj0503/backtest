package com.webproject.backtest_be_spring.presentation.admin.dto;

import com.webproject.backtest_be_spring.application.admin.dto.SystemNoticeDto;
import java.time.Instant;

public record NoticeResponse(
        Long id,
        String title,
        String content,
        String noticeType,
        String priority,
        boolean popup,
        boolean pinned,
        Instant startDate,
        Instant endDate,
        boolean active,
        Long authorId,
        String authorName,
        Instant createdAt,
        Instant updatedAt) {

    public static NoticeResponse from(SystemNoticeDto dto) {
        return new NoticeResponse(
                dto.id(),
                dto.title(),
                dto.content(),
                dto.noticeType().name().toLowerCase(),
                dto.priority().name().toLowerCase(),
                dto.popup(),
                dto.pinned(),
                dto.startDate(),
                dto.endDate(),
                dto.active(),
                dto.authorId(),
                dto.authorName(),
                dto.createdAt(),
                dto.updatedAt());
    }
}
