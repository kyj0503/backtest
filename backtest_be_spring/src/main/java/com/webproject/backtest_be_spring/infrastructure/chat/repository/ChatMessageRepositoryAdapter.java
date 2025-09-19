package com.webproject.backtest_be_spring.infrastructure.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatMessage;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatMessageRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class ChatMessageRepositoryAdapter implements ChatMessageRepository {

    private final JpaChatMessageRepository jpa;

    public ChatMessageRepositoryAdapter(JpaChatMessageRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public ChatMessage save(ChatMessage message) {
        return jpa.save(message);
    }

    @Override
    public Optional<ChatMessage> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Page<ChatMessage> findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId, Pageable pageable) {
        return jpa.findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(roomId, pageable);
    }

    @Override
    public List<ChatMessage> findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId) {
        return jpa.findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(roomId);
    }

    @Override
    public long countByDeletedFalse() {
        return jpa.countByDeletedFalse();
    }
}
