package com.webproject.backtest_be_spring.application.admin;

import com.webproject.backtest_be_spring.application.admin.dto.ReportDto;
import com.webproject.backtest_be_spring.application.admin.exception.AdminAccessDeniedException;
import com.webproject.backtest_be_spring.application.admin.exception.ReportNotFoundException;
import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.domain.admin.Report;
import com.webproject.backtest_be_spring.domain.admin.ReportStatus;
import com.webproject.backtest_be_spring.domain.admin.repository.ReportRepository;
import com.webproject.backtest_be_spring.domain.user.User;
import com.webproject.backtest_be_spring.domain.user.repository.UserRepository;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class AdminReportService {

    private final ReportRepository reportRepository;
    private final UserRepository userRepository;

    public AdminReportService(ReportRepository reportRepository, UserRepository userRepository) {
        this.reportRepository = reportRepository;
        this.userRepository = userRepository;
    }

    public Page<ReportDto> getReports(ReportStatus status, Pageable pageable) {
        Page<Report> reports = status != null ? reportRepository.findByStatus(status, pageable)
                : reportRepository.findAll(pageable);
        return reports.map(ReportDto::from);
    }

    public ReportDto process(Long reportId, Long adminId, ReportStatus status, String resolution) {
        Report report = reportRepository.findById(reportId).orElseThrow(() -> new ReportNotFoundException(reportId));
        User admin = userRepository.findById(adminId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + adminId));
        if (!admin.isAdmin()) {
            throw new AdminAccessDeniedException();
        }
        report.process(admin, status, resolution);
        return ReportDto.from(report);
    }
}
