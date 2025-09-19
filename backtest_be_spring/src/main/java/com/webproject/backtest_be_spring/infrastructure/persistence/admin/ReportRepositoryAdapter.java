package com.webproject.backtest_be_spring.infrastructure.persistence.admin;

import com.webproject.backtest_be_spring.domain.admin.model.Report;
import com.webproject.backtest_be_spring.domain.admin.model.ReportStatus;
import com.webproject.backtest_be_spring.domain.admin.repository.ReportRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
public class ReportRepositoryAdapter implements ReportRepository {

    private final JpaReportRepository delegate;

    public ReportRepositoryAdapter(JpaReportRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public Report save(Report report) {
        return delegate.save(report);
    }

    @Override
    public Optional<Report> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Page<Report> findByStatus(ReportStatus status, Pageable pageable) {
        return delegate.findByStatus(status, pageable);
    }

    @Override
    public Page<Report> findAll(Pageable pageable) {
        return delegate.findAll(pageable);
    }

    @Override
    public long countByStatus(ReportStatus status) {
        return delegate.countByStatus(status);
    }
}
