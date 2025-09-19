package com.webproject.backtest_be_spring.application.community.command;

public record CreateCommentCommand(Long parentId, String content) {
}
