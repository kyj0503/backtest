package com.webproject.backtest_be_spring.admin.domain.repository;

import com.webproject.backtest_be_spring.admin.domain.model.Report;
import com.webproject.backtest_be_spring.admin.domain.model.ReportStatus;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface ReportRepository {

    Report save(Report report);

    Optional<Report> findById(Long id);

    Page<Report> findByStatus(ReportStatus status, Pageable pageable);

    Page<Report> findAll(Pageable pageable);

    long countByStatus(ReportStatus status);
}
