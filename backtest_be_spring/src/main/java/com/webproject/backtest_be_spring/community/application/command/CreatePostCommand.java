package com.webproject.backtest_be_spring.community.application.command;

import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;

public record CreatePostCommand(
        PostCategory category,
        String title,
        String content,
        PostContentType contentType,
        boolean pinned,
        boolean featured) {
}
