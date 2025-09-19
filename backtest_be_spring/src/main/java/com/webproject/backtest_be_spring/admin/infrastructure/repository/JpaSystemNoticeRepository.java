package com.webproject.backtest_be_spring.admin.infrastructure.repository;

import com.webproject.backtest_be_spring.admin.domain.model.SystemNotice;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JpaSystemNoticeRepository extends JpaRepository<SystemNotice, Long> {

    Optional<SystemNotice> findById(Long id);

    Page<SystemNotice> findAll(Pageable pageable);
}
