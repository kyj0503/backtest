package com.webproject.backtest_be_spring.application.chat.exception;

public class ChatAccessDeniedException extends RuntimeException {

    public ChatAccessDeniedException() {
        super("채팅 기능을 사용할 권한이 없습니다.");
    }
}
