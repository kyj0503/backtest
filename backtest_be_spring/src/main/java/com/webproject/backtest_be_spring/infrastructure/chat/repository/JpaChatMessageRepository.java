package com.webproject.backtest_be_spring.infrastructure.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatMessage;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JpaChatMessageRepository extends JpaRepository<ChatMessage, Long> {

    Page<ChatMessage> findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId, Pageable pageable);

    List<ChatMessage> findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId);

    long countByDeletedFalse();

    Optional<ChatMessage> findById(Long id);
}
