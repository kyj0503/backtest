package com.webproject.backtest_be_spring.infrastructure.chat.repository;

import com.webproject.backtest_be_spring.domain.chat.model.ChatRoom;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomType;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JpaChatRoomRepository extends JpaRepository<ChatRoom, Long> {

    Optional<ChatRoom> findByIdAndActiveTrue(Long id);

    Page<ChatRoom> findByActiveTrue(Pageable pageable);

    Page<ChatRoom> findByRoomTypeAndActiveTrue(ChatRoomType roomType, Pageable pageable);

    boolean existsByNameIgnoreCase(String name);

    long countByActiveTrue();
}
