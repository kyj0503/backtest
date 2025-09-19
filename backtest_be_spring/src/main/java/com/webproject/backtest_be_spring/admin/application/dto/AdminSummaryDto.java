package com.webproject.backtest_be_spring.admin.application.dto;

public record AdminSummaryDto(
        long totalUsers,
        long activePosts,
        long totalComments,
        long activeChatRooms,
        long totalChatMessages,
        long pendingReports) {
}
