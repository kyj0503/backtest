package com.webproject.backtest_be_spring.chat.infrastructure.messaging;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.webproject.backtest_be_spring.chat.application.dto.ChatMessageDto;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class ChatMessagePublisher {

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

    public ChatMessagePublisher(StringRedisTemplate redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    public void publish(ChatMessageDto message) {
        try {
            String payload = objectMapper.writeValueAsString(message);
            redisTemplate.convertAndSend(topic(message.roomId()), payload);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("채팅 메시지를 직렬화할 수 없습니다.", e);
        }
    }

    private String topic(Long roomId) {
        return "chatroom." + roomId;
    }
}
