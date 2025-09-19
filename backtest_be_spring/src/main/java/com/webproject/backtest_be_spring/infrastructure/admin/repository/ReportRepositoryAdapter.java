package com.webproject.backtest_be_spring.infrastructure.admin.repository;

import com.webproject.backtest_be_spring.domain.admin.model.Report;
import com.webproject.backtest_be_spring.domain.admin.model.ReportStatus;
import com.webproject.backtest_be_spring.domain.admin.repository.ReportRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class ReportRepositoryAdapter implements ReportRepository {

    private final JpaReportRepository jpa;

    public ReportRepositoryAdapter(JpaReportRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public Report save(Report report) {
        return jpa.save(report);
    }

    @Override
    public Optional<Report> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Page<Report> findByStatus(ReportStatus status, Pageable pageable) {
        return jpa.findByStatus(status, pageable);
    }

    @Override
    public Page<Report> findAll(Pageable pageable) {
        return jpa.findAll(pageable);
    }

    @Override
    public long countByStatus(ReportStatus status) {
        return jpa.countByStatus(status);
    }
}
