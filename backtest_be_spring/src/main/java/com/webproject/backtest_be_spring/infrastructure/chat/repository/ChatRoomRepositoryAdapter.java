package com.webproject.backtest_be_spring.infrastructure.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoom;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomType;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatRoomRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class ChatRoomRepositoryAdapter implements ChatRoomRepository {

    private final JpaChatRoomRepository jpa;

    public ChatRoomRepositoryAdapter(JpaChatRoomRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public ChatRoom save(ChatRoom room) {
        return jpa.save(room);
    }

    @Override
    public Optional<ChatRoom> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Optional<ChatRoom> findByIdAndActiveTrue(Long id) {
        return jpa.findByIdAndActiveTrue(id);
    }

    @Override
    public Page<ChatRoom> findByActiveTrue(Pageable pageable) {
        return jpa.findByActiveTrue(pageable);
    }

    @Override
    public Page<ChatRoom> findByRoomTypeAndActiveTrue(ChatRoomType roomType, Pageable pageable) {
        return jpa.findByRoomTypeAndActiveTrue(roomType, pageable);
    }

    @Override
    public boolean existsByNameIgnoreCase(String name) {
        return jpa.existsByNameIgnoreCase(name);
    }

    @Override
    public long countByActiveTrue() {
        return jpa.countByActiveTrue();
    }
}
