package com.webproject.backtest_be_spring.infrastructure.persistence.chat;

import com.webproject.backtest_be_spring.domain.chat.model.ChatMessage;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatMessageRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
public class ChatMessageRepositoryAdapter implements ChatMessageRepository {

    private final JpaChatMessageRepository delegate;

    public ChatMessageRepositoryAdapter(JpaChatMessageRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public ChatMessage save(ChatMessage message) {
        return delegate.save(message);
    }

    @Override
    public Optional<ChatMessage> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Page<ChatMessage> findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId, Pageable pageable) {
        return delegate.findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(roomId, pageable);
    }

    @Override
    public List<ChatMessage> findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(Long roomId) {
        return delegate.findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(roomId);
    }

    @Override
    public long countByDeletedFalse() {
        return delegate.countByDeletedFalse();
    }
}
