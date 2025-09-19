package com.webproject.backtest_be_spring.application.community.command;

import com.webproject.backtest_be_spring.domain.community.model.PostCategory;
import com.webproject.backtest_be_spring.domain.community.model.PostContentType;

public record UpdatePostCommand(
        PostCategory category,
        String title,
        String content,
        PostContentType contentType,
        Boolean pinned,
        Boolean featured) {
}
