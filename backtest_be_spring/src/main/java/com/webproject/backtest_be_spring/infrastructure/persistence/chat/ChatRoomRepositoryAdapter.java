package com.webproject.backtest_be_spring.infrastructure.persistence.chat;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoom;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomType;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatRoomRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
public class ChatRoomRepositoryAdapter implements ChatRoomRepository {

    private final JpaChatRoomRepository delegate;

    public ChatRoomRepositoryAdapter(JpaChatRoomRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public ChatRoom save(ChatRoom room) {
        return delegate.save(room);
    }

    @Override
    public Optional<ChatRoom> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Optional<ChatRoom> findByIdAndActiveTrue(Long id) {
        return delegate.findByIdAndActiveTrue(id);
    }

    @Override
    public Page<ChatRoom> findByActiveTrue(Pageable pageable) {
        return delegate.findByActiveTrue(pageable);
    }

    @Override
    public Page<ChatRoom> findByRoomTypeAndActiveTrue(ChatRoomType roomType, Pageable pageable) {
        return delegate.findByRoomTypeAndActiveTrue(roomType, pageable);
    }

    @Override
    public boolean existsByNameIgnoreCase(String name) {
        return delegate.existsByNameIgnoreCase(name);
    }

    @Override
    public long countByActiveTrue() {
        return delegate.countByActiveTrue();
    }
}
