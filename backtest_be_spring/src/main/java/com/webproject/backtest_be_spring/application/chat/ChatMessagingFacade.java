package com.webproject.backtest_be_spring.application.chat;

import com.webproject.backtest_be_spring.application.chat.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.application.chat.dto.ChatMessageDto;
import com.webproject.backtest_be_spring.infrastructure.messaging.chat.ChatMessagePublisher;
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
