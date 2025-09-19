package com.webproject.backtest_be_spring.presentation.api.community.dto;

public record CommentLikeResponse(boolean liked) {
    public static CommentLikeResponse of(boolean liked) {
        return new CommentLikeResponse(liked);
    }
}
