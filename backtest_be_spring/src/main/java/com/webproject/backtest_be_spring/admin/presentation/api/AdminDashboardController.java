package com.webproject.backtest_be_spring.admin.presentation.api;

import com.webproject.backtest_be_spring.admin.application.AdminDashboardService;
import com.webproject.backtest_be_spring.admin.presentation.api.dto.AdminSummaryResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin/stats")
@Tag(name = "Admin Dashboard", description = "관리자 대시보드 API")
@PreAuthorize("hasRole('ADMIN')")
public class AdminDashboardController {

    private final AdminDashboardService adminDashboardService;

    public AdminDashboardController(AdminDashboardService adminDashboardService) {
        this.adminDashboardService = adminDashboardService;
    }

    @Operation(summary = "요약 통계", description = "서비스 전반의 핵심 지표를 제공합니다.")
    @GetMapping("/summary")
    public ResponseEntity<AdminSummaryResponse> summary() {
        return ResponseEntity.ok(AdminSummaryResponse.from(adminDashboardService.getSummary()));
    }
}
