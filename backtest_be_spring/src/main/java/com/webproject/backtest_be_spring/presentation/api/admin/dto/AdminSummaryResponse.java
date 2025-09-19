package com.webproject.backtest_be_spring.presentation.api.admin.dto;

import com.webproject.backtest_be_spring.application.admin.dto.AdminSummaryDto;

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
