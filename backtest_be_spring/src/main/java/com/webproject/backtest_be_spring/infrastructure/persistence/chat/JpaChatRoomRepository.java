package com.webproject.backtest_be_spring.infrastructure.persistence.chat;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoom;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomType;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JpaChatRoomRepository extends JpaRepository<ChatRoom, Long> {

    Page<ChatRoom> findByActiveTrue(Pageable pageable);

    Page<ChatRoom> findByRoomTypeAndActiveTrue(ChatRoomType roomType, Pageable pageable);

    Optional<ChatRoom> findByIdAndActiveTrue(Long id);

    boolean existsByNameIgnoreCase(String name);

    long countByActiveTrue();
}
