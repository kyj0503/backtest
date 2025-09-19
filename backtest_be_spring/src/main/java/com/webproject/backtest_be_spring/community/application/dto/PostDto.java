package com.webproject.backtest_be_spring.community.application.dto;

import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import java.time.Instant;

public record PostDto(
        Long id,
        PostCategory category,
        String title,
        String content,
        PostContentType contentType,
        long viewCount,
        long likeCount,
        long commentCount,
        boolean pinned,
        boolean featured,
        boolean deleted,
        Instant createdAt,
        Instant updatedAt,
        AuthorSummary author) {

    public static PostDto from(Post post) {
        return new PostDto(
                post.getId(),
                post.getCategory(),
                post.getTitle(),
                post.getContent(),
                post.getContentType(),
                post.getViewCount(),
                post.getLikeCount(),
                post.getCommentCount(),
                post.isPinned(),
                post.isFeatured(),
                post.isDeleted(),
                post.getCreatedAt(),
                post.getUpdatedAt(),
                new AuthorSummary(post.getAuthor().getId(), post.getAuthor().getUsername(), post.getAuthor().getEmail()));
    }

    public record AuthorSummary(Long id, String username, String email) {
    }
}
