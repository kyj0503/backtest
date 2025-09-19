package com.webproject.backtest_be_spring.chat.domain.repository;

import com.webproject.backtest_be_spring.chat.domain.model.ChatMessage;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface ChatMessageRepository {

    ChatMessage save(ChatMessage message);

    Optional<ChatMessage> findById(Long id);

    Page<ChatMessage> findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId, Pageable pageable);

    List<ChatMessage> findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId);

    long countByDeletedFalse();
}
