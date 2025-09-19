package com.webproject.backtest_be_spring.domain.admin.repository;

import com.webproject.backtest_be_spring.domain.admin.model.Report;
import com.webproject.backtest_be_spring.domain.admin.model.ReportStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReportRepository extends JpaRepository<Report, Long> {

    long countByStatus(ReportStatus status);

    Page<Report> findByStatus(ReportStatus status, Pageable pageable);
}
