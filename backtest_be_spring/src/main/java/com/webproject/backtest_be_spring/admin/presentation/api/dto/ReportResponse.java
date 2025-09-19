package com.webproject.backtest_be_spring.admin.presentation.api.dto;

import com.webproject.backtest_be_spring.admin.application.dto.ReportDto;
import java.time.Instant;

public record ReportResponse(
        Long id,
        String targetType,
        Long targetId,
        String reason,
        String description,
        String status,
        Long reporterId,
        String reporterName,
        Long processorId,
        String processorName,
        String resolution,
        Instant processedAt,
        Instant createdAt) {

    public static ReportResponse from(ReportDto dto) {
        return new ReportResponse(
                dto.id(),
                dto.targetType().name().toLowerCase(),
                dto.targetId(),
                dto.reason().name().toLowerCase(),
                dto.description(),
                dto.status().name().toLowerCase(),
                dto.reporterId(),
                dto.reporterName(),
                dto.processorId(),
                dto.processorName(),
                dto.resolution(),
                dto.processedAt(),
                dto.createdAt());
    }
}
