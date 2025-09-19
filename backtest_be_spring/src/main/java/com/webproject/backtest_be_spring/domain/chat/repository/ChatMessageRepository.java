package com.webproject.backtest_be_spring.domain.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatMessage;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, Long> {

    Page<ChatMessage> findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId, Pageable pageable);

    List<ChatMessage> findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId);

    long countByDeletedFalse();
}
