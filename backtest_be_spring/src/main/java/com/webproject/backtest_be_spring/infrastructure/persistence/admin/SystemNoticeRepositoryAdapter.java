package com.webproject.backtest_be_spring.infrastructure.persistence.admin;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import com.webproject.backtest_be_spring.domain.admin.repository.SystemNoticeRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
public class SystemNoticeRepositoryAdapter implements SystemNoticeRepository {

    private final JpaSystemNoticeRepository delegate;

    public SystemNoticeRepositoryAdapter(JpaSystemNoticeRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public SystemNotice save(SystemNotice notice) {
        return delegate.save(notice);
    }

    @Override
    public void delete(SystemNotice notice) {
        delegate.delete(notice);
    }

    @Override
    public Optional<SystemNotice> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Page<SystemNotice> findAll(Pageable pageable) {
        return delegate.findAll(pageable);
    }
}
