package com.webproject.backtest_be_spring.application.community.dto;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostCategory;
import java.time.Instant;

public record PostSummaryDto(
        Long id,
        PostCategory category,
        String title,
        long viewCount,
        long likeCount,
        long commentCount,
        boolean pinned,
        boolean featured,
        Instant createdAt,
        PostDto.AuthorSummary author) {

    public static PostSummaryDto from(Post post) {
        return new PostSummaryDto(
                post.getId(),
                post.getCategory(),
                post.getTitle(),
                post.getViewCount(),
                post.getLikeCount(),
                post.getCommentCount(),
                post.isPinned(),
                post.isFeatured(),
                post.getCreatedAt(),
                new PostDto.AuthorSummary(post.getAuthor().getId(), post.getAuthor().getUsername(), post.getAuthor().getEmail()));
    }
}
