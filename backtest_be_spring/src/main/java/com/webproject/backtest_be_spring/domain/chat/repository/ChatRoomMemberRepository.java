package com.webproject.backtest_be_spring.domain.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomMember;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatRoomMemberRepository extends JpaRepository<ChatRoomMember, Long> {

    Optional<ChatRoomMember> findByRoomIdAndUserId(Long roomId, Long userId);

    List<ChatRoomMember> findByRoomIdAndActiveTrue(Long roomId);

    long countByRoomIdAndActiveTrue(Long roomId);
}
