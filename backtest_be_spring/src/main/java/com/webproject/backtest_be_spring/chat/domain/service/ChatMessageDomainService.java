package com.webproject.backtest_be_spring.chat.domain.service;

import com.webproject.backtest_be_spring.chat.domain.model.ChatMessage;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessageType;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.user.domain.model.User;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class ChatMessageDomainService {

    public ChatMessage create(ChatRoom room, User sender, ChatMessageType messageType, String content,
            String fileUrl, String fileName, Integer fileSize, ChatMessage replyTo) {
        ChatMessageType resolvedType = messageType == null ? ChatMessageType.TEXT : messageType;
        if (resolvedType == ChatMessageType.TEXT && !StringUtils.hasText(content)) {
            throw new IllegalArgumentException("텍스트 메시지는 내용을 포함해야 합니다.");
        }
        return ChatMessage.create(room, sender, resolvedType, content, fileUrl, fileName, fileSize, replyTo);
    }

    public void delete(ChatMessage message) {
        message.markDeleted();
    }
}
