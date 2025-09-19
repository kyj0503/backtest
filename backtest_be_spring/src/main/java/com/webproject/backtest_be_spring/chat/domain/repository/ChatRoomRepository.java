package com.webproject.backtest_be_spring.chat.domain.repository;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface ChatRoomRepository {

    ChatRoom save(ChatRoom room);

    Optional<ChatRoom> findById(Long id);

    Optional<ChatRoom> findByIdAndActiveTrue(Long id);

    Page<ChatRoom> findByActiveTrue(Pageable pageable);

    Page<ChatRoom> findByRoomTypeAndActiveTrue(ChatRoomType roomType, Pageable pageable);

    boolean existsByNameIgnoreCase(String name);

    long countByActiveTrue();
}
