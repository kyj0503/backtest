package com.webproject.backtest_be_spring.community.application.exception;

public class CommentNotFoundException extends RuntimeException {

    public CommentNotFoundException(Long id) {
        super("댓글을 찾을 수 없습니다. id=" + id);
    }
}
