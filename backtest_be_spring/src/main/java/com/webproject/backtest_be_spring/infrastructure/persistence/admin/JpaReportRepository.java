package com.webproject.backtest_be_spring.infrastructure.persistence.admin;

import com.webproject.backtest_be_spring.domain.admin.model.Report;
import com.webproject.backtest_be_spring.domain.admin.model.ReportStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JpaReportRepository extends JpaRepository<Report, Long> {

    Page<Report> findByStatus(ReportStatus status, Pageable pageable);

    long countByStatus(ReportStatus status);
}
