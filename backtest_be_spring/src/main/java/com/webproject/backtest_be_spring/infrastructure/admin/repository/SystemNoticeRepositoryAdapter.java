package com.webproject.backtest_be_spring.infrastructure.admin.repository;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import com.webproject.backtest_be_spring.domain.admin.repository.SystemNoticeRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class SystemNoticeRepositoryAdapter implements SystemNoticeRepository {

    private final JpaSystemNoticeRepository jpa;

    public SystemNoticeRepositoryAdapter(JpaSystemNoticeRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public SystemNotice save(SystemNotice notice) {
        return jpa.save(notice);
    }

    @Override
    @Transactional
    public void delete(SystemNotice notice) {
        jpa.delete(notice);
    }

    @Override
    public Optional<SystemNotice> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Page<SystemNotice> findAll(Pageable pageable) {
        return jpa.findAll(pageable);
    }
}
