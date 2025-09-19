package com.webproject.backtest_be_spring.community.application.dto;

import com.webproject.backtest_be_spring.community.domain.model.PostComment;
import java.time.Instant;
import java.util.List;

public record CommentDto(
        Long id,
        Long postId,
        Long parentId,
        String content,
        long likeCount,
        boolean deleted,
        Instant createdAt,
        Instant updatedAt,
        PostDto.AuthorSummary author,
        List<CommentDto> children) {

    public static CommentDto from(PostComment comment, List<CommentDto> children) {
        return new CommentDto(
                comment.getId(),
                comment.getPost().getId(),
                comment.getParent() != null ? comment.getParent().getId() : null,
                comment.getContent(),
                comment.getLikeCount(),
                comment.isDeleted(),
                comment.getCreatedAt(),
                comment.getUpdatedAt(),
                new PostDto.AuthorSummary(comment.getAuthor().getId(), comment.getAuthor().getUsername(),
                        comment.getAuthor().getEmail()),
                children);
    }
}
