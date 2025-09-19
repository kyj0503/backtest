package com.webproject.backtest_be_spring.application.chat.exception;

public class ChatRoomNotFoundException extends RuntimeException {

    public ChatRoomNotFoundException(Long id) {
        super("채팅방을 찾을 수 없습니다. id=" + id);
    }
}
