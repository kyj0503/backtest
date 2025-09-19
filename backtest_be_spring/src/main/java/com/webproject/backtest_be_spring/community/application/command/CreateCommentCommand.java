package com.webproject.backtest_be_spring.community.application.command;

public record CreateCommentCommand(Long parentId, String content) {
}
