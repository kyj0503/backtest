package com.webproject.backtest_be_spring.infrastructure.persistence.admin;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JpaSystemNoticeRepository extends JpaRepository<SystemNotice, Long> {

    Page<SystemNotice> findAll(Pageable pageable);
}
