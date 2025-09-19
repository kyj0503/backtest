package com.webproject.backtest_be_spring.presentation.api.community.dto;

import com.webproject.backtest_be_spring.application.community.dto.PostDto;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;

public record PostResponse(
        Long id,
        String category,
        String title,
        String content,
        String contentType,
        long viewCount,
        long likeCount,
        long commentCount,
        boolean pinned,
        boolean featured,
        boolean deleted,
        Instant createdAt,
        Instant updatedAt,
        Author author) {

    public static PostResponse from(PostDto dto) {
        PostDto.AuthorSummary author = dto.author();
        return new PostResponse(
                dto.id(),
                dto.category().name().toLowerCase(),
                dto.title(),
                dto.content(),
                dto.contentType().name().toLowerCase(),
                dto.viewCount(),
                dto.likeCount(),
                dto.commentCount(),
                dto.pinned(),
                dto.featured(),
                dto.deleted(),
                dto.createdAt(),
                dto.updatedAt(),
                new Author(author.id(), author.username(), author.email()));
    }

    @Schema(name = "PostAuthor")
    public record Author(Long id, String username, String email) {
    }
}
