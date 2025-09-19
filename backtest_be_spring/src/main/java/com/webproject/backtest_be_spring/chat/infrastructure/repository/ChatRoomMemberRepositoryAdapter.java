package com.webproject.backtest_be_spring.chat.infrastructure.repository;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomMemberRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class ChatRoomMemberRepositoryAdapter implements ChatRoomMemberRepository {

    private final JpaChatRoomMemberRepository jpa;

    public ChatRoomMemberRepositoryAdapter(JpaChatRoomMemberRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public ChatRoomMember save(ChatRoomMember member) {
        return jpa.save(member);
    }

    @Override
    public Optional<ChatRoomMember> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Optional<ChatRoomMember> findByRoomIdAndUserId(Long roomId, Long userId) {
        return jpa.findByRoomIdAndUserId(roomId, userId);
    }

    @Override
    public List<ChatRoomMember> findByRoomIdAndActiveTrue(Long roomId) {
        return jpa.findByRoomIdAndActiveTrue(roomId);
    }

    @Override
    public long countByRoomIdAndActiveTrue(Long roomId) {
        return jpa.countByRoomIdAndActiveTrue(roomId);
    }
}
