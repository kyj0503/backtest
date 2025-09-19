package com.webproject.backtest_be_spring.infrastructure.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomMember;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JpaChatRoomMemberRepository extends JpaRepository<ChatRoomMember, Long> {

    Optional<ChatRoomMember> findById(Long id);

    Optional<ChatRoomMember> findByRoomIdAndUserId(Long roomId, Long userId);

    List<ChatRoomMember> findByRoomIdAndActiveTrue(Long roomId);

    long countByRoomIdAndActiveTrue(Long roomId);
}
