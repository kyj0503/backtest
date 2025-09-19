package com.webproject.backtest_be_spring.application.chat.dto;

import com.webproject.backtest_be_spring.domain.chat.ChatMemberRole;
import com.webproject.backtest_be_spring.domain.chat.ChatRoomMember;
import java.time.Instant;

public record ChatRoomMemberDto(
        Long id,
        Long userId,
        String username,
        ChatMemberRole role,
        boolean active,
        Instant joinedAt,
        Instant lastReadAt) {

    public static ChatRoomMemberDto from(ChatRoomMember member) {
        return new ChatRoomMemberDto(
                member.getId(),
                member.getUser().getId(),
                member.getUser().getUsername(),
                member.getRole(),
                member.isActive(),
                member.getJoinedAt(),
                member.getLastReadAt());
    }
}
