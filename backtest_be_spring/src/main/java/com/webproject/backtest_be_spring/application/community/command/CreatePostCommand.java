package com.webproject.backtest_be_spring.application.community.command;

import com.webproject.backtest_be_spring.domain.community.PostCategory;
import com.webproject.backtest_be_spring.domain.community.PostContentType;

public record CreatePostCommand(
        PostCategory category,
        String title,
        String content,
        PostContentType contentType,
        boolean pinned,
        boolean featured) {
}
