package com.webproject.backtest_be_spring.presentation.api.admin;

import com.webproject.backtest_be_spring.application.admin.AdminReportService;
import com.webproject.backtest_be_spring.application.admin.dto.ReportDto;
import com.webproject.backtest_be_spring.infrastructure.security.UserPrincipal;
import com.webproject.backtest_be_spring.domain.admin.model.ReportStatus;
import com.webproject.backtest_be_spring.presentation.api.admin.dto.ReportProcessRequest;
import com.webproject.backtest_be_spring.presentation.api.admin.dto.ReportResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.Locale;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin/reports")
@Tag(name = "Admin Reports", description = "신고 관리 API")
@PreAuthorize("hasRole('ADMIN')")
public class AdminReportController {

    private final AdminReportService adminReportService;

    public AdminReportController(AdminReportService adminReportService) {
        this.adminReportService = adminReportService;
    }

    @Operation(summary = "신고 목록", description = "신고 내역을 페이징하여 조회합니다.")
    @GetMapping
    public ResponseEntity<Page<ReportResponse>> getReports(
            @RequestParam(name = "status", required = false) String status,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        ReportStatus reportStatus = parseStatus(status);
        Page<ReportResponse> responses = adminReportService.getReports(reportStatus, pageable)
                .map(ReportResponse::from);
        return ResponseEntity.ok(responses);
    }

    @Operation(summary = "신고 처리", description = "신고 상태와 결과를 업데이트합니다.")
    @PatchMapping("/{reportId}")
    public ResponseEntity<ReportResponse> processReport(@PathVariable Long reportId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody ReportProcessRequest request) {
        ReportStatus status = parseStatus(request.status());
        ReportDto dto = adminReportService.process(reportId, principal.getId(), status, request.resolution());
        return ResponseEntity.ok(ReportResponse.from(dto));
    }

    private ReportStatus parseStatus(String status) {
        if (status == null || status.isBlank()) {
            return null;
        }
        try {
            return ReportStatus.valueOf(status.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 신고 상태입니다: " + status);
        }
    }
}
