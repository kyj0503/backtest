package com.webproject.backtest_be_spring.community.presentation.api.dto;

public record PostLikeResponse(boolean liked) {
    public static PostLikeResponse of(boolean liked) {
        return new PostLikeResponse(liked);
    }
}
