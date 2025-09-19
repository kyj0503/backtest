package com.webproject.backtest_be_spring.community.presentation.api.dto;

import com.webproject.backtest_be_spring.community.application.dto.PostSummaryDto;
import java.time.Instant;

public record PostSummaryResponse(
        Long id,
        String category,
        String title,
        long viewCount,
        long likeCount,
        long commentCount,
        boolean pinned,
        boolean featured,
        Instant createdAt,
        PostResponse.Author author) {

    public static PostSummaryResponse from(PostSummaryDto dto) {
        return new PostSummaryResponse(
                dto.id(),
                dto.category().name().toLowerCase(),
                dto.title(),
                dto.viewCount(),
                dto.likeCount(),
                dto.commentCount(),
                dto.pinned(),
                dto.featured(),
                dto.createdAt(),
                new PostResponse.Author(dto.author().id(), dto.author().username(), dto.author().email()));
    }
}
