package com.webproject.backtest_be_spring.presentation.api.community.dto;

import com.webproject.backtest_be_spring.application.community.dto.CommentDto;
import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

public record CommentResponse(
        Long id,
        Long postId,
        Long parentId,
        String content,
        long likeCount,
        boolean deleted,
        Instant createdAt,
        Instant updatedAt,
        PostResponse.Author author,
        List<CommentResponse> children) {

    public static CommentResponse from(CommentDto dto) {
        List<CommentResponse> childResponses = dto.children() == null
                ? List.of()
                : dto.children().stream().map(CommentResponse::from).collect(Collectors.toList());
        return new CommentResponse(
                dto.id(),
                dto.postId(),
                dto.parentId(),
                dto.content(),
                dto.likeCount(),
                dto.deleted(),
                dto.createdAt(),
                dto.updatedAt(),
                new PostResponse.Author(dto.author().id(), dto.author().username(), dto.author().email()),
                childResponses);
    }
}
