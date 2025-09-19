package com.webproject.backtest_be_spring.infrastructure.persistence.chat;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomMember;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatRoomMemberRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class ChatRoomMemberRepositoryAdapter implements ChatRoomMemberRepository {

    private final JpaChatRoomMemberRepository delegate;

    public ChatRoomMemberRepositoryAdapter(JpaChatRoomMemberRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public ChatRoomMember save(ChatRoomMember member) {
        return delegate.save(member);
    }

    @Override
    public Optional<ChatRoomMember> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Optional<ChatRoomMember> findByRoomIdAndUserId(Long roomId, Long userId) {
        return delegate.findByRoomIdAndUserId(roomId, userId);
    }

    @Override
    public List<ChatRoomMember> findByRoomIdAndActiveTrue(Long roomId) {
        return delegate.findByRoomIdAndActiveTrue(roomId);
    }

    @Override
    public long countByRoomIdAndActiveTrue(Long roomId) {
        return delegate.countByRoomIdAndActiveTrue(roomId);
    }
}
