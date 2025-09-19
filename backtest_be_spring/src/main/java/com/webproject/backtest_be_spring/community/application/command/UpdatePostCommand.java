package com.webproject.backtest_be_spring.community.application.command;

import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;

public record UpdatePostCommand(
        PostCategory category,
        String title,
        String content,
        PostContentType contentType,
        Boolean pinned,
        Boolean featured) {
}
