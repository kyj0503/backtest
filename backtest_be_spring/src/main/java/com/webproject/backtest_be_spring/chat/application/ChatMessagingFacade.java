package com.webproject.backtest_be_spring.chat.application;

import com.webproject.backtest_be_spring.chat.application.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.chat.application.dto.ChatMessageDto;
import com.webproject.backtest_be_spring.chat.infrastructure.messaging.ChatMessagePublisher;
import org.springframework.stereotype.Service;

@Service
public class ChatMessagingFacade {

    private final ChatMessageService chatMessageService;
    private final ChatMessagePublisher chatMessagePublisher;

    public ChatMessagingFacade(ChatMessageService chatMessageService, ChatMessagePublisher chatMessagePublisher) {
        this.chatMessageService = chatMessageService;
        this.chatMessagePublisher = chatMessagePublisher;
    }

    public ChatMessageDto send(Long roomId, Long userId, SendChatMessageCommand command) {
        ChatMessageDto dto = chatMessageService.sendMessage(roomId, userId, command);
        chatMessagePublisher.publish(dto);
        return dto;
    }
}
