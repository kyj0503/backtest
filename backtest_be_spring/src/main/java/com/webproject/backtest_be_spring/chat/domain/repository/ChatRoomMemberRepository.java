package com.webproject.backtest_be_spring.chat.domain.repository;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import java.util.List;
import java.util.Optional;

public interface ChatRoomMemberRepository {

    ChatRoomMember save(ChatRoomMember member);

    Optional<ChatRoomMember> findById(Long id);

    Optional<ChatRoomMember> findByRoomIdAndUserId(Long roomId, Long userId);

    List<ChatRoomMember> findByRoomIdAndActiveTrue(Long roomId);

    long countByRoomIdAndActiveTrue(Long roomId);
}
