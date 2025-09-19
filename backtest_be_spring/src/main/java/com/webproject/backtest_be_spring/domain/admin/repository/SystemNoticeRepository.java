package com.webproject.backtest_be_spring.domain.admin.repository;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SystemNoticeRepository extends JpaRepository<SystemNotice, Long> {
}
