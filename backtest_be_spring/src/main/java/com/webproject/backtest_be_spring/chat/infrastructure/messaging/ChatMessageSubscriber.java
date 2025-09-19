package com.webproject.backtest_be_spring.chat.infrastructure.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.webproject.backtest_be_spring.chat.application.dto.ChatMessageDto;
import java.nio.charset.StandardCharsets;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
public class ChatMessageSubscriber implements MessageListener {

    private static final Logger log = LoggerFactory.getLogger(ChatMessageSubscriber.class);

    private final ObjectMapper objectMapper;
    private final SimpMessagingTemplate messagingTemplate;

    public ChatMessageSubscriber(ObjectMapper objectMapper, SimpMessagingTemplate messagingTemplate) {
        this.objectMapper = objectMapper;
        this.messagingTemplate = messagingTemplate;
    }

    @Override
    public void onMessage(Message message, byte[] pattern) {
        try {
            String payload = new String(message.getBody(), StandardCharsets.UTF_8);
            ChatMessageDto dto = objectMapper.readValue(payload, ChatMessageDto.class);
            messagingTemplate.convertAndSend("/topic/chatrooms/" + dto.roomId(), dto);
        } catch (Exception ex) {
            log.error("Failed to process chat message from Redis", ex);
        }
    }
}
