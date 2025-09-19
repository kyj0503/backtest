package com.webproject.backtest_be_spring.infrastructure.admin.repository;

import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface JpaSystemNoticeRepository extends JpaRepository<SystemNotice, Long> {

    Optional<SystemNotice> findById(Long id);

    Page<SystemNotice> findAll(Pageable pageable);
}
