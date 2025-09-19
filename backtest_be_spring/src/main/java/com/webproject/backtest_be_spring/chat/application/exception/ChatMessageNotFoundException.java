package com.webproject.backtest_be_spring.chat.application.exception;

public class ChatMessageNotFoundException extends RuntimeException {

    public ChatMessageNotFoundException(Long id) {
        super("채팅 메시지를 찾을 수 없습니다. id=" + id);
    }
}
