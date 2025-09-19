package com.webproject.backtest_be_spring.admin.infrastructure.repository;

import com.webproject.backtest_be_spring.admin.domain.model.Report;
import com.webproject.backtest_be_spring.admin.domain.model.ReportStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaReportRepository extends JpaRepository<Report, Long> {

    Page<Report> findByStatus(ReportStatus status, Pageable pageable);

    Page<Report> findAll(Pageable pageable);

    long countByStatus(ReportStatus status);

    Optional<Report> findById(Long id);
}
