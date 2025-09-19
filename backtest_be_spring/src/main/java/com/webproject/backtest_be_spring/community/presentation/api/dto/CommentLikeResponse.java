package com.webproject.backtest_be_spring.community.presentation.api.dto;

public record CommentLikeResponse(boolean liked) {
    public static CommentLikeResponse of(boolean liked) {
        return new CommentLikeResponse(liked);
    }
}
