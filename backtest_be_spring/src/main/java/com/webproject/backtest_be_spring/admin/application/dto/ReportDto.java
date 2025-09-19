package com.webproject.backtest_be_spring.admin.application.dto;

import com.webproject.backtest_be_spring.admin.domain.model.Report;
import com.webproject.backtest_be_spring.admin.domain.model.ReportReason;
import com.webproject.backtest_be_spring.admin.domain.model.ReportStatus;
import com.webproject.backtest_be_spring.admin.domain.model.ReportTargetType;
import java.time.Instant;

public record ReportDto(
        Long id,
        ReportTargetType targetType,
        Long targetId,
        ReportReason reason,
        String description,
        ReportStatus status,
        Long reporterId,
        String reporterName,
        Long processorId,
        String processorName,
        String resolution,
        Instant processedAt,
        Instant createdAt) {

    public static ReportDto from(Report report) {
        return new ReportDto(
                report.getId(),
                report.getTargetType(),
                report.getTargetId(),
                report.getReportReason(),
                report.getDescription(),
                report.getStatus(),
                report.getReporter().getId(),
                report.getReporter().getUsername(),
                report.getProcessor() != null ? report.getProcessor().getId() : null,
                report.getProcessor() != null ? report.getProcessor().getUsername() : null,
                report.getResolution(),
                report.getProcessedAt(),
                report.getCreatedAt());
    }
}
