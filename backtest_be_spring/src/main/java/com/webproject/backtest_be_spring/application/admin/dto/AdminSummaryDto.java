package com.webproject.backtest_be_spring.application.admin.dto;

public record AdminSummaryDto(
        long totalUsers,
        long activePosts,
        long totalComments,
        long activeChatRooms,
        long totalChatMessages,
        long pendingReports) {
}
