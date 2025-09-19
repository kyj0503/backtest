package com.webproject.backtest_be_spring.admin.domain.repository;

import com.webproject.backtest_be_spring.admin.domain.model.SystemNotice;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface SystemNoticeRepository {

    SystemNotice save(SystemNotice notice);

    void delete(SystemNotice notice);

    java.util.Optional<SystemNotice> findById(Long id);

    Page<SystemNotice> findAll(Pageable pageable);
}
