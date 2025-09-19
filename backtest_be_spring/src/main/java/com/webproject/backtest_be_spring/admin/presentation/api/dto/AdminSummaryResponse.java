package com.webproject.backtest_be_spring.admin.presentation.api.dto;

import com.webproject.backtest_be_spring.admin.application.dto.AdminSummaryDto;

public record AdminSummaryResponse(
        long totalUsers,
        long activePosts,
        long totalComments,
        long activeChatRooms,
        long totalChatMessages,
        long pendingReports) {

    public static AdminSummaryResponse from(AdminSummaryDto dto) {
        return new AdminSummaryResponse(
                dto.totalUsers(),
                dto.activePosts(),
                dto.totalComments(),
                dto.activeChatRooms(),
                dto.totalChatMessages(),
                dto.pendingReports());
    }
}
