package com.webproject.backtest_be_spring.admin.application;

import com.webproject.backtest_be_spring.admin.application.dto.AdminSummaryDto;
import com.webproject.backtest_be_spring.admin.domain.model.ReportStatus;
import com.webproject.backtest_be_spring.admin.domain.repository.ReportRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatMessageRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomRepository;
import com.webproject.backtest_be_spring.community.domain.repository.PostCommentRepository;
import com.webproject.backtest_be_spring.community.domain.repository.PostRepository;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class AdminDashboardService {

    private final UserRepository userRepository;
    private final PostRepository postRepository;
    private final PostCommentRepository postCommentRepository;
    private final ChatRoomRepository chatRoomRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final ReportRepository reportRepository;

    public AdminDashboardService(UserRepository userRepository, PostRepository postRepository,
            PostCommentRepository postCommentRepository, ChatRoomRepository chatRoomRepository,
            ChatMessageRepository chatMessageRepository, ReportRepository reportRepository) {
        this.userRepository = userRepository;
        this.postRepository = postRepository;
        this.postCommentRepository = postCommentRepository;
        this.chatRoomRepository = chatRoomRepository;
        this.chatMessageRepository = chatMessageRepository;
        this.reportRepository = reportRepository;
    }

    public AdminSummaryDto getSummary() {
        long users = userRepository.count();
        long posts = postRepository.countByDeletedFalse();
        long comments = postCommentRepository.countByDeletedFalse();
        long chatRooms = chatRoomRepository.countByActiveTrue();
        long chatMessages = chatMessageRepository.countByDeletedFalse();
        long pendingReports = reportRepository.countByStatus(ReportStatus.PENDING);
        return new AdminSummaryDto(users, posts, comments, chatRooms, chatMessages, pendingReports);
    }
}
